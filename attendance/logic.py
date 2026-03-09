# components/attendance/logic.py

import pandas as pd
from typing import Dict, List, Tuple

# This is our centralized logic hub, containing all business calculations.

def _calculate_kpis_for_dataframe(df: pd.DataFrame) -> dict:
    """
    A simple, non-recursive helper to calculate KPIs for any given DataFrame.
    This function performs the core math and is called by other functions.
    """
    if df.empty:
        return {
            "total_employees": 0, "presence_rate": 0, "leave_rate": 0, "absenteeism_rate": 0,
            "total_presence": 0, "total_leave": 0, "total_absenteeism": 0, "mandays": 0,
            "total_extra_work_days": 0, "leave_breakdown": {}
        }

    total_presence = df['total_presence'].sum()
    total_leave = df['total_leave'].sum()
    total_absenteeism = df['total_absenteeism'].sum()
    total_mandays = df['mandays'].sum()
    total_extra_work = df['worked_weekends'].sum() + df['worked_holidays'].sum()
    leave_breakdown_cols = [col for col in df.columns if col.startswith('leave_')]
    company_leave_breakdown = {col.replace('leave_', '').upper(): df[col].sum() for col in leave_breakdown_cols}

    return {
        "total_employees": len(df),
        "presence_rate": (total_presence / total_mandays * 100) if total_mandays > 0 else 0,
        "leave_rate": (total_leave / total_mandays * 100) if total_mandays > 0 else 0,
        "absenteeism_rate": (total_absenteeism / total_mandays * 100) if total_mandays > 0 else 0,
        "total_presence": total_presence,
        "total_leave": total_leave,
        "total_absenteeism": total_absenteeism,
        "mandays": total_mandays,
        "total_extra_work_days": total_extra_work,
        "leave_breakdown": company_leave_breakdown
    }

def _calculate_kpis(df: pd.DataFrame, period: str) -> dict:
    """
    Orchestrates the calculation of KPIs for the main group and for each manager subgroup.
    """
    dq_report = {
        "total_employees_processed": len(df),
        "employees_missing_manager_name": len(df[df['Reporting_Manager'] == 'N/A']),
        "employees_with_zero_mandays": len(df[df['mandays'] <= 0])
    }
    
    company_summary = _calculate_kpis_for_dataframe(df)

    manager_summary_list = []
    if 'Reporting_Manager' in df.columns and not df.empty:
        if 'Functional Lead' in df.columns:
            grouped = df.groupby(['Functional Lead', 'Reporting_Manager'])
        else:
            grouped = df.groupby('Reporting_Manager')

        for name_tuple, group in grouped:
            if isinstance(name_tuple, tuple) and len(name_tuple) == 2:
                fl_name, manager_name = name_tuple
            else:
                fl_name, manager_name = 'N/A', name_tuple
            
            manager_kpis = _calculate_kpis_for_dataframe(group)
            
            manager_entry = {
                "manager_name": str(manager_name),
                "team_size": manager_kpis.get("total_employees"),
                "presence_rate": manager_kpis.get("presence_rate"),
                "leave_rate": manager_kpis.get("leave_rate"),
                "absenteeism_rate": manager_kpis.get("absenteeism_rate"),
                "team_members": group.to_dict(orient='records'),
                "functional_lead": fl_name
            }
            manager_summary_list.append(manager_entry)

    return {
        "analysis_period": f"Analysis for: {period}",
        "data_quality_report": dq_report,
        "company_summary": company_summary,
        "manager_summary": manager_summary_list
    }

