import pandas as pd
from typing import Dict, List
from .schemas import DataQualityReport, CompanySummary, ManagerSummary, EmployeeRecord

# This is our centralized logic hub, containing all business calculations.

def generate_attendance_summary(df: pd.DataFrame, period: str) -> dict:
    """
    Takes a processed, aggregated DataFrame and computes all summary statistics (KPIs).
    """
    if df.empty:
        return {
            "analysis_period": f"No data for: {period}",
            "data_quality_report": DataQualityReport(total_employees_processed=0, employees_missing_manager_name=0, employees_with_zero_workable_days=0).dict(),
            "company_summary": CompanySummary(total_employees=0, presence_rate=0, leave_rate=0, absenteeism_rate=0, total_presence=0, total_leave=0, total_absenteeism=0, total_workable=0, total_extra_work_days=0, leave_breakdown={}).dict(),
            "manager_summary": []
        }
    dq_report = DataQualityReport(
        total_employees_processed=len(df),
        employees_missing_manager_name=len(df[df['Reporting_Manager'] == 'N/A']),
        employees_with_zero_workable_days=len(df[df['total_workable_days'] <= 0])
    )
    total_presence = df['total_presence'].sum()
    total_leave = df['total_leave'].sum()
    total_absenteeism = df['total_absenteeism'].sum()
    total_workable = df['total_workable_days'].sum()
    total_extra_work = df['worked_weekends'].sum() + df['worked_holidays'].sum()
    leave_breakdown_cols = [col for col in df.columns if col.startswith('leave_')]
    company_leave_breakdown = {col.replace('leave_', '').upper(): df[col].sum() for col in leave_breakdown_cols}
    company_summary = CompanySummary(
        total_employees=len(df),
        presence_rate=(total_presence / total_workable * 100) if total_workable > 0 else 0,
        leave_rate=(total_leave / total_workable * 100) if total_workable > 0 else 0,
        absenteeism_rate=(total_absenteeism / total_workable * 100) if total_workable > 0 else 0,
        total_presence=total_presence,
        total_leave=total_leave,
        total_absenteeism=total_absenteeism,
        total_workable=total_workable,
        total_extra_work_days=total_extra_work,
        leave_breakdown=company_leave_breakdown
    )
    manager_summary_list = []
    if 'Reporting_Manager' in df.columns:
        for manager_name, group in df.groupby('Reporting_Manager'):
            team_presence = group['total_presence'].sum()
            team_leave = group['total_leave'].sum()
            team_absenteeism = group['total_absenteeism'].sum()
            team_workable = group['total_workable_days'].sum()
            team_members_records = group.to_dict(orient='records')
            manager_entry = ManagerSummary(
                manager_name=str(manager_name),
                team_size=len(group),
                presence_rate=(team_presence / team_workable * 100) if team_workable > 0 else 0,
                leave_rate=(team_leave / team_workable * 100) if team_workable > 0 else 0,
                absenteeism_rate=(team_absenteeism / team_workable * 100) if team_workable > 0 else 0,
                team_members=[EmployeeRecord.parse_obj(rec) for rec in team_members_records]
            )
            manager_summary_list.append(manager_entry.dict())
    return {
        "analysis_period": f"Analysis for: {period}",
        "data_quality_report": dq_report.dict(),
        "company_summary": company_summary.dict(),
        "manager_summary": manager_summary_list
    }

def calculate_monthly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly trends, now intelligently handling partial start/end months
    and creating a clean 'DisplayMonth' label for the chart's X-axis.
    """
    if daily_df.empty:
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
    monthly_summary['total_workable'] = monthly_summary['presence'] + monthly_summary['leave'] + monthly_summary['total_absenteeism']
    monthly_summary['Presence Rate'] = (monthly_summary['presence'] / monthly_summary['total_workable'] * 100).fillna(0)
    monthly_summary['Leave Rate'] = (monthly_summary['leave'] / monthly_summary['total_workable'] * 100).fillna(0)
    monthly_summary['Absenteeism Rate'] = (monthly_summary['total_absenteeism'] / monthly_summary['total_workable'] * 100).fillna(0)

    def create_display_label(row):
        month_period = row['Month']
        total_days_in_month = month_period.days_in_month
        if row['days_in_data'] < total_days_in_month:
            return f"{month_period.strftime('%b %Y')} ({row['days_in_data']} days)"
        else:
            return month_period.strftime('%b %Y')

    monthly_summary['DisplayMonth'] = monthly_summary.apply(create_display_label, axis=1)
    monthly_summary['Month'] = monthly_summary['Month'].astype(str)
    
    return monthly_summary.sort_values('Month')

# --- RE-ENGINEERED LOGIC FOR FEATURE 1: MANAGER QUADRANT ANALYSIS ---
def get_manager_quadrant_analysis(df: pd.DataFrame) -> dict:
    """
    Performs a full quadrant analysis on manager performance, categorizing each manager
    and returning a structured dictionary for the strategic briefing.
    """
    if df.empty or 'Reporting_Manager' not in df.columns:
        return {"matrix_data": pd.DataFrame(), "analysis": {}}

    manager_groups = df.groupby('Reporting_Manager')
    
    manager_metrics = []
    for name, group in manager_groups:
        if name == 'N/A' or len(group) == 0:
            continue

        total_workable = group['total_workable_days'].sum()
        total_presence = group['total_presence'].sum()
        total_absenteeism = group['total_absenteeism'].sum()
        total_extra_days = group['worked_weekends'].sum() + group['worked_holidays'].sum()

        absenteeism_rate = (total_absenteeism / total_workable * 100) if total_workable > 0 else 0
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

    # --- Categorization Logic ---
    avg_absenteeism = matrix_data['absenteeism_rate'].mean()
    avg_effort = matrix_data['extra_effort_rate'].mean()

    analysis = {
        "avg_absenteeism": avg_absenteeism,
        "avg_effort": avg_effort,
        "star_performers": [],
        "burnout_risk": [],
        "stable_uninspired": [],
        "high_risk": []
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
        else: # High absenteeism, low effort
            analysis["high_risk"].append(manager_record)
            
    return {"matrix_data": matrix_data, "analysis": analysis}
# --- END OF RE-ENGINEERED LOGIC ---```