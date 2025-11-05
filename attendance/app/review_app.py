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
st.set_page_config(page_title="HR-Insight | Executive Command Center", page_icon="💎", layout="wide")

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
        p, .stMarkdown, .stDataFrame, .stSelectbox {
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
        .stDownloadButton>button {
            border-radius: 8px;
            background-color: var(--secondary-bg);
            color: var(--primary-accent);
            border: 1px solid var(--primary-accent);
            font-weight: 600;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def create_plotly_pie_chart(data: dict):
    # ... (code remains unchanged)
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
    # ... (code remains unchanged)
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

st.title("💎 HR-Insight Executive Command Center")
st.markdown("##### Strategic Attendance Intelligence for C-Suite Decision-Making")
st.markdown("---")

uploaded_file = st.file_uploader("Upload Adrenalin Max Attendance Report", type=['xlsx', 'xls'])

if uploaded_file:
    if st.session_state.file_name != uploaded_file.name:
        st.session_state.file_name = uploaded_file.name
        with st.spinner("Processing strategic data..."):
            file_bytes = uploaded_file.getvalue()
            st.session_state.master_df, st.session_state.daily_df = analyzer.analyze_attendance(file_bytes)
        st.success(f"File '{uploaded_file.name}' processed successfully!")
        st.rerun()

if not st.session_state.master_df.empty:
    master_df = st.session_state.master_df
    daily_df = st.session_state.daily_df

    # ... (Sidebar and filtering logic remains unchanged)
    st.sidebar.header("Filters & Actions")
    ou_list = ["(All OUs)"] + sorted(master_df['OU Name'].unique().tolist())
    selected_ou = st.sidebar.selectbox("Filter by Business Unit (OU)", ou_list)
    ou_filtered_df = master_df if selected_ou == "(All OUs)" else master_df[master_df['OU Name'] == selected_ou]
    
    fl_list = ["(All Functional Leads)"] + sorted(ou_filtered_df['Functional Lead'].unique().tolist())
    selected_fl = st.sidebar.selectbox("Filter by Functional Lead", fl_list)
    fl_filtered_df = ou_filtered_df if selected_fl == "(All Functional Leads)" else ou_filtered_df[ou_filtered_df['Functional Lead'] == selected_fl]
    
    mgr_list = ["(All Reporting Managers)"] + sorted(fl_filtered_df['Reporting_Manager'].unique().tolist())
    selected_mgr = st.sidebar.selectbox("Filter by Reporting Manager", mgr_list)
    filtered_df = fl_filtered_df if selected_mgr == "(All Reporting Managers)" else fl_filtered_df[fl_filtered_df['Reporting_Manager'] == selected_mgr]

    employee_ids_in_view = filtered_df['Employee ID'].unique()
    filtered_daily_df = daily_df[daily_df['Employee ID'].isin(employee_ids_in_view)]
    
    company_summary_data = logic.generate_attendance_summary(master_df, "Company-Wide")
    company_kpis = company_summary_data.get('company_summary', {})
    
    filtered_summary_data = logic.generate_attendance_summary(filtered_df, "Current View")
    filtered_kpis = filtered_summary_data.get('company_summary', {})
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Download Report")
    excel_bytes = exporter.create_excel_report(filtered_summary_data, filtered_df)
    st.sidebar.download_button(
        label="📥 Download Detailed Report", data=excel_bytes,
        file_name=f"HR_Insight_Report_{selected_ou}_{selected_fl}_{selected_mgr}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    tab1, tab2, tab3, tab4 = st.tabs(["📈 KPI Overview", "🧠 AI Strategic Briefing", "🏢 Team Deep Dive", "📊 Leadership Scorecard"])

    with tab1:
        # ... (code for tab1 remains unchanged)
        st.header(f"Analysis for: {selected_ou} | {selected_fl} | {selected_mgr}")
        
        if filtered_kpis.get("total_employees", 0) > 0:
            cols = st.columns(4)
            
            with cols[0]:
                pr_delta = filtered_kpis['presence_rate'] - company_kpis.get('presence_rate', 0)
                delta_color = "var(--primary-accent)" if pr_delta >= 0 else "var(--risk-color)"
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Presence Rate</div><div class="kpi-value">{filtered_kpis['presence_rate']:.1f}%</div><div class="kpi-delta" style="color:{delta_color};">{pr_delta:+.1f}% vs. Company Avg.</div></div>""", unsafe_allow_html=True)

            with cols[1]:
                lr_delta = filtered_kpis['leave_rate'] - company_kpis.get('leave_rate', 0)
                delta_color = "var(--risk-color)" if lr_delta >= 0 else "var(--primary-accent)"
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Leave Rate</div><div class="kpi-value">{filtered_kpis['leave_rate']:.1f}%</div><div class="kpi-delta" style="color:{delta_color};">{lr_delta:+.1f}% vs. Company Avg.</div></div>""", unsafe_allow_html=True)

            with cols[2]:
                ar_delta = filtered_kpis['absenteeism_rate'] - company_kpis.get('absenteeism_rate', 0)
                delta_color = "var(--risk-color)" if ar_delta >= 0 else "var(--primary-accent)"
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Absenteeism Rate</div><div class="kpi-value">{filtered_kpis['absenteeism_rate']:.1f}%</div><div class="kpi-delta" style="color:{delta_color};">{ar_delta:+.1f}% vs. Company Avg.</div></div>""", unsafe_allow_html=True)

            with cols[3]:
                st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Filtered Employees</div><div class="kpi-value">{filtered_kpis['total_employees']}</div><div class="kpi-delta" style="color:var(--subtle-text-color);">&nbsp;</div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
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
        else:
            st.info("No data available for the current filter selection.")

    with tab2:
        # ... (code for tab2 remains unchanged)
        st.header(f"AI Strategic Briefing for: {selected_ou} | {selected_fl} | {selected_mgr}")
        consecutive_absences = insights.find_consecutive_absence_streaks(filtered_daily_df)
        dow_patterns = insights.find_day_of_week_patterns(filtered_daily_df, filtered_df)
        
        st.subheader("Gemini AI Analyst")
        st.markdown("Generate a top-line summary, identify key risks, and receive actionable recommendations from our integrated AI strategist.")
        if st.button("🤖 Generate Strategic Briefing"):
            with st.spinner("AI Strategist is analyzing the data portfolio..."):
                prompt = f"""
                As a C-Suite level HR Strategist, provide an executive briefing based on the following attendance data for the group: {selected_ou} | {selected_fl} | {selected_mgr}.
                Your audience is the CEO. Be concise, direct, and focus on business impact.

                **Data Points:**
                - Total Employees: {filtered_kpis.get('total_employees', 0)}
                - Presence Rate: {filtered_kpis.get('presence_rate', 0):.2f}%
                - Leave Rate: {filtered_kpis.get('leave_rate', 0):.2f}%
                - Absenteeism Rate: {filtered_kpis.get('absenteeism_rate', 0):.2f}%

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
                1.  **Top-Line Assessment:** A single, powerful sentence to describe the workforce health of this group.
                2.  **Strategic Risks:** Bullet points identifying the most critical risks to the business (e.g., "Risk of project delays due to high absenteeism," "Potential for decreased morale...").
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

    with tab3:
        # ... (code for tab3 remains unchanged)
        st.header("Hierarchical Team Drill-Down")
        st.markdown("Analyze performance by manager. Status indicators highlight teams with absenteeism over the 7% threshold.")
        
        if filtered_df.empty:
            st.info("No manager data to display for the current filter selection.")
        else:
            for fl_name, fl_group in filtered_df.groupby('Functional Lead'):
                st.subheader(f"Functional Lead: {fl_name}")
                for mgr_name, mgr_group in fl_group.groupby('Reporting_Manager'):
                    mgr_summary = logic.generate_attendance_summary(mgr_group, mgr_name)
                    mgr_kpis = mgr_summary.get('company_summary', {})
                    rate = mgr_kpis.get('absenteeism_rate', 0)
                    
                    status_icon = "⚠️" if rate > 7.0 else "✅"
                    expander_label = (
                        f"**{mgr_name}** ({mgr_kpis.get('total_employees', 0)} Employees) | "
                        f"Absenteeism Rate: **{rate:.1f}%** {status_icon}"
                    )
                    
                    with st.expander(expander_label):
                        display_group = mgr_group.rename(columns={
                            'Employee ID': 'Emp. ID', 'Employee Name': 'Name',
                            'total_presence': 'Present', 'total_leave': 'Leave',
                            'total_absenteeism': 'Absent', 'total_workable_days': 'Workable Days'
                        })
                        st.dataframe(display_group[[
                            'Emp. ID', 'Name', 'Present', 'Leave', 'Absent', 'Workable Days'
                        ]], use_container_width=True)
    
    with tab4:
        st.header("Leadership Scorecard: Strategic Overview")
        st.markdown("This analysis provides a clear, data-driven summary of manager performance, focusing on team health and engagement.")

        manager_analysis_result = logic.get_manager_quadrant_analysis(fl_filtered_df)
        matrix_data = manager_analysis_result.get("matrix_data", pd.DataFrame())
        analysis_summary = manager_analysis_result.get("analysis", {})

        if not matrix_data.empty and len(matrix_data) > 1:
            # --- The new, self-explanatory methodology section ---
            with st.expander("Methodology & Definitions: Understanding the Data", expanded=True):
                st.markdown("""
                This analysis categorizes each manager into one of four groups to identify leadership effectiveness and potential team health issues. Here is a complete breakdown of the methodology:

                **1. The Metrics (The Columns)**
                - **Absenteeism %**: Calculated as `(Unplanned Absences / Total Workable Days) * 100`. This uses the `LWP` and `ABSENT` codes from the raw data. It is the primary indicator of team health. **High percentages are a major red flag.**
                - **Extra Effort %**: Calculated as `(Weekend & Holiday Work / Total Present Days) * 100`. This uses the `W*` and `H*` codes. It reflects team commitment, but a very high rate can be an early warning sign of burnout.
                - **Team Size**: The number of employees reporting to the manager.

                **2. The Status Categories (The Story)**
                The categories are determined by comparing each manager's metrics against the average for the entire group.
                - **🔥 Burnout Risk**: Managers whose teams have **above-average absenteeism** AND **above-average extra effort**. This is the most critical group, signifying unsustainable pressure.
                - **🚩 High Risk**: Managers whose teams have **above-average absenteeism** but **below-average extra effort**. This indicates potential issues with low engagement, poor morale, or ineffective leadership.
                - **✅ Star Performer**: Managers whose teams have **below-average absenteeism** but **above-average extra effort**. These are highly engaged and committed teams.
                - **⚖️ Stable Cluster**: Managers whose teams have **below-average absenteeism** AND **below-average extra effort**. This is the reliable, consistent core of the organization.
                """)

            # --- Engineer the final DataFrame for display ---
            if not matrix_data.empty:
                display_df = matrix_data.copy()
                
                # Create a mapping from manager name to their quadrant
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

                # Format and select final columns
                display_df.rename(columns={
                    'manager_name': 'Manager',
                    'team_size': 'Team Size',
                    'absenteeism_rate': 'Absenteeism %',
                    'extra_effort_rate': 'Extra Effort %'
                }, inplace=True)

                final_df = display_df[['Status', 'Manager', 'Team Size', 'Absenteeism %', 'Extra Effort %']].sort_values(by="Absenteeism %", ascending=False)
                
                st.subheader("Strategic Manager Overview")
                st.markdown("Use the color-coding to instantly identify areas of concern. Sort by clicking on column headers.")
                
                # Display the styled DataFrame
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