def generate_attendance_summary(
    df: pd.DataFrame, 
    period: str, 
    master_df: pd.DataFrame = None,
    daily_df: pd.DataFrame = None
) -> Tuple[dict, dict]:
    """
    Top-level function. Takes a processed, aggregated DataFrame and computes all summary statistics.
    Includes logic to calculate the 'Standard Capacity' baseline using daily_df.
    """
    if df.empty:
        empty_summary = {
            "analysis_period": f"No data for: {period}",
            "data_quality_report": {"total_employees_processed": 0, "employees_missing_manager_name": 0, "employees_with_zero_mandays": 0},
            "company_summary": {"total_employees": 0, "presence_rate": 0, "leave_rate": 0, "absenteeism_rate": 0, "total_presence": 0, "total_leave": 0, "total_absenteeism": 0, "mandays": 0, "total_extra_work_days": 0, "leave_breakdown": {}},
            "manager_summary": []
        }
        return empty_summary, empty_summary.get('company_summary', {})

    summary_dict = _calculate_kpis(df, period)
    
    # --- NEW LOGIC: Calculate Max Working Days (Theoretical Max) ---
    # We count unique dates in the daily file. 
    # The analyzer has already removed 'W' and 'H', so these are valid working days.
    if daily_df is not None and not daily_df.empty and 'Date' in daily_df.columns:
        max_working_days = daily_df['Date'].nunique()
    else:
        max_working_days = 0
    
    # Add this to the summary so the frontend can access it
    summary_dict['period_max_working_days'] = max_working_days
    # ---------------------------------------------------------------
    
    baseline_kpis = {}
    is_single_ou_view = ('OU Name' in df.columns) and (df['OU Name'].nunique() == 1)
    
    if is_single_ou_view and master_df is not None and not master_df.empty and master_df['OU Name'].nunique() > 1:
        current_ou = df['OU Name'].iloc[0]
        peer_df = master_df[master_df['OU Name'] != current_ou]
        if not peer_df.empty:
            peer_kpis = _calculate_kpis_for_dataframe(peer_df)
            baseline_kpis = peer_kpis
            baseline_kpis['baseline_name'] = f"vs. Peer Avg. ({peer_df['OU Name'].nunique()} OUs)"

    if not baseline_kpis and master_df is not None and not master_df.empty:
        company_kpis = _calculate_kpis_for_dataframe(master_df)
        baseline_kpis = company_kpis
        baseline_kpis['baseline_name'] = "vs. Company Avg."

    return summary_dict, baseline_kpis

