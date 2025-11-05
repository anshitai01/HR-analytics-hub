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
    # This correctly unpacks the tuple, getting the aggregated employee data.
    # The daily data is ignored here with '_' as it is not needed for this API response.
    aggregated_df, _ = analyzer.analyze_attendance(file_contents)
    
    # Step 2: Call the single, authoritative source for all business logic and calculations.
    # This replaces the old, duplicated _build_response_from_df function.
    analysis_results = logic.generate_attendance_summary(aggregated_df, "Overall")

    # Step 3: Pydantic validates the dictionary and returns the final JSON response.
    return AttendanceAnalysisResponse(**analysis_results)