# components/attendance/insights.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def find_consecutive_absence_streaks(daily_df, streak_threshold=4):
    """
    Intelligently identifies employees with N or more consecutive days of unplanned absence.
    This version includes robust logic to correctly handle weekends and provides
    clear, contextual start/end dates for each streak.
    """
    try:
        absence_codes = {'LWP', 'ABSENT'}
        daily_with_meta = daily_df.copy()
        
        daily_with_meta['Relieving_Date'] = pd.to_datetime(daily_with_meta['Relieving_Date'], errors='coerce')
        
        valid_absences = daily_with_meta[
            (daily_with_meta['Code'].isin(absence_codes)) &
            ((daily_with_meta['Relieving_Date'].isna()) | (daily_with_meta['Date'] <= daily_with_meta['Relieving_Date']))
        ].sort_values(['Employee ID', 'Date'])

        if valid_absences.empty:
            return pd.DataFrame()

        # --- THE FIX: INTELLIGENT STREAK DETECTION ---
        # A streak is only broken if the gap between absences is > 3 days (i.e., it skips more than a weekend).
        valid_absences['date_diff'] = valid_absences.groupby('Employee ID')['Date'].diff().dt.days
        valid_absences['streak_id'] = (valid_absences['date_diff'] > 3).cumsum()
        
        # --- ENHANCEMENT: ADDING CONTEXT (START & END DATES) ---
        streak_counts = valid_absences.groupby(['Employee ID', 'Employee Name', 'streak_id']).agg(
            absence_start=('Date', 'min'),
            absence_end=('Date', 'max'),
            days_of_absence=('Date', 'size') # This is now the count of actual absent days
        ).reset_index()
        
        long_streaks = streak_counts[streak_counts['days_of_absence'] >= streak_threshold]
        
        if not long_streaks.empty:
            # --- ENHANCEMENT: RENAME COLUMNS FOR STAKEHOLDER CLARITY ---
            final_df = long_streaks.rename(columns={
                'days_of_absence': 'Consecutive Days',
                'absence_start': 'Absence Start Date',
                'absence_end': 'Absence End Date'
            })
            # Format dates for cleaner display
            final_df['Absence Start Date'] = final_df['Absence Start Date'].dt.strftime('%Y-%m-%d')
            final_df['Absence End Date'] = final_df['Absence End Date'].dt.strftime('%Y-%m-%d')
            
            return final_df[['Employee Name', 'Consecutive Days', 'Absence Start Date', 'Absence End Date']].sort_values('Consecutive Days', ascending=False)
            
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Insight Error in 'find_consecutive_absence_streaks': {e}")
        return pd.DataFrame()


def find_day_of_week_patterns(daily_df, employee_df, pattern_threshold_pct=40, significance_threshold=4):
    """
    Identifies employees with a high percentage of unplanned leaves on Mondays or Fridays,
    but only if they have a significant number of total leaves to constitute a real pattern.
    """
    try:
        leave_codes = {'CL', 'SL', 'LWP', 'ABSENT'}
        
        leave_days = daily_df[daily_df['Code'].isin(leave_codes)].copy()
        if leave_days.empty: return pd.DataFrame()
            
        leave_days['day_of_week'] = leave_days['Date'].dt.day_name()
        total_leaves = leave_days.groupby('Employee ID').size().reset_index(name='total_leaves')
        
        significant_leavers = total_leaves[total_leaves['total_leaves'] >= significance_threshold]
        if significant_leavers.empty: return pd.DataFrame()

        mondays_fridays = leave_days[leave_days['day_of_week'].isin(['Monday', 'Friday'])]
        if mondays_fridays.empty: return pd.DataFrame()

        pattern_counts = mondays_fridays.groupby(['Employee ID', 'day_of_week']).size().reset_index(name='pattern_days')
        
        merged_df = significant_leavers.merge(pattern_counts, on='Employee ID')
        merged_df['pattern_pct'] = (merged_df['pattern_days'] / merged_df['total_leaves'] * 100)
        
        significant_patterns = merged_df[merged_df['pattern_pct'] >= pattern_threshold_pct]

        if not significant_patterns.empty:
            patterns_with_names = significant_patterns.merge(employee_df[['Employee ID', 'Employee Name']], on='Employee ID', how='left')
            patterns_with_names['Description'] = patterns_with_names.apply(
                lambda row: f"{row['pattern_pct']:.0f}% of their {row['total_leaves']} leaves were on {row['day_of_week']}s", axis=1
            )
            
            sorted_patterns = patterns_with_names.sort_values('pattern_pct', ascending=False)
            return sorted_patterns[['Employee Name', 'Description']]
            
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Insight Error in 'find_day_of_week_patterns': {e}")
        return pd.DataFrame()