def calculate_monthly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly trends for Presence, Leave, and Absenteeism Rates based on Mandays.
    """
    if daily_df.empty or 'Date' not in daily_df.columns or len(daily_df['Date'].dt.to_period('M').unique()) < 1:
        return pd.DataFrame()

    daily_df = daily_df.copy()
    daily_df['Date'] = pd.to_datetime(daily_df['Date'])
    daily_df['Month'] = daily_df['Date'].dt.to_period('M')
    
    monthly_summary = daily_df.groupby('Month').agg(
        presence=('presence', 'sum'),
        leave=('leave', 'sum'),
        lwp=('lwp', 'sum'),
        absent=('absent', 'sum'),
        days_in_data=('Date', 'nunique')
    ).reset_index()
    
    monthly_summary['total_absenteeism'] = monthly_summary['lwp'] + monthly_summary['absent']
    monthly_summary['mandays'] = monthly_summary['presence'] + monthly_summary['leave'] + monthly_summary['total_absenteeism']
    
    monthly_summary['Presence Rate'] = (monthly_summary['presence'] / monthly_summary['mandays'] * 100).where(monthly_summary['mandays'] > 0, 0)
    monthly_summary['Leave Rate'] = (monthly_summary['leave'] / monthly_summary['mandays'] * 100).where(monthly_summary['mandays'] > 0, 0)
    monthly_summary['Absenteeism Rate'] = (monthly_summary['total_absenteeism'] / monthly_summary['mandays'] * 100).where(monthly_summary['mandays'] > 0, 0)
    monthly_summary['deployment_percentage'] = (monthly_summary['presence'] / monthly_summary['mandays'] * 100).where(monthly_summary['mandays'] > 0, 0)

    def create_display_label(row):
        month_period = row['Month']
        return month_period.strftime('%b %Y')

    monthly_summary['DisplayMonth'] = monthly_summary.apply(create_display_label, axis=1)
    monthly_summary['Month'] = monthly_summary['Month'].astype(str)
    
    return monthly_summary.sort_values('Month')

def find_statistical_anomalies(monthly_trends: pd.DataFrame) -> List[str]:
    """
    Identifies significant deviations in the most recent month's data compared to the historical average.
    """
    if monthly_trends.empty or len(monthly_trends) < 3:
        return []

    alerts = []
    monthly_trends = monthly_trends.sort_values('Month').reset_index()
    latest_month = monthly_trends.iloc[-1]
    historical_data = monthly_trends.iloc[:-1]
    hist_avg_absenteeism = historical_data['Absenteeism Rate'].mean()
    hist_std_absenteeism = historical_data['Absenteeism Rate'].std()
    
    threshold = hist_avg_absenteeism + (1.5 * hist_std_absenteeism)
    
    if latest_month['Absenteeism Rate'] > threshold:
        latest_rate = latest_month['Absenteeism Rate']
        hist_avg = hist_avg_absenteeism
        percent_increase = ((latest_rate - hist_avg) / hist_avg) * 100 if hist_avg > 0 else 100
        
        alert_string = (
            f"**Strategic Alert:** Absenteeism for **{latest_month['DisplayMonth']} at {latest_rate:.1f}%** "
            f"is significantly higher than the historical average of {hist_avg:.1f}%. "
            f"This represents a **{percent_increase:.0f}% increase**, warranting investigation."
        )
        alerts.append(alert_string)
        
    return alerts

def get_manager_quadrant_analysis(df: pd.DataFrame) -> dict:
    """
    Performs a full quadrant analysis on manager performance.
    """
    if df.empty or 'Reporting_Manager' not in df.columns:
        return {"matrix_data": pd.DataFrame(), "analysis": {}}

    manager_groups = df.groupby('Reporting_Manager')
    
    manager_metrics = []
    for name, group in manager_groups:
        if name == 'N/A' or len(group) == 0:
            continue

        total_mandays = group['mandays'].sum()
        total_presence = group['total_presence'].sum()
        total_absenteeism = group['total_absenteeism'].sum()
        total_extra_days = group['worked_weekends'].sum() + group['worked_holidays'].sum()

        absenteeism_rate = (total_absenteeism / total_mandays * 100) if total_mandays > 0 else 0
        extra_effort_rate = (total_extra_days / total_presence * 100) if total_presence > 0 else 0

        manager_metrics.append({
            'manager_name': name,
            'team_size': len(group),
            'absenteeism_rate': absenteeism_rate,
            'extra_effort_rate': extra_effort_rate
        })
    
    matrix_data = pd.DataFrame(manager_metrics)
    if matrix_data.empty:
        return {"matrix_data": pd.DataFrame(), "analysis": {}}

    avg_absenteeism = matrix_data['absenteeism_rate'].mean()
    avg_effort = matrix_data['extra_effort_rate'].mean()

    analysis = {
        "avg_absenteeism": avg_absenteeism,
        "avg_effort": avg_effort,
        "star_performers": [], "burnout_risk": [],
        "stable_uninspired": [], "high_risk": []
    }

    for index, row in matrix_data.iterrows():
        is_low_absenteeism = row['absenteeism_rate'] <= avg_absenteeism
        is_high_effort = row['extra_effort_rate'] >= avg_effort
        
        manager_record = {
            "name": row['manager_name'],
            "absenteeism": f"{row['absenteeism_rate']:.1f}%",
            "effort": f"{row['extra_effort_rate']:.1f}%"
        }

        if is_low_absenteeism and is_high_effort:
            analysis["star_performers"].append(manager_record)
        elif not is_low_absenteeism and is_high_effort:
            analysis["burnout_risk"].append(manager_record)
        elif is_low_absenteeism and not is_high_effort:
            analysis["stable_uninspired"].append(manager_record)
        else: 
            analysis["high_risk"].append(manager_record)
            
    return {"matrix_data": matrix_data, "analysis": analysis}

def calculate_grouped_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly trends for key metrics, grouped by Functional Lead.
    """
    if daily_df.empty or 'Functional Lead' not in daily_df.columns or daily_df['Date'].dt.to_period('M').nunique() < 1:
        return pd.DataFrame()

    daily_df['Functional Lead'] = daily_df['Functional Lead'].fillna('N/A')
    daily_df['Month'] = daily_df['Date'].dt.to_period('M')
    
    grouped_summary = daily_df.groupby(['Month', 'Functional Lead']).agg(
        presence=('presence', 'sum'),
        leave=('leave', 'sum'),
        lwp=('lwp', 'sum'),
        absent=('absent', 'sum'),
    ).reset_index()
    
    grouped_summary['total_absenteeism'] = grouped_summary['lwp'] + grouped_summary['absent']
    grouped_summary['mandays'] = grouped_summary['presence'] + grouped_summary['leave'] + grouped_summary['total_absenteeism']
    
    grouped_summary['Presence Rate'] = (grouped_summary['presence'] / grouped_summary['mandays'] * 100).where(grouped_summary['mandays'] > 0, 0)
    grouped_summary['Absenteeism Rate'] = (grouped_summary['total_absenteeism'] / grouped_summary['mandays'] * 100).where(grouped_summary['mandays'] > 0, 0)
    grouped_summary['deployment_percentage'] = (grouped_summary['presence'] / grouped_summary['mandays'] * 100).where(grouped_summary['mandays'] > 0, 0)

    grouped_summary['Month'] = grouped_summary['Month'].astype(str)
    
    return grouped_summary.sort_values(['Functional Lead', 'Month'])

