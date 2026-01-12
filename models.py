from typing import List
from pydantic import BaseModel, Field, field_validator
import re


class CarePlanRequest(BaseModel):
    patient_first_name: str = Field(..., min_length=1)
    patient_last_name: str = Field(..., min_length=1)
    referring_provider: str = Field(..., min_length=1)
    referring_provider_npi: str = Field(..., min_length=10, max_length=10)
    patient_mrn: str = Field(..., min_length=6, max_length=6)
    primary_diagnosis: str = Field(..., min_length=1)  # ICD-10 code
    medication_name: str = Field(..., min_length=1)
    additional_diagnoses: str = ""  # Comma-separated ICD-10 codes
    medication_history: str = ""  # Comma-separated list
    patient_records: str = ""

    @field_validator("referring_provider_npi")
    @classmethod
    def validate_npi(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("NPI must contain only digits")
        if len(v) != 10:
            raise ValueError("NPI must be exactly 10 digits")
        return v

    @field_validator("patient_mrn")
    @classmethod
    def validate_mrn(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("MRN must contain only digits")
        if len(v) != 6:
            raise ValueError("MRN must be exactly 6 digits")
        return v

    @field_validator("primary_diagnosis")
    @classmethod
    def validate_primary_diagnosis(cls, v: str) -> str:
        # Basic ICD-10 format: letter followed by digits, optional decimal
        pattern = r"^[A-Z]\d{2}(\.\d{1,4})?$"
        if not re.match(pattern, v.upper()):
            raise ValueError("Primary diagnosis must be a valid ICD-10 code (e.g., E11.9)")
        return v.upper()


class CarePlanResponse(BaseModel):
    id: int
    warnings: List[str] = []
    generated_plan: str
