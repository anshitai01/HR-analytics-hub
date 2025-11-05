# components/exit_analysis/router.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd

# Import our custom modules for this component
from . import analyzer
from . import logic
from . import schemas

# Create a router for this component
router = APIRouter(
    prefix="/analyze/exit",
    tags=["Exit Analysis"]
)

@router.post("/", response_model=schemas.ExitAnalysisResponse)
async def analyze_exit_data_endpoint(file: UploadFile = File(...)):
    """
    Analyzes the uploaded employee exit survey file.
    
    This endpoint orchestrates the full pipeline:
    1. Reads and cleans the raw data using the analyzer.
    2. Generates sentiment and themes using the logic module.
    3. Structures the final output according to the Pydantic schemas.
    """
    file_contents = await file.read()
    
    # Step 1: Call the analyzer to process the raw file into a clean DataFrame.
    processed_df = analyzer.process_exit_data(file_contents)
    
    if processed_df.empty:
        raise HTTPException(status_code=400, detail="Failed to process the uploaded file. It might be empty or in an incorrect format.")

    # Step 2: Call the logic module to generate AI-powered insights.
    analysis_results = logic.generate_exit_insights(processed_df)

    # Step 3: Transform the results to match our defined response schema.
    # This ensures our API response is always consistent.
    
    # Transform the themes dictionary into a list of Theme objects
    themes_list = [
        schemas.Theme(theme_name=name, keywords=words)
        for name, words in analysis_results.get("themes", {}).items()
    ]
    
    # The processed_data is already a list of dictionaries, ready for validation.
    employee_data_list = analysis_results.get("processed_data", [])

    # Step 4: Return the final, structured response.
    # FastAPI will automatically validate this against ExitAnalysisResponse.
    return schemas.ExitAnalysisResponse(
        themes=themes_list,
        employee_data=employee_data_list
    )