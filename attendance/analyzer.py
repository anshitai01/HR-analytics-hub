import pandas as pd
import numpy as np
import re
import logging
import io

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Constants for clarity and maintainability ---
# W* and H* are Presence codes, representing work done on a non-working day.
PRESENCE_CODES = {'P', 'AR', 'W*', 'H*'}
LEAVE_CODES = {'BL', 'CL', 'CO', 'EL', 'ELec', 'ML', 'PL', 'PRL', 'RH', 'SL'}
ABSENCE_CODES = {'LWP', 'ABSENT', 'A'}
# --- NEW: Define codes that are NOT part of an employee's workable days ---
# These represent scheduled non-working days where no work was performed.
SCHEDULED_NON_WORKING_CODES = {'H', 'W'}

# Codes that we want to break down for detailed analysis
LEAVE_BREAKDOWN_CODES = {'CL', 'SL', 'PRL', 'BL', 'ML', 'RH', 'ELec', 'CO'}

# --- Main Analysis Pipeline ---

def analyze_attendance(file_contents: bytes) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main orchestration function. Reads, cleans, processes, and aggregates the attendance data.
    
    Returns a tuple:
    1. The final employee-aggregated DataFrame.
    2. The intermediate daily metrics DataFrame, needed for time-series analysis.
    """
    logger.info("Starting full attendance analysis pipeline...")
    
    try:
        raw_df = pd.read_excel(io.BytesIO(file_contents), sheet_name=0)
    except Exception as e:
        logger.error(f"Failed to read Excel file. Error: {e}")
        raise ValueError(f"Failed to read data. The provided file might not be a valid Excel (.xlsx/.xls) file or is corrupted. Details: {str(e)}")

    long_df = _clean_and_melt_data(raw_df)
    if long_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    metrics_df = _calculate_metrics_from_long_data(long_df)

    aggregated_df = _aggregate_employee_data(metrics_df)
    
    logger.info(f"Analysis complete. Processed {len(aggregated_df)} unique employees.")
    
    return aggregated_df, metrics_df

# --- Helper Functions ---

def _clean_and_melt_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans, filters, and transforms raw data from wide to long format.
    Includes robust logic for column name matching and duplicate employee handling.
    """
    logger.info("Step 1: Cleaning and melting data...")

    CANONICAL_METADATA_COLS = {
        'Employee ID', 'Employee Name', 'Reporting_Manager', 
        'Email ID', 'OU Name', 'Functional Lead', 'Relieving_Date'
    }

    def normalize_col(name):
        return re.sub(r'\s+', ' ', str(name).strip().lower().replace('_', ' '))

    rename_map = {}
    normalized_target_map = {normalize_col(name): name for name in CANONICAL_METADATA_COLS}

    for col in df.columns:
        normalized_col = normalize_col(col)
        if normalized_col in normalized_target_map:
            canonical_name = normalized_target_map[normalized_col]
            if col != canonical_name:
                rename_map[col] = canonical_name
    
    df.rename(columns=rename_map, inplace=True)
    logger.info(f"Standardized column names. Mapped: {rename_map}")

    if 'Employee ID' not in df.columns:
        raise ValueError("The 'Employee ID' column was not found after standardizing column names. Please ensure the file contains a column representing the employee ID.")
        
    df.dropna(subset=['Employee ID'], inplace=True)
    df['Employee ID'] = df['Employee ID'].astype(str).str.strip()

    ids_to_exclude = ['123', 'fc', 'pc']
    df = df[~df['Employee ID'].str.lower().str.contains('|'.join(ids_to_exclude), na=False)]

    metadata_cols = list(CANONICAL_METADATA_COLS)
    
    date_pattern = re.compile(r'\d{1,2}-[A-Za-z]{3}-\d{2,4}')
    date_columns = [col for col in df.columns if date_pattern.match(str(col))]

    if not date_columns:
        logger.error("No valid date columns found. Aborting analysis.")
        raise ValueError(f"No valid date columns found (e.g., '1-Jan-26'). Found columns: {list(df.columns)[:10]}...")

    for col in ['OU Name', 'Functional Lead', 'Reporting_Manager', 'Relieving_Date']:
        if col not in df.columns:
            df[col] = pd.NaT if col == 'Relieving_Date' else 'N/A'
            logger.warning(f"CRITICAL: Column '{col}' was not found in the source file at all. Using placeholder.")

    for col in metadata_cols:
        if col not in df.columns:
            df[col] = pd.NaT if col == 'Relieving_Date' else 'N/A'
            
    df[['Employee ID', 'Employee Name', 'Reporting_Manager', 'OU Name', 'Functional Lead', 'Email ID']] = \
        df[['Employee ID', 'Employee Name', 'Reporting_Manager', 'OU Name', 'Functional Lead', 'Email ID']].fillna('N/A').astype(str)
    
    if 'Relieving_Date' in df.columns:
        df['Relieving_Date'] = pd.to_datetime(df['Relieving_Date'], errors='coerce')

    if df['Employee ID'].duplicated().any():
        logger.warning("Duplicate Employee IDs found. Consolidating rows...")
        grouping_keys = [key for key in ['Employee ID'] if key in df.columns]
        if grouping_keys:
            df = df.groupby(grouping_keys).first().reset_index()
        
    long_df = df.melt(
        id_vars=metadata_cols,
        value_vars=date_columns,
        var_name='Date',
        value_name='Code'
    )
    
    long_df.dropna(subset=['Code'], inplace=True)
    long_df['Code'] = long_df['Code'].astype(str).str.strip().str.upper()
    long_df['Date'] = pd.to_datetime(long_df['Date'], format='%d-%b-%y', errors='coerce')
    
    # --- ADDITION: Exclude non-working days from the main analysis data ---
    # This ensures they don't interfere with presence, leave, or absence counts.
    long_df = long_df[~long_df['Code'].isin(SCHEDULED_NON_WORKING_CODES)]

    logger.info(f"Successfully melted data into {len(long_df)} employee-day records.")
    return long_df

