# components/attendance/app/review_app.py

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from attendance import analyzer, exporter, logic, insights
from core import ai_services

# --- Page Configuration ---
st.set_page_config(
    page_title="HR-Insight | Executive Command Center", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- === "MIDNIGHT SLATE & GOLD" UI/UX === ---

def load_css():
    """Injects custom CSS for the ultra-luxe, C-suite theme."""
    css = """
    <style>
        /* --- Import Google Fonts: Inter for UI, Plus Jakarta Sans for Headers --- */
        @import url('https://fonts.googleapis.com/css2?family+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

        /* --- Color & Font Design Tokens --- */
        :root {
            /* Palette: Deep, sophisticated, and focused */
            --primary-bg: #111111; /* Near-black for the main background */
            --secondary-bg: #1E1E1E; /* Slightly lighter for cards and elements */
            --border-color: #333333; /* Subtle borders for definition */
            --text-color: #EAEAEA; /* Primary text, soft white */
            --subtle-text-color: #A0A0A0; /* Secondary text, for labels and descriptions */
            
            /* Accents: Deliberate and impactful */
            --primary-accent: #00A99D; /* A slightly richer, deeper Teal */
            --highlight-accent: #D4AF37; /* Classic, rich Gold for AI and key highlights */
            --risk-color: #E57373; /* A softer, less jarring red for negative deltas */
            --warning-color: #FBC02D; /* A clear yellow for caution */
            --success-color: #66BB6A; /* A pleasant green for positive trends */


            /* Typography */
            --header-font: 'Plus Jakarta Sans', sans-serif;
            --body-font: 'Inter', sans-serif;
        }

        /* --- Global Styles --- */
        .stApp {
            background-color: var(--primary-bg);
            color: var(--text-color);
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--header-font);
            font-weight: 700;
            color: var(--text-color);
        }
        p, .stMarkdown, .stDataFrame, .stSelectbox, .stMultiSelect, .stCheckbox {
            font-family: var(--body-font);
            color: var(--text-color);
        }
        .stMarkdown h5 {
            font-weight: 400;
            color: var(--subtle-text-color);
            letter-spacing: 0.5px;
        }

        /* --- Main Title & Header --- */
        .stApp > header {
            background-color: transparent;
        }
        div[data-testid="stToolbar"] {
            display: none; /* Hide Streamlit's default toolbar for a cleaner look */
        }

        /* --- Sidebar Overhaul --- */
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(30,30,30,0.95) 0%, rgba(17,17,17,0.95) 100%);
            backdrop-filter: blur(10px);
            border-right: 1px solid var(--border-color);
        }
        .stSidebar h2, .stSidebar h3, .stSidebar .stMarkdown {
            color: var(--text-color);
        }
        
        /* --- Custom Component Styles: The KPI Card --- */
        .kpi-card {
            background: var(--secondary-bg);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            height: 100%;
            position: relative; /* Needed for tooltip positioning */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .kpi-card:hover {
            border-color: var(--highlight-accent);
            transform: translateY(-5px);
            box-shadow: 0px 10px 30px rgba(212, 175, 55, 0.1);
        }
        .kpi-title {
            font-family: var(--body-font);
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--subtle-text-color);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }
        .kpi-value {
            font-family: var(--header-font);
            font-size: 2.75rem;
            font-weight: 800;
            color: var(--text-color);
            line-height: 1.1;
        }
        .kpi-delta {
            font-family: var(--body-font);
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        /* --- Drilldown Card Styling --- */
        .drilldown-card {
            background-color: var(--secondary-bg);
            border-left: 4px solid var(--primary-accent);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 1rem;
        }
        .drilldown-card .formula {
            font-family: monospace;
            background-color: var(--primary-bg);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            color: var(--subtle-text-color);
        }

        /* --- AI Summary Card: The "Gemini Gem" --- */
        .ai-summary-card {
            background: linear-gradient(135deg, #2a2a2a, #1a1a1a);
            border-left: 4px solid var(--highlight-accent);
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }
        .ai-summary-card p {
            font-size: 1.05rem;
            line-height: 1.6;
        }

        /* --- Controls & Buttons --- */
        .stButton>button {
            border-radius: 8px;
            background: var(--highlight-accent);
            color: var(--primary-bg);
            border: none;
            padding: 12px 24px;
            font-family: var(--body-font);
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            filter: brightness(1.1);
        }
        .stDownloadButton>button, .stButton>button.secondary {
            border-radius: 8px;
            background-color: var(--secondary-bg);
            color: var(--primary-accent);
            border: 1px solid var(--primary-accent);
            font-weight: 600;
        }

        /* Style for the rendered HTML table to match the theme */
        .stApp table {
            width: 100%;
            border: none;
            border-collapse: collapse;
        }
        .stApp th {
            background-color: #2a2a2a; /* Slightly lighter than secondary-bg */
            text-align: left;
            font-family: var(--header-font);
            font-weight: 600;
            padding: 12px 10px;
        }
        .stApp td {
            padding: 10px;
            border-top: 1px solid var(--border-color);
        }

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def style_trend_indicator(trend_text):
    """Applies color and an icon to the trend text."""
    if trend_text == "Improving":
        return f'<span style="color: var(--success-color);">▲ {trend_text}</span>'
    elif trend_text == "Worsening":
        return f'<span style="color: var(--risk-color);">▼ {trend_text}</span>'
    else: # Stable
        return f'<span style="color: var(--subtle-text-color);">▬ {trend_text}</span>'

def create_plotly_pie_chart(data: dict):
    if not data: return None
    df = pd.DataFrame(list(data.items()), columns=['Leave Type', 'Days']).sort_values('Leave Type')
    colors = ['#00A99D', '#00796B', '#004D40', '#4DB6AC', '#80CBC4'] 
    fig = px.pie(df, values='Days', names='Leave Type', hole=0.5, color_discrete_sequence=colors)
    fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+value+percent',
                      marker=dict(line=dict(color= 'var(--secondary-bg)', width=3)),
                      textfont_size=14)
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family="Inter, sans-serif", color="var(--text-color)"))
    return fig

def create_subplots_trend_charts(trend_data: pd.DataFrame):
    if trend_data.empty or len(trend_data) < 2:
        return None

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Presence Rate Trend", "Leave Rate Trend", "Absenteeism Rate Trend")
    )

    metrics = {
        "Presence Rate": {"color": "#00A99D", "row": 1},
        "Leave Rate": {"color": "#FBC02D", "row": 2},
        "Absenteeism Rate": {"color": "#E57373", "row": 3}
    }

    for metric, config in metrics.items():
        fig.add_trace(
            go.Scatter(
                x=trend_data['DisplayMonth'],
                y=trend_data[metric],
                mode='lines+markers',
                name=metric,
                line=dict(color=config['color'], width=2.5),
                marker=dict(size=7)
            ),
            row=config['row'], col=1
        )
        fig.update_yaxes(title_text="%", row=config['row'], col=1, title_standoff=10)

    fig.update_layout(
        height=700,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="var(--subtle-text-color)"),
        margin=dict(l=50, r=40, t=50, b=50)
    )
    
    for annotation in fig['layout']['annotations']:
        annotation['font']['size'] = 16
        annotation['font']['family'] = 'Plus Jakarta Sans, sans-serif'
        annotation['font']['color'] = 'var(--text-color)'
        annotation['x'] = 0.0
        annotation['xanchor'] = 'left'

    fig.update_xaxes(gridcolor='var(--border-color)', showline=False, tickfont=dict(size=12))
    fig.update_yaxes(gridcolor='var(--border-color)', zeroline=False, showline=False, tickfont=dict(size=12))

    return fig

# --- Main App Execution ---
load_css()

if 'master_df' not in st.session_state: st.session_state.master_df = pd.DataFrame()
if 'daily_df' not in st.session_state: st.session_state.daily_df = pd.DataFrame()
if 'file_name' not in st.session_state: st.session_state.file_name = None
if 'drilldown_metric' not in st.session_state: st.session_state.drilldown_metric = None

st.title("HR-Insight Executive Command Center")
st.markdown("##### Strategic Attendance Intelligence for C-Suite Decision-Making")
st.markdown("---")

uploaded_file = st.file_uploader("Upload Adrenalin Max Attendance Report", type=['xlsx', 'xls'])

if uploaded_file:
    if st.session_state.file_name != uploaded_file.name:
        st.session_state.drilldown_metric = None 
        with st.spinner("Processing strategic data..."):
            file_bytes = uploaded_file.getvalue()
            try:
                st.session_state.master_df, st.session_state.daily_df = analyzer.analyze_attendance(file_bytes)
                st.session_state.file_name = uploaded_file.name
                st.success(f"File '{uploaded_file.name}' processed successfully!")
                st.rerun()
            except ValueError as ve:
                st.error(str(ve))
                st.session_state.file_name = None
            except Exception as e:
                st.error(f"An unexpected error occurred while processing the file: {str(e)}")
                st.session_state.file_name = None

if not st.session_state.master_df.empty:
    master_df = st.session_state.master_df
    daily_df = st.session_state.daily_df

    st.sidebar.header("Filters & Actions")
    
    with st.sidebar.expander("Filter by Business Unit (OU)", expanded=True):
        all_ou_options = sorted(master_df['OU Name'].unique().tolist())
        select_all_ou = st.checkbox("Select All / Deselect All", value=True, key='all_ou')
        st.write("---")
        
        selected_ou = []
        for ou in all_ou_options:
            if st.checkbox(ou, value=select_all_ou, key=f"ou_{ou}"):
                selected_ou.append(ou)
    ou_filtered_df = master_df[master_df['OU Name'].isin(selected_ou)] if selected_ou else pd.DataFrame(columns=master_df.columns)
    
    with st.sidebar.expander("Filter by Functional Lead", expanded=False):
        all_fl_options = sorted(ou_filtered_df['Functional Lead'].unique().tolist())
        select_all_fl = st.checkbox("Select All / Deselect All", value=True, key='all_fl')
        st.write("---")
        selected_fl = []
        for fl in all_fl_options:
            if st.checkbox(fl, value=select_all_fl, key=f"fl_{fl}"):
                selected_fl.append(fl)
    fl_filtered_df = ou_filtered_df[ou_filtered_df['Functional Lead'].isin(selected_fl)] if selected_fl else pd.DataFrame(columns=ou_filtered_df.columns)
    
    with st.sidebar.expander("Filter by Reporting Manager", expanded=False):
        all_mgr_options = sorted(fl_filtered_df['Reporting_Manager'].unique().tolist())
        select_all_mgr = st.checkbox("Select All / Deselect All", value=True, key='all_mgr')
        st.write("---")
        selected_mgr = []
        for mgr in all_mgr_options:
            if st.checkbox(mgr, value=select_all_mgr, key=f"mgr_{mgr}"):
                selected_mgr.append(mgr)
    filtered_df = fl_filtered_df[fl_filtered_df['Reporting_Manager'].isin(selected_mgr)] if selected_mgr else pd.DataFrame(columns=fl_filtered_df.columns)

    employee_ids_in_view = filtered_df['Employee ID'].unique()
    filtered_daily_df = daily_df[daily_df['Employee ID'].isin(employee_ids_in_view)]
    
    filtered_summary_data, baseline_kpis = logic.generate_attendance_summary(
        filtered_df, "Current View", master_df=master_df, daily_df=filtered_daily_df
    )
    filtered_kpis = filtered_summary_data.get('company_summary', {})
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Download Report")
    excel_bytes = exporter.create_excel_report(filtered_summary_data, filtered_df)
    st.sidebar.download_button(
        label="📥 Download Detailed Report", data=excel_bytes,
        file_name=f"HR_Insight_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Pre-calculate totals for the filtered view to use in both main and drill-down views
    if not filtered_df.empty:
        total_mandays_val = filtered_df['mandays'].sum()
        total_presence_val = filtered_df['total_presence'].sum()
        total_leave_val = filtered_df['total_leave'].sum()
        total_absenteeism_val = filtered_df['total_absenteeism'].sum()

        # --- NEW: CAPACITY CALCULATION ---
        # 1. Get unique working days in this specific filtered view
        period_working_days = filtered_daily_df['Date'].nunique() if not filtered_daily_df.empty else 0
        # 2. Get number of employees
        current_headcount = len(filtered_df)
        # 3. Calculate Standard Capacity (Benchmark)
        standard_capacity = current_headcount * period_working_days
        # 4. Calculate Gap (Actual vs Standard)
        capacity_gap = standard_capacity - total_mandays_val
        # ---------------------------------

        deployment_pct_val = (total_presence_val / total_mandays_val * 100) if total_mandays_val > 0 else 0
        absenteeism_rate_val = (total_absenteeism_val / total_mandays_val * 100) if total_mandays_val > 0 else 0
        presence_rate_val = filtered_kpis.get('presence_rate', 0)
        leave_rate_val = filtered_kpis.get('leave_rate', 0)

    if st.session_state.drilldown_metric:
        metric_clicked = st.session_state.drilldown_metric
        st.header(f"Analysis & Proof: {metric_clicked}")
        
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.drilldown_metric = None
            st.rerun()

        with st.container():
            st.markdown('<div class="drilldown-card">', unsafe_allow_html=True)
            
            # --- START OF UNIFIED DRILL-DOWN LOGIC ---
            # Define variables that will be set in the if/elif block
            formula_str, values_str = "", ""
            codes_to_use, breakdown_title, top_contrib_title, top_contrib_col = None, "", "", ""
            
            if metric_clicked == "Deployment":
                formula_str = "(Mandays Worked / Mandays) * 100"
                values_str = f"({total_presence_val:,.1f} / {total_mandays_val:,.1f}) * 100 = {deployment_pct_val:.1f}%"
                codes_to_use = analyzer.PRESENCE_CODES
                breakdown_title = "Breakdown of 'Mandays Worked' by Code"
                top_contrib_title = "Top 5 Employees by Mandays Worked"
                top_contrib_col = 'total_presence'
            
            elif metric_clicked == "Absenteeism Rate":
                formula_str = "(Mandays Lost / Mandays) * 100"
                values_str = f"({total_absenteeism_val:,.1f} / {total_mandays_val:,.1f}) * 100 = {absenteeism_rate_val:.1f}%"
                codes_to_use = analyzer.ABSENCE_CODES
                breakdown_title = "Breakdown of 'Mandays Lost' by Code"
                top_contrib_title = "Top 5 Employees by Mandays Lost"
                top_contrib_col = 'total_absenteeism'
            
            elif metric_clicked == "Mandays Worked":
                formula_str = "Sum of all 'Presence' days and half-days."
                values_str = f"Total Value: {total_presence_val:,.1f} Days"
                codes_to_use = analyzer.PRESENCE_CODES
                breakdown_title = "Breakdown of 'Mandays Worked' by Code"
                top_contrib_title = "Top 5 Employees by Mandays Worked"
                top_contrib_col = 'total_presence'
            
            elif metric_clicked == "Mandays Lost":
                formula_str = "Sum of all 'Absenteeism' days and half-days."
                values_str = f"Total Value: {total_absenteeism_val:,.1f} Days"
                codes_to_use = analyzer.ABSENCE_CODES
                breakdown_title = "Breakdown of 'Mandays Lost' by Code"
                top_contrib_title = "Top 5 Employees by Mandays Lost"
                top_contrib_col = 'total_absenteeism'
                
            elif metric_clicked == "Presence Rate":
                formula_str = "(Mandays Worked / Mandays) * 100"
                values_str = f"({total_presence_val:,.1f} / {total_mandays_val:,.1f}) * 100 = {presence_rate_val:.1f}%"
                codes_to_use = analyzer.PRESENCE_CODES
                breakdown_title = "Breakdown of 'Mandays Worked' by Code"
                top_contrib_title = "Top 5 Employees by Mandays Worked"
                top_contrib_col = 'total_presence'

            elif metric_clicked == "Leave Rate":
                formula_str = "(Total Leave Days / Mandays) * 100"
                values_str = f"({total_leave_val:,.1f} / {total_mandays_val:,.1f}) * 100 = {leave_rate_val:.1f}%"
                codes_to_use = analyzer.LEAVE_CODES
                breakdown_title = "Breakdown of 'Leave Days' by Code"
                top_contrib_title = "Top 5 Employees by Leave Days"
                top_contrib_col = 'total_leave'
            
            # Display the common elements
            st.subheader(f"Calculation for {metric_clicked}")
            st.markdown(f"**Formula:** <span class='formula'>{formula_str}</span>", unsafe_allow_html=True)
            st.markdown(f"**Values:** `{values_str}`")
            st.markdown("---")

            drilldown_data = filtered_daily_df[filtered_daily_df['Code'].apply(lambda x: any(c in codes_to_use for c in x.split('/')))]

            st.subheader(breakdown_title)
            code_counts = drilldown_data['Code'].value_counts().sort_values(ascending=False)
            if not code_counts.empty:
                st.table(code_counts)
            else:
                st.info(f"No records found with the relevant codes for this calculation.")

            st.subheader(top_contrib_title)
            if not filtered_df.empty:
                top_contributors = filtered_df.sort_values(by=top_contrib_col, ascending=False).head(5)
                st.table(top_contributors[['Employee Name', top_contrib_col]])
            else:
                st.info("No employee data available for this breakdown.")

            with st.expander("Show Full Raw Data Records for this Calculation"):
                display_cols = ['Date', 'Employee Name', 'Reporting_Manager', 'OU Name', 'Code', 'presence', 'leave', 'lwp', 'absent']
                existing_display_cols = [col for col in display_cols if col in drilldown_data.columns]
                st.dataframe(drilldown_data[existing_display_cols].sort_values(by=['Date', 'Employee Name']), use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            # --- END OF UNIFIED DRILL-DOWN LOGIC ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📈 KPI Overview", "🧠 AI Strategic Briefing", "🏢 Team Deep Dive", "📊 Leadership Scorecard"])

        with tab1:
            def format_filter_header(selected_items, all_options, name_if_all):
                if not selected_items: return "(None Selected)"
                if len(selected_items) == len(all_options): return name_if_all
                if len(selected_items) == 1: return selected_items[0]
                return f"({len(selected_items)} selected)"

            ou_display = format_filter_header(selected_ou, all_ou_options, "(All OUs)")
            fl_display = format_filter_header(selected_fl, all_fl_options, "(All Functional Leads)")
            mgr_display = format_filter_header(selected_mgr, all_mgr_options, "(All Reporting Managers)")

            st.header(f"Analysis for: {ou_display} | {fl_display} | {mgr_display}")
            
            if not filtered_df.empty:
                st.subheader("Strategic Overview")
                strat_cols = st.columns(4)
                
                with strat_cols[0]:
                    deployment_tooltip = "Measures productive days against scheduled workdays (Mandays). Formula: (Mandays Worked / Mandays) * 100."
                    st.markdown(f"""<div class="kpi-card"><div><div class="kpi-title">% Deployment <span title="{deployment_tooltip}">&nbsp;ⓘ</span></div><div class="kpi-value">{deployment_pct_val:.1f}%</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div>""", unsafe_allow_html=True)
                    if st.button("Show Calculation", key="dd_deployment", use_container_width=True, type="secondary"):
                        st.session_state.drilldown_metric = "Deployment"; st.rerun()

                with strat_cols[1]:
                    absenteeism_tooltip = "Measures unplanned absence days against scheduled workdays (Mandays). Formula: (Mandays Lost / Mandays) * 100."
                    st.markdown(f"""<div class="kpi-card"><div><div class="kpi-title">Absenteeism Rate <span title="{absenteeism_tooltip}">&nbsp;ⓘ</span></div><div class="kpi-value">{absenteeism_rate_val:.1f}%</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div>""", unsafe_allow_html=True)
                    if st.button("Show Calculation", key="dd_absenteeism", use_container_width=True, type="secondary"):
                        st.session_state.drilldown_metric = "Absenteeism Rate"; st.rerun()
                
                # --- UPDATED CARD: CAPACITY UTILIZATION ---
                with strat_cols[2]:
                    cap_tooltip = f"Actual Mandays vs. Standard Capacity.\nStandard Capacity = {current_headcount} Employees × {period_working_days} Working Days."
                    
                    gap_color = "var(--warning-color)" if capacity_gap > 0 else "var(--subtle-text-color)"
                    gap_text = f"Gap: -{capacity_gap:,.1f} Days" if capacity_gap > 0 else "Full Capacity"
                    
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div>
                            <div class="kpi-title">Mandays (Actual / Cap) <span title="{cap_tooltip}">&nbsp;ⓘ</span></div>
                            <div class="kpi-value" style="font-size: 2.2rem;">
                                {total_mandays_val:,.0f} <span style="font-size: 1.2rem; color: var(--subtle-text-color);">/ {standard_capacity:,.0f}</span>
                            </div>
                            <div class="kpi-delta" style="color: {gap_color};">
                                {gap_text}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Show Breakdown", key="dd_mandays_worked", use_container_width=True, type="secondary"):
                        st.session_state.drilldown_metric = "Mandays Worked"; st.rerun()
                # ------------------------------------------

                with strat_cols[3]:
                    mandays_lost_tooltip = "The total number of days lost to unplanned absence. Corresponds to codes like LWP, ABSENT, A."
                    st.markdown(f"""<div class="kpi-card"><div><div class="kpi-title">Mandays Lost <span title="{mandays_lost_tooltip}">&nbsp;ⓘ</span></div><div class="kpi-value">{total_absenteeism_val:,.1f}</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div>""", unsafe_allow_html=True)
                    if st.button("Show Calculation", key="dd_mandays_lost", use_container_width=True, type="secondary"):
                        st.session_state.drilldown_metric = "Mandays Lost"; st.rerun()

                st.markdown("---")
                
                st.subheader("Operational Metrics")
                context_cols = st.columns(3)
                
                with context_cols[0]:
                    presence_tooltip = "Measures productive days against all accounted-for days. Formula: (Present / (Present + Leave + Absent))."
                    st.markdown(f"""<div class="kpi-card"><div><div class="kpi-title">Presence Rate <span title="{presence_tooltip}">&nbsp;ⓘ</span></div><div class="kpi-value">{presence_rate_val:.1f}%</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div>""", unsafe_allow_html=True)
                    if st.button("Show Calculation", key="dd_presence", use_container_width=True, type="secondary"):
                        st.session_state.drilldown_metric = "Presence Rate"; st.rerun()
                
                with context_cols[1]:
                    leave_tooltip = "Measures planned leave days against all accounted-for days. Formula: (Leave / (Present + Leave + Absent))."
                    st.markdown(f"""<div class="kpi-card"><div><div class="kpi-title">Leave Rate <span title="{leave_tooltip}">&nbsp;ⓘ</span></div><div class="kpi-value">{leave_rate_val:.1f}%</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div>""", unsafe_allow_html=True)
                    if st.button("Show Calculation", key="dd_leave", use_container_width=True, type="secondary"):
                        st.session_state.drilldown_metric = "Leave Rate"; st.rerun()

                with context_cols[2]:
                    # Keep Filtered Employees Card
                    st.markdown(f"""<div class="kpi-card"><div><div class="kpi-title">Filtered Employees <span title="The total number of unique employees included in the current analysis.">&nbsp;ⓘ</span></div><div class="kpi-value">{len(filtered_df)}</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div></div>""", unsafe_allow_html=True)
                
                st.markdown("---")
                with st.container():
                    st.subheader("Analyze Business Impact")
                    calc_cols = st.columns([0.4, 0.6])
                    with calc_cols[0]:
                        avg_daily_cost = st.number_input(
                            "Enter Average Daily Employee Cost ($)",
                            min_value=0,
                            value=100,
                            step=10,
                            help="Enter an estimated average cost per employee per day to calculate the financial impact of lost mandays."
                        )
                    with calc_cols[1]:
                        estimated_cost = total_absenteeism_val * avg_daily_cost
                        st.markdown(f"""
                        <div class="kpi-card" style="padding: 18px;">
                            <div class="kpi-title" style="margin-bottom: 4px;">Estimated Cost of Absenteeism</div>
                            <div class="kpi-value" style="font-size: 2.2rem;">${estimated_cost:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                
                col1, col2 = st.columns([0.4, 0.6])
                with col1:
                    st.subheader("Leave Breakdown")
                    fig_pie = create_plotly_pie_chart(filtered_kpis.get('leave_breakdown', {}))
                    if fig_pie: st.plotly_chart(fig_pie, use_container_width=True)
                with col2:
                    st.subheader("Monthly Attendance Trends")
                    monthly_trends_for_chart = logic.calculate_monthly_trends(filtered_daily_df)
                    fig_trends = create_subplots_trend_charts(monthly_trends_for_chart)
                    if fig_trends: st.plotly_chart(fig_trends, use_container_width=True)
                
                st.markdown("---")
                
                st.subheader("Functional Lead Monthly Performance")
                grouped_trend_data = logic.calculate_grouped_trends(filtered_daily_df)

                if not grouped_trend_data.empty:
                    control_col, info_col = st.columns([0.3, 0.7])
                    with control_col:
                        trend_metric = st.selectbox(
                            "Select Metric to Compare", 
                            ["% Deployment", "Absenteeism Rate", "Presence Rate"], 
                            index=0,
                            key="heatmap_metric_selector"
                        )
                    with info_col:
                         st.markdown(f"<p style='text-align: right; color: var(--subtle-text-color); margin-top: 2rem;'>Color scale indicates performance: Red is high-risk for Absenteeism, Green is high-performance for Deployment/Presence.</p>", unsafe_allow_html=True)

                    heatmap_data = logic.prepare_heatmap_data(grouped_trend_data, filtered_df, trend_metric)
                    
                    if not heatmap_data.empty:
                        color_map = 'Reds' if trend_metric == "Absenteeism Rate" else 'Greens'
                        month_cols = [col for col in heatmap_data.columns if col not in ['Team Size', 'Overall Avg.', 'Trend']]

                        styled_heatmap = heatmap_data.style \
                            .format('{:.1f}%', subset=month_cols + ['Overall Avg.']) \
                            .format('{:.0f}', subset=['Team Size']) \
                            .format({'Trend': style_trend_indicator}) \
                            .background_gradient(cmap=color_map, subset=month_cols) \
                            .background_gradient(cmap=color_map, subset=['Overall Avg.'])
                        
                        st.write(styled_heatmap.to_html(escape=False), unsafe_allow_html=True)

                    else:
                        st.info("Not enough data to generate a comparative heatmap table.")
                else:
                    st.info("Not enough monthly data to generate a comparative trend analysis.")
            else:
                st.info("No data available for the current filter selection.")

            st.markdown("---")
            with st.expander("📖 Methodology & Data Definitions", expanded=False):
                st.markdown(f"""
                This section provides the official definitions and formulas used throughout the dashboard to ensure complete transparency and a single source of truth for all calculations.

                #### **Core Concepts**

                - **Mandays:** The total number of scheduled workdays for an employee in the period. This is the primary denominator for strategic metrics. 
                  - **Formula:** `(Total Accounted-for Days)`. This is equivalent to `Present + Leave + Absent`. Note: Standard weekoffs (`W`) and holidays (`H`) are excluded from this total.

                - **Mandays Worked:** The total number of days an employee was present and productive.
                  - **Corresponds to Codes:** `{', '.join(sorted(list(analyzer.PRESENCE_CODES)))}`

                - **Mandays Lost:** The total number of days lost to unplanned absence.
                  - **Corresponds to Codes:** `{', '.join(sorted(list(analyzer.ABSENCE_CODES)))}`

                ---
                #### **Key Performance Indicators (KPIs)**

                **1. % Deployment (Strategic Metric)**
                - **Description:** Measures the percentage of scheduled work time (`Mandays`) that an employee was actually present and productive. This is a key indicator of resource utilization.
                - **Formula:** `(Mandays Worked / Mandays) * 100`

                **2. Absenteeism Rate (Strategic Metric)**
                - **Description:** Measures the percentage of scheduled work time (`Mandays`) that was lost to unplanned absence.
                - **Formula:** `(Mandays Lost / Mandays) * 100`

                **3. Presence Rate (Operational Metric)**
                - **Description:** Measures productive days as a percentage of all *accounted-for* days (Present, Leave, and Absent). This helps understand an individual's activity pattern.
                - **Formula:** `(Mandays Worked / Mandays) * 100`

                """)

        with tab2:
            st.header(f"AI Strategic Briefing for: {ou_display} | {fl_display} | {mgr_display}")
            
            if not filtered_df.empty:
                total_mandays_val = filtered_df['mandays'].sum()
                total_presence_val = filtered_df['total_presence'].sum()
                total_absenteeism_val = filtered_df['total_absenteeism'].sum()
                deployment_pct_val = (total_presence_val / total_mandays_val * 100) if total_mandays_val > 0 else 0
                
                consecutive_absences = insights.find_consecutive_absence_streaks(filtered_daily_df)
                dow_patterns = insights.find_day_of_week_patterns(filtered_daily_df, filtered_df)
                
                st.subheader("Gemini AI Analyst")
                st.markdown("Generate a top-line summary, identify key risks, and receive actionable recommendations from our integrated AI strategist.")
                if st.button("🤖 Generate Strategic Briefing"):
                    with st.spinner("AI Strategist is analyzing the data portfolio..."):
                        prompt = f"""
                        As a C-Suite level HR Strategist, provide an executive briefing based on the following attendance data for the group: {ou_display} | {fl_display} | {mgr_display}.
                        Your audience is the CEO. Be concise, direct, and focus on business impact.

                        **Key Strategic Data Points:**
                        - Total Employees: {len(filtered_df)}
                        - Deployment Rate: {deployment_pct_val:.2f}%
                        - Total Mandays Worked: {total_presence_val:,.0f}
                        - Total Mandays Lost to Unplanned Absence: {total_absenteeism_val:,.0f}

                        **Automated Red Flags:**
                        """
                        if not consecutive_absences.empty:
                            prompt += f"\n- **Attrition Risk - Long Absences:** {len(consecutive_absences)} employee(s) show long, consecutive unplanned absences, signaling potential burnout or personal issues that could lead to attrition."
                        if not dow_patterns.empty:
                            prompt += f"\n- **Engagement Risk - Weekend Adjacency:** {len(dow_patterns)} employee(s) exhibit a pattern of Mon/Fri absences, suggesting potential disengagement or work-life imbalance."
                        if consecutive_absences.empty and dow_patterns.empty:
                            prompt += "\n- No significant negative attendance patterns were automatically flagged. This indicates good operational stability in this cohort."

                        prompt += """

                        **Executive Briefing Structure:**
                        1.  **Top-Line Assessment:** A single, powerful sentence to describe the workforce productivity and health of this group using the Deployment Rate and Mandays Lost.
                        2.  **Strategic Risks:** Bullet points identifying the most critical risks to the business (e.g., "Risk of project delays due to X Mandays Lost," "Potential for decreased morale...").
                        3.  **C-Suite Recommendations:** 2-3 high-level, strategic recommendations for leadership to consider (e.g., "Direct managers to conduct confidential wellness checks," "Review team workload and deadlines to mitigate burnout risk.").
                        """
                        ai_summary = ai_services.generate_narrative(prompt)
                        st.markdown(f'<div class="ai-summary-card">{ai_summary}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("Detailed Findings (Red Flags)")
                st.markdown("Prioritized alerts based on automated analysis of attendance patterns.")
                with st.expander(f"🚩 Long Absence Streaks ({len(consecutive_absences)} found)", expanded=not consecutive_absences.empty):
                    st.markdown("**Business Impact:** Long, unplanned absence streaks can be an early indicator of significant personal issues, health problems, or employee burnout. They pose a direct risk to productivity and team morale, and may be a precursor to employee turnover.")
                    if not consecutive_absences.empty: st.dataframe(consecutive_absences, use_container_width=True)
                    else: st.success("No employees met the criteria for long absence streaks in this view.")
                with st.expander(f"⚠️ Weekend Adjacency Patterns ({len(dow_patterns)} found)", expanded=not dow_patterns.empty):
                    st.markdown("**Business Impact:** A strong pattern of unplanned absences on Mondays or Fridays can suggest issues with work-life balance or low engagement. This can erode team productivity over time and may indicate underlying cultural issues that need addressing.")
                    if not dow_patterns.empty: st.dataframe(dow_patterns, use_container_width=True)
                    else: st.success("No employees showed a significant pattern of Mon/Fri absences in this view.")
            else:
                st.info("No data available for AI briefing in the current filter selection.")

        with tab3:
            st.header("Hierarchical Team Drill-Down")
            # Added Context for the Deep Dive
            st.markdown(f"Analyze performance by manager. **Period Working Days: {period_working_days}**") 
            
            if filtered_df.empty:
                st.info("No manager data to display for the current filter selection.")
            else:
                for fl_name, fl_group in filtered_df.groupby('Functional Lead'):
                    st.subheader(f"Functional Lead: {fl_name}")
                    for mgr_name, mgr_group in fl_group.groupby('Reporting_Manager'):
                        if mgr_group.empty: continue
                        
                        mgr_mandays = mgr_group['mandays'].sum()
                        mgr_team_size = len(mgr_group)

                        # NEW: Manager Standard Capacity
                        mgr_standard_cap = mgr_team_size * period_working_days

                        mgr_absenteeism = mgr_group['total_absenteeism'].sum()
                        mgr_absenteeism_rate = (mgr_absenteeism / mgr_mandays * 100) if mgr_mandays > 0 else 0
                        
                        status_icon = "⚠️" if mgr_absenteeism_rate > 7.0 else "✅"
                        
                        # UPDATED LABEL to show Actual / Cap
                        expander_label = (
                            f"**{mgr_name}** ({mgr_team_size} Emps) | "
                            f"Mandays: **{mgr_mandays:,.0f}**/{mgr_standard_cap:,.0f} | "
                            f"Absenteeism: **{mgr_absenteeism_rate:.1f}%** {status_icon}"
                        )
                        
                        with st.expander(expander_label):
                            display_group = mgr_group.rename(columns={
                                'Employee ID': 'Emp. ID', 'Employee Name': 'Name',
                                'total_presence': 'Present', 'total_leave': 'Leave',
                                'total_absenteeism': 'Absent', 'mandays': 'Mandays'
                            })
                            st.dataframe(display_group[[
                                'Emp. ID', 'Name', 'Present', 'Leave', 'Absent', 'Mandays'
                            ]], use_container_width=True)
        
        with tab4:
            st.header("Leadership Scorecard: Strategic Overview")
            st.markdown("This analysis provides a clear, data-driven summary of manager performance, focusing on team health and engagement.")

            manager_analysis_result = logic.get_manager_quadrant_analysis(filtered_df) 
            matrix_data = manager_analysis_result.get("matrix_data", pd.DataFrame())
            analysis_summary = manager_analysis_result.get("analysis", {})

            if not matrix_data.empty and len(matrix_data) > 1:
                with st.expander("Methodology & Definitions: Understanding the Data", expanded=True):
                    st.markdown("""
                    This analysis categorizes each manager into one of four groups to identify leadership effectiveness and potential team health issues. Here is a complete breakdown of the methodology:

                    **1. The Metrics (The Columns)**
                    - **Absenteeism %**: Calculated as `(Unplanned Absences / Total Mandays) * 100`. This is the primary indicator of team health. **High percentages are a major red flag.**
                    - **Extra Effort %**: Calculated as `(Weekend & Holiday Work / Total Present Days) * 100`. This uses the `W*` and `H*` codes. It reflects team commitment, but a very high rate can be an early warning sign of burnout.
                    - **Team Size**: The number of employees reporting to the manager.

                    **2. The Status Categories (The Story)**
                    The categories are determined by comparing each manager's metrics against the average for the entire group.
                    - **🔥 Burnout Risk**: Managers whose teams have **above-average absenteeism** AND **above-average extra effort**. This is the most critical group, signifying unsustainable pressure.
                    - **🚩 High Risk**: Managers whose teams have **above-average absenteeism** but **below-average extra effort**. This indicates potential issues with low engagement, poor morale, or ineffective leadership.
                    - **✅ Star Performer**: Managers whose teams have **below-average absenteeism** but **above-average extra effort**. These are highly engaged and committed teams.
                    - **⚖️ Stable Cluster**: Managers whose teams have **below-average absenteeism** AND **below-average extra effort**. This is the reliable, consistent core of the organization.
                    """)

                if not matrix_data.empty:
                    display_df = matrix_data.copy()
                    
                    manager_to_quadrant = {}
                    for quadrant, managers in analysis_summary.items():
                        if isinstance(managers, list):
                            for manager in managers:
                                manager_to_quadrant[manager['name']] = quadrant

                    display_df['quadrant'] = display_df['manager_name'].map(manager_to_quadrant)
                    
                    status_map = {
                        "star_performers": "✅ Star Performer",
                        "burnout_risk": "🔥 Burnout Risk",
                        "stable_uninspired": "⚖️ Stable Cluster",
                        "high_risk": "🚩 High Risk"
                    }
                    display_df['Status'] = display_df['quadrant'].map(status_map)

                    display_df.rename(columns={
                        'manager_name': 'Manager',
                        'team_size': 'Team Size',
                        'absenteeism_rate': 'Absenteeism %',
                        'extra_effort_rate': 'Extra Effort %'
                    }, inplace=True)

                    final_df = display_df[['Status', 'Manager', 'Team Size', 'Absenteeism %', 'Extra Effort %']].sort_values(by="Absenteeism %", ascending=False)
                    
                    st.subheader("Strategic Manager Overview")
                    st.markdown("Use the color-coding to instantly identify areas of concern. Sort by clicking on column headers.")
                    
                    st.dataframe(
                        final_df.style
                            .background_gradient(cmap='Reds', subset=['Absenteeism %'])
                            .background_gradient(cmap='YlOrBr', subset=['Extra Effort %'])
                            .format({
                                'Absenteeism %': '{:.1f}%',
                                'Extra Effort %': '{:.1f}%'
                            }),
                        use_container_width=True
                    )
            else:
                st.info("Not enough manager data to generate the performance analysis (at least 2 managers are required for comparison).")

else:
    st.info("Please upload an attendance file to begin the analysis.")