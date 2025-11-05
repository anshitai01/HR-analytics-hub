# components/attendance/schemas.py
from pydantic import BaseModel, Field, Extra
from typing import List, Dict, Any

# --- This file is now fully aligned with the output of the new analyzer.py ---

class DataQualityReport(BaseModel):
    total_employees_processed: int
    employees_missing_manager_name: int
    employees_with_zero_workable_days: int

class CompanySummary(BaseModel):
    total_employees: int
    presence_rate: float
    leave_rate: float
    absenteeism_rate: float
    total_presence: float
    total_leave: float
    total_absenteeism: float
    total_workable: float
    total_extra_work_days: float
    leave_breakdown: Dict[str, float]

# This schema models a single row of our final aggregated DataFrame.
# It must match the columns exactly.
class EmployeeRecord(BaseModel):
    Employee_ID: str = Field(alias='Employee ID')
    Employee_Name: str = Field(alias='Employee Name')
    Reporting_Manager: str
    OU_Name: str = Field(alias='OU Name')
    Functional_Lead: str = Field(alias='Functional Lead')
    total_presence: float
    total_leave: float
    total_absenteeism: float
    total_workable_days: float
    worked_weekends: float
    worked_holidays: float
    # Use Extra.allow to dynamically accept all 'leave_*' columns
    class Config:
        extra = 'allow'
        anystr_strip_whitespace = True
        allow_population_by_field_name = True


class ManagerSummary(BaseModel):
    manager_name: str
    team_size: int
    presence_rate: float
    leave_rate: float
    absenteeism_rate: float
    team_members: List[EmployeeRecord]


class AttendanceAnalysisResponse(BaseModel):
    analysis_period: str
    data_quality_report: DataQualityReport
    company_summary: CompanySummary
    manager_summary: List[ManagerSummary]