def prepare_heatmap_data(grouped_trends: pd.DataFrame, aggregated_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    Pivots the grouped trend data and adds team size, overall average, and a trend indicator for the heatmap table.
    """
    if grouped_trends.empty or aggregated_df.empty:
        return pd.DataFrame()

    metric_column_name = 'deployment_percentage' if metric == '% Deployment' else metric

    heatmap_pivot = grouped_trends.pivot_table(
        index='Functional Lead',
        columns='Month',
        values=metric_column_name,
        aggfunc='mean'
    ).fillna(0).reset_index()
    
    # --- FIX: Use the aggregated_df for all calculations involving summary columns ---
    team_sizes = aggregated_df.groupby('Functional Lead')['Employee ID'].nunique().reset_index()
    team_sizes.rename(columns={'Employee ID': 'Team Size'}, inplace=True)
    
    overall_avg = aggregated_df.groupby('Functional Lead').agg(
        total_presence=('total_presence', 'sum'),
        total_absenteeism=('total_absenteeism', 'sum'),
        mandays=('mandays', 'sum')
    ).reset_index()
    
    overall_avg['Overall Avg.'] = 0.0
    if metric == '% Deployment' or metric == 'Presence Rate':
        overall_avg['Overall Avg.'] = (overall_avg['total_presence'] / overall_avg['mandays'] * 100).where(overall_avg['mandays'] > 0, 0)
    elif metric == 'Absenteeism Rate':
        overall_avg['Overall Avg.'] = (overall_avg['total_absenteeism'] / overall_avg['mandays'] * 100).where(overall_avg['mandays'] > 0, 0)

    final_table = team_sizes.merge(overall_avg[['Functional Lead', 'Overall Avg.']], on='Functional Lead')
    final_table = final_table.merge(heatmap_pivot, on='Functional Lead')
    
    month_cols = [col for col in heatmap_pivot.columns if col != 'Functional Lead']
    trends = []
    for index, row in final_table.iterrows():
        if len(month_cols) < 2:
            trends.append("Stable")
            continue
        
        start_val = row[month_cols[0]]
        end_val = row[month_cols[-1]]
        
        if abs(start_val - end_val) < 0.5:
             trends.append("Stable")
        elif (metric == 'Absenteeism Rate' and end_val < start_val) or \
             ((metric == '% Deployment' or metric == 'Presence Rate') and end_val > start_val):
            trends.append("Improving")
        else:
            trends.append("Worsening")
            
    final_table['Trend'] = trends
    
    new_col_order = ['Functional Lead', 'Team Size', 'Overall Avg.', 'Trend'] + month_cols
    final_table = final_table[new_col_order]

    final_table.set_index('Functional Lead', inplace=True)
    
    return final_table.sort_values(by='Overall Avg.', ascending=(metric != 'Absenteeism Rate'))