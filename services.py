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


class ProviderConflictError(Exception):
    """Raised when a provider conflict is detected."""
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
    
    # Check for same patient + same medication on a previous day
    previous_submission = db.find_previous_submission(
        data.patient_mrn,
        data.medication_name
    )
    if previous_submission:
        warnings.append(
            f"Warning: This patient (MRN: {data.patient_mrn}) already has a care plan "
            f"for {data.medication_name} from a previous date."
        )
    
    return warnings


def check_blocking_provider_conflict(name: str, npi: str) -> None:
    """
    Check for provider conflicts that should block submission.
    Raises ProviderConflictError if conflict found.
    """
    # Check if provider name exists with a different NPI - this is blocked
    existing_by_name = db.find_provider_by_name(name)
    if existing_by_name and existing_by_name["npi"] != npi:
        raise ProviderConflictError(
            f"Provider '{name}' is already registered with NPI {existing_by_name['npi']}. "
            f"Cannot register same provider with different NPI ({npi})."
        )
    
    # Check if NPI exists with a different name - this is also blocked
    existing_by_npi = db.find_provider_by_npi(npi)
    if existing_by_npi and existing_by_npi["name"].lower() != name.lower():
        raise ProviderConflictError(
            f"NPI {npi} is already registered to provider '{existing_by_npi['name']}'. "
            f"Cannot register different provider name ('{name}') with same NPI."
        )


def check_blocking_duplicate(data: CarePlanRequest) -> None:
    """
    Check for exact duplicate submissions that should be blocked.
    Raises DuplicateSubmissionError if duplicate found.
    """
    existing = db.find_duplicate_submission(
        data.patient_first_name,
        data.patient_last_name,
        data.patient_mrn,
        data.medication_name
    )
    if existing:
        raise DuplicateSubmissionError(
            f"A care plan for {data.patient_first_name} {data.patient_last_name} "
            f"(MRN: {data.patient_mrn}) with medication {data.medication_name} "
            f"was already submitted today."
        )


def create_care_plan(data: CarePlanRequest) -> CarePlanResult:
    """
    Main business operation: Create a care plan.
    
    1. Block exact duplicates (same patient + medication + today)
    2. Block provider conflicts (same provider with different NPI)
    3. Check for potential duplicates and collect warnings
    4. Generate care plan via LLM
    5. Save provider and care plan to database
    6. Return result with warnings
    """
    # Block exact duplicates
    check_blocking_duplicate(data)
    
    # Block provider conflicts
    check_blocking_provider_conflict(data.referring_provider, data.referring_provider_npi)
    
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
