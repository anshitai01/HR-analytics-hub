# components/attendance/exporter.py

import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

def create_excel_report(analysis_summary: dict, detailed_df: pd.DataFrame) -> bytes:
    """
    Generates a multi-sheet, professional Excel report in memory with detailed calculation breakdowns.
    This version is aligned with the new, refactored analyzer output.
    """
    logger.info(f"Generating detailed Excel report for {len(detailed_df)} employees...")
    output_buffer = io.BytesIO()
    
    company_summary = analysis_summary.get('company_summary', {})

    with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
        
        # --- Sheet 1: High-Level Summary ---
        summary_data = {
            "Metric": [
                "Total Employees in View",
                "Overall Presence %",
                "Overall Leave %",
                "Overall Absenteeism %",
                "Total Presence Days",
                "Total Leave Days",
                "Total Absenteeism Days",
                "Total Workable Days (Denominator)",
                "Total Weekend/Holiday Work Days" # New metric
            ],
            "Value": [
                company_summary.get("total_employees"),
                f"{company_summary.get('presence_rate', 0):.2f}%",
                f"{company_summary.get('leave_rate', 0):.2f}%",
                f"{company_summary.get('absenteeism_rate', 0):.2f}%",
                company_summary.get("total_presence"),
                company_summary.get("total_leave"),
                company_summary.get("total_absenteeism"),
                company_summary.get("total_workable"),
                company_summary.get("total_extra_work_days")
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        

        # --- Sheet 2: Detailed Employee Data (The "Proof" Sheet) ---
        export_df = detailed_df.copy()
        
        # Engineer the new, user-facing columns for clarity
        export_df['presence_percentage'] = (
            # CHANGED: Using new column names
            export_df['total_presence'] / export_df['total_workable_days'] * 100
        ).where(export_df['total_workable_days'] > 0, 0).round(2)
        
        export_df['absenteeism_percentage'] = (
            # CHANGED: Using new column names
            export_df['total_absenteeism'] / export_df['total_workable_days'] * 100
        ).where(export_df['total_workable_days'] > 0, 0).round(2)

        # *** The "Show Your Work" Column ***
        export_df['calculation_breakdown'] = export_df.apply(
            # CHANGED: Using new column names
            lambda row: f"{row['total_presence']} (Present) + {row['total_leave']} (Leave) + {row['total_absenteeism']} (Absent) = {row['total_workable_days']} Workable Days",
            axis=1
        )
        
        # Rename columns for a clean, professional-looking export
        export_df.rename(columns={
            # CHANGED: Using new column names from analyzer
            'total_presence': 'presence_days',
            'total_leave': 'leave_days',
            'total_absenteeism': 'absenteeism_days',
            'total_workable_days': 'total_workable_days',
            'Employee ID': 'Employee_ID',
            'Employee Name': 'Employee_Name',
            'Reporting_Manager': 'Reporting_Manager',
            'Functional Lead': 'Functional_Lead',
            'OU Name': 'OU_Name'
        }, inplace=True)
        
        # Reorder columns for a logical flow in the final report
        final_columns = [
            'Employee_ID', 'Employee_Name', 'OU_Name', 'Functional_Lead', 'Reporting_Manager', 
            'presence_days', 'leave_days', 'absenteeism_days', 
            'total_workable_days', 'presence_percentage', 'absenteeism_percentage',
            'worked_weekends', 'worked_holidays', # ADDED: New valuable metrics
            'calculation_breakdown'
        ]
        # Include leave breakdown columns if they exist
        leave_cols = sorted([col for col in export_df.columns if col.startswith('leave_')])
        
        # Filter for only existing columns to prevent errors if a column is missing
        final_columns_exist = [col for col in final_columns if col in export_df.columns]
        leave_cols_exist = [col for col in leave_cols if col in export_df.columns]
        
        export_df = export_df[final_columns_exist + leave_cols_exist]
        export_df.to_excel(writer, sheet_name='Detailed Employee Data', index=False)
        
        # Auto-adjust column widths for readability
        for sheet_name in writer.sheets:
            sheet = writer.sheets[sheet_name]
            for col in sheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            cell_len = len(str(cell.value))
                            if cell.font and cell.font.bold: cell_len += 2
                            if cell_len > max_length: max_length = cell_len
                    except: pass
                adjusted_width = (max_length + 2)
                sheet.column_dimensions[column].width = adjusted_width

    logger.info("Excel report generated successfully in memory.")
    excel_bytes = output_buffer.getvalue()
    return excel_bytes