# components/attendance/router.py

from fastapi import APIRouter, UploadFile, File

# Import the Pydantic model for response validation.
from .schemas import AttendanceAnalysisResponse

# Import our backend modules:
# - analyzer: Handles the raw data processing from the Excel file.
# - logic: Contains the centralized business logic for KPI calculations.
from . import analyzer, logic

router = APIRouter(
    prefix="/analyze/attendance",
    tags=["Attendance Analysis"]
)

@router.post("/", response_model=AttendanceAnalysisResponse)
async def analyze_attendance_endpoint(file: UploadFile = File(...)):
    """
    Analyzes the uploaded HR attendance Excel file and returns a structured JSON response.
    
    This endpoint orchestrates the analysis pipeline:
    1. Reads the uploaded file into memory.
    2. Calls the core analyzer to process the data into structured DataFrames.
    3. Calls the centralized logic module to calculate all KPIs and summaries.
    4. Validates the final result against the response model and returns it.
    """
    file_contents = await file.read()
    
    # Step 1: Call the core analysis engine.
    # CHANGE: We now unpack 'daily_df' (the second return value) instead of ignoring it.
    # This allows us to pass the calendar data to the logic module.
    aggregated_df, daily_df = analyzer.analyze_attendance(file_contents)
    
    # Step 2: Call the single, authoritative source for all business logic and calculations.
    # CHANGE: We pass 'daily_df' to the function so it can calculate period lengths.
    # We also unpack the result: 'analysis_results' is the summary dict, '_' is the baseline dict (not needed for API).
    analysis_results, _ = logic.generate_attendance_summary(aggregated_df, "Overall", daily_df=daily_df)

    # Step 3: Pydantic validates the dictionary and returns the final JSON response.
    return AttendanceAnalysisResponse(**analysis_results)