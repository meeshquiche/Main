import requests
import pandas as pd
from Shiny import App, render, ui, reactive

# --- API LOGIC ---
ENDPOINT = "https://api.usaspending.gov/api/v2/references/toptier_agencies/"
HEADERS = {"User-Agent": "MyPythonApp/1.0"}

def fetch_spending_data():
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Convert to DataFrame for easy handling in Shiny
        df = pd.DataFrame(data.get("results", []))
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- SHINY UI ---
app_ui = ui.page_fluid(
    ui.panel_title("🏛️ Federal AI Spending Reporter"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.markdown("### Controls"),
            ui.input_action_button("refresh", "Fetch Latest Data", class_="btn-primary"),
            ui.hr(),
            ui.input_select("agency_filter", "Select Agency for AI Report", choices=[]),
            ui.input_action_button("run_ai", "Generate AI Summary", class_="btn-success"),
        ),
        ui.navset_tab(
            ui.nav_panel("Data Table", 
                ui.output_table("spending_table")
            ),
            ui.nav_panel("AI Insights", 
                ui.markdown("#### Executive Summary"),
                ui.output_text_verbatim("ai_report")
            ),
        ),
    ),
)

# --- SERVER LOGIC ---
def server(input, output, session):
    # Reactive value to store the dataframe
    v = reactive.Value(pd.DataFrame())

    # 1. Fetch data on button click
    @reactive.Effect
    @reactive.event(input.refresh)
    def _():
        df = fetch_spending_data()
        v.set(df)
        # Update the dropdown choices based on fetched data
        if not df.empty:
            choices = dict(zip(df['toptier_code'], df['agency_name']))
            ui.update_select("agency_filter", choices=choices)

    # 2. Render the Data Table
    @output
    @render.table
    def spending_table():
        df = v.get()
        if df.empty:
            return pd.DataFrame({"Message": ["Click 'Fetch Latest Data' to begin."]})
        return df[['agency_name', 'abbreviation', 'budget_authority_amount', 'outlay_amount']].head(15)

    # 3. Generate AI Report (Mocked for Lab Environment)
    @output
    @render.text
    @reactive.event(input.run_ai)
    def ai_report():
        df = v.get()
        selected_code = input.agency_filter()
        
        if df.empty or not selected_code:
            return "Please fetch data and select an agency first."
        
        # Filter for the specific agency
        agency_data = df[df['toptier_code'] == selected_code].iloc[0]
        
        # This is where your AI call (OpenAI/Ollama) would live.
        # For this lab, we demonstrate the prompt logic:
        summary = (
            f"AI ANALYSIS REPORT:\n"
            f"Agency: {agency_data['agency_name']} ({agency_data['abbreviation']})\n"
            f"Current Budget Authority: ${agency_data['budget_authority_amount']:,.2f}\n"
            f"Actual Outlays: ${agency_data['outlay_amount']:,.2f}\n\n"
            f"Insight: {agency_data['agency_name']} has utilized "
            f"{(agency_data['outlay_amount']/agency_data['budget_authority_amount'])*100:.1f}% "
            f"of its budget authority this year."
        )
        return summary

app = App(app_ui, server)