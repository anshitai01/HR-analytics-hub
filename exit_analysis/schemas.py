# components/exit_analysis/schemas.py

from pydantic import BaseModel, Extra
from typing import List, Dict, Any

# --- Pydantic Models for API Data Structure ---

class Theme(BaseModel):
    """Represents a single discovered theme."""
    theme_name: str
    keywords: List[str]

class EmployeeExitRecord(BaseModel):
    """
    Represents the consolidated data for a single employee.
    Includes demographics, exit details, and our calculated sentiment.
    """
    # Key identifier fields from the raw data
    dateofjoining: str
    dob: str
    gender: str
    designation: str
    resignationletterdate: str
    actualrelievingdate: str
    separationtype: str
    resignationreason: str
    
    # Insights we generated
    sentiment: str

    # Allow any other columns that came from the pivot (i.e., the questions)
    class Config:
        extra = 'allow'


class ExitAnalysisResponse(BaseModel):
    """The main response model for the entire exit analysis endpoint."""
    themes: List[Theme]
    employee_data: List[EmployeeExitRecord]