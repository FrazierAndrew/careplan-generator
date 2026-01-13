"""
Business logic layer - Orchestrates operations and enforces business rules.
"""
from typing import List
from dataclasses import dataclass

from models import CarePlanRequest
from llm import generate_care_plan
import database as db


class DuplicateSubmissionError(Exception):
    """Raised when a duplicate submission is detected."""
    pass


@dataclass
class CarePlanResult:
    """Result of creating a care plan."""
    id: int
    warnings: List[str]
    generated_plan: str


def check_duplicate_warnings(data: CarePlanRequest) -> List[str]:
    """
    Check for potential duplicates and return warning messages.
    Does not block submission - just warns the user.
    """
    warnings = []
    
    # Check for duplicate patient by MRN
    existing_by_mrn = db.find_care_plan_by_mrn(data.patient_mrn)
    if existing_by_mrn:
        warnings.append(
            f"Warning: Patient with MRN {data.patient_mrn} already exists in the system."
        )
    else:
        # Only check by name if MRN didn't match (avoid double warning)
        existing_by_name = db.find_care_plan_by_patient_name(
            data.patient_first_name, 
            data.patient_last_name
        )
        if existing_by_name:
            warnings.append(
                f"Warning: Patient with name {data.patient_first_name} {data.patient_last_name} may already exist."
            )
    
    # Check for duplicate order
    existing_order = db.find_care_plan_by_order(
        data.patient_mrn,
        data.medication_name,
        data.primary_diagnosis
    )
    if existing_order:
        warnings.append(
            f"Warning: An order for {data.medication_name} with diagnosis "
            f"{data.primary_diagnosis} already exists for this patient."
        )
    
    # Check for provider conflicts
    provider_warnings = check_provider_conflicts(
        data.referring_provider,
        data.referring_provider_npi
    )
    warnings.extend(provider_warnings)
    
    return warnings


def check_provider_conflicts(name: str, npi: str) -> List[str]:
    """
    Check for provider data conflicts.
    Returns warnings if the same provider appears with different NPIs,
    or the same NPI appears with different provider names.
    """
    warnings = []
    
    # Check if NPI exists with a different name
    existing_by_npi = db.find_provider_by_npi(npi)
    if existing_by_npi and existing_by_npi["name"].lower() != name.lower():
        warnings.append(
            f"Warning: NPI {npi} is already registered to provider "
            f"'{existing_by_npi['name']}'."
        )
    
    # Check if name exists with a different NPI
    existing_by_name = db.find_provider_by_name(name)
    if existing_by_name and existing_by_name["npi"] != npi:
        warnings.append(
            f"Warning: Provider '{name}' is already registered with a different "
            f"NPI ({existing_by_name['npi']})."
        )
    
    return warnings


def check_blocking_duplicate(data: CarePlanRequest) -> None:
    """
    Check for exact duplicate submissions that should be blocked.
    Raises DuplicateSubmissionError if duplicate found.
    """
    existing = db.find_duplicate_submission(
        data.patient_first_name,
        data.patient_last_name,
        data.medication_name
    )
    if existing:
        raise DuplicateSubmissionError(
            f"A care plan for {data.patient_first_name} {data.patient_last_name} "
            f"with medication {data.medication_name} was already submitted today."
        )


def create_care_plan(data: CarePlanRequest) -> CarePlanResult:
    """
    Main business operation: Create a care plan.
    
    1. Block exact duplicates (same patient + medication + today)
    2. Check for potential duplicates and collect warnings
    3. Generate care plan via LLM
    4. Save provider and care plan to database
    5. Return result with warnings
    """
    # Block exact duplicates
    check_blocking_duplicate(data)
    
    # Collect warnings (does not block)
    warnings = check_duplicate_warnings(data)
    
    # Generate care plan
    generated_plan = generate_care_plan(data)
    
    # Persist data
    db.insert_provider(data.referring_provider, data.referring_provider_npi)
    care_plan_id = db.insert_care_plan(data.model_dump(), generated_plan)
    
    return CarePlanResult(
        id=care_plan_id,
        warnings=warnings,
        generated_plan=generated_plan
    )
