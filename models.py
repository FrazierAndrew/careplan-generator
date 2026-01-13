from typing import List
from pydantic import BaseModel, Field, field_validator
import re

# ICD-10 pattern: letter followed by 2 digits, optional decimal with 1-4 digits
ICD10_PATTERN = r"^[A-Z]\d{2}(\.\d{1,4})?$"


def is_valid_icd10(code: str) -> bool:
    """Check if a string is a valid ICD-10 code."""
    return bool(re.match(ICD10_PATTERN, code.upper()))


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
        if not is_valid_icd10(v):
            raise ValueError("Primary diagnosis must be a valid ICD-10 code (e.g., E11.9)")
        return v.upper()

    @field_validator("additional_diagnoses")
    @classmethod
    def validate_additional_diagnoses(cls, v: str) -> str:
        if not v or not v.strip():
            return ""
        codes = [c.strip() for c in v.split(",") if c.strip()]
        invalid = [c for c in codes if not is_valid_icd10(c)]
        if invalid:
            raise ValueError(f"Invalid ICD-10 code(s): {', '.join(invalid)}")
        return ", ".join(c.upper() for c in codes)


class CarePlanResponse(BaseModel):
    id: int
    warnings: List[str] = []
    generated_plan: str