def _calculate_metrics_from_long_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates presence, leave, and absenteeism from the long-format DataFrame
    using efficient, fully vectorized operations.
    """
    logger.info("Step 2: Calculating metrics with vectorized operations...")
    
    # Initialize all metric columns to 0.0 for float precision
    df['presence'] = 0.0
    df['leave'] = 0.0
    df['lwp'] = 0.0
    df['absent'] = 0.0
    df['worked_weekends'] = 0.0
    df['worked_holidays'] = 0.0
    
    for code in LEAVE_BREAKDOWN_CODES:
        df[f'leave_{code.lower()}'] = 0.0

    # Vectorized Logic for Split Days (e.g., "CL/SL")
    is_split = df['Code'].str.contains('/', na=False)
    split_codes = df.loc[is_split, 'Code'].str.split('/', n=1, expand=True)
    
    if not split_codes.empty:
        code1 = split_codes[0].str.strip()
        code2 = split_codes[1].str.strip()

        # Assign 0.5 for each part of the split day
        df.loc[is_split, 'presence'] = (code1.isin(PRESENCE_CODES) * 0.5) + (code2.isin(PRESENCE_CODES) * 0.5)
        df.loc[is_split, 'leave'] = (code1.isin(LEAVE_CODES) * 0.5) + (code2.isin(LEAVE_CODES) * 0.5)
        df.loc[is_split, 'lwp'] = (code1.eq('LWP') * 0.5) + (code2.eq('LWP') * 0.5)
        df.loc[is_split, 'absent'] = (code1.eq('ABSENT') * 0.5) + (code2.eq('ABSENT') * 0.5)
        df.loc[is_split, 'worked_weekends'] = (code1.eq('W*') * 0.5) + (code2.eq('W*') * 0.5)
        df.loc[is_split, 'worked_holidays'] = (code1.eq('H*') * 0.5) + (code2.eq('H*') * 0.5)

        for code in LEAVE_BREAKDOWN_CODES:
            df.loc[is_split, f'leave_{code.lower()}'] = (code1.eq(code) * 0.5) + (code2.eq(code) * 0.5)
            
    # Vectorized Logic for Full Days
    full_day_mask = ~is_split
    code_full = df.loc[full_day_mask, 'Code']
    
    df.loc[full_day_mask, 'presence'] = code_full.isin(PRESENCE_CODES).astype(float)
    df.loc[full_day_mask, 'leave'] = code_full.isin(LEAVE_CODES).astype(float)
    df.loc[full_day_mask, 'lwp'] = code_full.eq('LWP').astype(float)
    df.loc[full_day_mask, 'absent'] = code_full.eq('ABSENT').astype(float)
    df.loc[full_day_mask, 'worked_weekends'] = code_full.eq('W*').astype(float)
    df.loc[full_day_mask, 'worked_holidays'] = code_full.eq('H*').astype(float)

    for code in LEAVE_BREAKDOWN_CODES:
        df.loc[full_day_mask, f'leave_{code.lower()}'] = code_full.eq(code).astype(float)
        
    return df

def _aggregate_employee_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates the daily metrics to a final, per-employee summary DataFrame.
    """
    logger.info("Step 3: Aggregating data and engineering new metrics...")

    grouping_cols = [col for col in ['Employee ID', 'Employee Name', 'Reporting_Manager', 'OU Name', 'Functional Lead'] if col in df.columns]
    
    agg_cols_to_sum = ['presence', 'leave', 'lwp', 'absent', 'worked_weekends', 'worked_holidays'] + \
                      [f'leave_{code.lower()}' for code in LEAVE_BREAKDOWN_CODES]

    agg_dict = {col: 'sum' for col in agg_cols_to_sum}
    if 'Relieving_Date' in df.columns:
        agg_dict['Relieving_Date'] = 'first' 
        
    aggregated_df = df.groupby(grouping_cols, as_index=False).agg(agg_dict)
    
    # --- Engineer Final HR-defined Metrics ---
    # Existing metrics (unchanged)
    aggregated_df['total_absenteeism'] = aggregated_df['lwp'] + aggregated_df['absent']
    aggregated_df['total_workable_days'] = (
        aggregated_df['presence'] + 
        aggregated_df['leave'] + 
        aggregated_df['total_absenteeism']
    )
    
    # --- START OF NEW METRIC ENGINEERING ---
    # 1. Rename 'total_workable_days' to 'mandays' to align with HR terminology.
    #    Based on the HR table, Mandays = Present + Leave + LWP, which is our total_workable_days.
    aggregated_df.rename(columns={'total_workable_days': 'mandays'}, inplace=True)

    # 2. Calculate the new "% Deployment" metric.
    #    Formula: (Total Presence Days / Mandays) * 100
    aggregated_df['deployment_percentage'] = (
        (aggregated_df['presence'] / aggregated_df['mandays']) * 100
    ).where(aggregated_df['mandays'] > 0, 0).round(2)
    # --- END OF NEW METRIC ENGINEERING ---
    
    # Rename other columns for clarity in the final output
    aggregated_df.rename(columns={
        'presence': 'total_presence',
        'leave': 'total_leave',
    }, inplace=True)
    
    return aggregated_df
