# components/exit_analysis/app/exit_app.py

import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from exit_analysis import analyzer, logic

# --- Page Configuration: Must be the first Streamlit command ---
st.set_page_config(page_title="HR-Insight | Exit Command Center", page_icon="🚪", layout="wide")

# --- UI/UX Styling ---
def load_css():
    """Injects the custom CSS for the full 'Command Center' theme."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
        :root {
            --primary-bg: #111111; --secondary-bg: #1E1E1E; --border-color: #333333;
            --text-color: #EAEAEA; --subtle-text-color: #A0A0A0; --primary-accent: #00A99D;
            --highlight-accent: #D4AF37; --risk-color: #E57373;
            --header-font: 'Plus Jakarta Sans', sans-serif; --body-font: 'Inter', sans-serif;
        }
        .stApp { background-color: var(--primary-bg); color: var(--text-color); }
        h1, h2, h3, h4 { font-family: var(--header-font); font-weight: 700; color: var(--text-color); }
        .stMarkdown, .stDataFrame, .stSelectbox, .stButton>button { font-family: var(--body-font); }
        
        /* Interactive Theme Button Styling */
        .stButton>button {
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            text-align: left;
            transition: all 0.2s ease-in-out;
            width: 100%;
        }
        .stButton>button:hover {
            border-left: 4px solid var(--highlight-accent);
            transform: translateY(-3px);
            background-color: #2a2a2a;
        }
        .stButton>button p { /* Target the text inside the button */
            color: var(--highlight-accent);
            font-family: var(--header-font);
            font-size: 1.2rem;
            font-weight: 700;
        }
        /* Style for the "Back" button */
        .stButton>button.back-button {
            background-color: var(--secondary-bg);
            border: 1px solid var(--primary-accent);
            color: var(--primary-accent);
        }

        /* Styling for verbatim comment display */
        .comment-card {
            border-left: 3px solid var(--subtle-text-color);
            padding-left: 1rem;
            margin-bottom: 1.5rem;
            background-color: var(--secondary-bg);
            border-radius: 8px;
            padding: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# --- UI Rendering Functions ---

def render_overview(insights):
    """Renders the main dashboard view with interactive theme cards."""
    st.header("Strategic Attrition Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ Top Reasons for Satisfaction (Praise Themes)")
        praise_themes = insights.get('praise_themes', [])
        if not praise_themes:
            st.info("No significant positive themes were identified.")
        else:
            for theme in praise_themes:
                # When a button is clicked, it sets session_state and reruns
                if st.button(theme['name'], key=f"btn_{theme['name']}", use_container_width=True):
                    st.session_state.selected_theme = theme['name']
                    st.rerun()

    with col2:
        st.markdown("#### 🚩 Top Drivers of Attrition (Concern Themes)")
        concern_themes = insights.get('concern_themes', [])
        if not concern_themes:
            st.info("No significant negative themes were identified.")
        else:
            for theme in concern_themes:
                if st.button(theme['name'], key=f"btn_{theme['name']}", use_container_width=True):
                    st.session_state.selected_theme = theme['name']
                    st.rerun()

def render_deep_dive(selected_theme, employee_df):
    """Renders the detailed drill-down view for a selected theme."""
    st.header(f"Deep Dive: {selected_theme}")
    
    if st.button("⬅️ Back to Overview"):
        st.session_state.selected_theme = None
        st.rerun()

    # Filter the DataFrame to find all employees tagged with the selected theme
    filtered_df = employee_df[employee_df['assigned_themes'].apply(lambda themes: selected_theme in themes)]

    if filtered_df.empty:
        st.warning("No specific employee records found for this theme.")
        return

    st.markdown(f"Found **{len(filtered_df)} employees** whose feedback relates to this theme.")
    st.markdown("---")
    
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        st.subheader("Verbatim Comments (The 'Why')")
        # Heuristically find the free-text question columns
        text_cols = [c for c in filtered_df.columns if 'what' in c or 'suggestion' in c or 'comment' in c or 'addtional' in c]
        for _, row in filtered_df.iterrows():
            # Consolidate all non-empty comments for a clean display
            all_comments = ". ".join(str(s) for s in row[text_cols] if pd.notna(s) and str(s).strip() and len(str(s)) > 1)
            if all_comments:
                st.markdown(f'<div class="comment-card"><i>"{all_comments}"</i></div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("Demographic Breakdown (The 'Who')")
        if 'designation' in filtered_df.columns:
            fig = px.pie(filtered_df, names='designation', title='Breakdown by Designation', hole=0.4)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='var(--text-color)'), legend_title_text='')
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Traceable Data (The 'Proof')")
    display_cols = ['designation', 'resignationreason', 'sentiment'] + text_cols
    # Ensure all columns exist before trying to display them
    final_display_cols = [col for col in display_cols if col in filtered_df.columns]
    st.dataframe(filtered_df[final_display_cols], use_container_width=True)

# --- Main Application Execution ---

load_css()
# Initialize session state variables to manage the app's state
if 'exit_insights' not in st.session_state: st.session_state.exit_insights = None
if 'file_name' not in st.session_state: st.session_state.file_name = None
if 'selected_theme' not in st.session_state: st.session_state.selected_theme = None

st.title("🚪 Exit Insight Command Center")
uploaded_file = st.file_uploader("Upload Exit Form Data", type=['xlsx', 'xls', 'csv', 'txt'], key="exit_data_uploader")

if uploaded_file:
    # Process only if it's a new file to avoid redundant computation
    if st.session_state.file_name != uploaded_file.name:
        st.session_state.selected_theme = None # Reset view on new file upload
        st.session_state.file_name = uploaded_file.name
        with st.spinner("Running Advanced AI Analysis... Interpreting themes..."):
            # Full end-to-end pipeline call
            insights = logic.generate_exit_insights(analyzer.process_exit_data(uploaded_file.getvalue()))
            st.session_state.exit_insights = insights
        st.rerun()

if st.session_state.exit_insights:
    employee_df = pd.DataFrame(st.session_state.exit_insights['employee_data'])
    
    # This is the core logic that decides which view to show
    if st.session_state.selected_theme is None:
        render_overview(st.session_state.exit_insights)
    else:
        render_deep_dive(st.session_state.selected_theme, employee_df)
else:
    st.info("Please upload your exit analysis data file to begin.")