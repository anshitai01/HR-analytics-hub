# components/exit_analysis/analyzer.py

import pandas as pd
import re
import logging
import io

# --- Setup logging for traceability ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Main Analysis Pipeline ---

def process_exit_data(file_contents: bytes) -> pd.DataFrame:
    """
    Main orchestration function. Reads, cleans, and pivots the exit interview data.
    
    Args:
        file_contents: The raw bytes of the uploaded Excel file.

    Returns:
        A cleaned Pandas DataFrame where each row represents one employee's
        consolidated exit feedback.
    """
    logger.info("Starting exit data processing pipeline...")
    
    try:
        # --- THE FINAL FIX ---
        # By removing the 'engine' argument, pandas will now automatically use
        # 'xlrd' for .xls files and 'openpyxl' for .xlsx files.
        # This makes our component robust to both formats.
        raw_df = pd.read_excel(io.BytesIO(file_contents))
        logger.info(f"Successfully read Excel file. Found {len(raw_df)} total rows.")
    except Exception as e:
        logger.error(f"Failed to read data file. It must be a valid Excel (.xlsx, .xls) file. Error: {e}")
        return pd.DataFrame()

    if raw_df.empty:
        return pd.DataFrame()

    pivoted_df = _pivot_and_consolidate(raw_df)
    
    logger.info(f"Processing complete. Consolidated data for {len(pivoted_df)} unique employees.")
    
    return pivoted_df


# --- Helper Functions ---

def _pivot_and_consolidate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the long-format exit data (one row per question) into a wide-format
    DataFrame (one row per employee).
    """
    logger.info("Step 1: Pivoting data to consolidate rows per employee...")

    identifier_cols = [
        'DATEOFJOINING', 'DOB', 'GENDER', 'DESIGNATION', 
        'RESIGNATIONLETTERDATE', 'ACTUALRELIEVINGDATE', 'SEPARATIONTYPE', 
        'RESIGNATIONREASON'
    ]
    
    missing_cols = [col for col in identifier_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Source file is missing required identifier columns: {missing_cols}. Aborting.")
        return pd.DataFrame()

    pivot_index = identifier_cols
    pivot_columns = 'QUESTION_DESC'
    pivot_values = 'CHOICE_OR_COMMENTS'

    try:
        pivoted = df.pivot_table(
            index=pivot_index,
            columns=pivot_columns,
            values=pivot_values,
            aggfunc='first'
        ).reset_index()
        
        pivoted.columns = [re.sub(r'[^0-9a-zA-Z_]', '', str(col).replace(' ', '_')).lower() for col in pivoted.columns]
        
        logger.info("Successfully pivoted data.")
        return pivoted

    except Exception as e:
        logger.error(f"Failed during the pivot operation. Check data format. Error: {e}")
        return pd.DataFrame()