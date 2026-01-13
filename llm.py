import os
from openai import OpenAI
from models import CarePlanRequest


class CarePlanGenerationError(Exception):
    """Raised when care plan generation fails."""
    pass


def generate_care_plan(data: CarePlanRequest) -> str:
    """Generate a care plan using OpenAI. Raises CarePlanGenerationError on failure."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise CarePlanGenerationError(
            "Care plan generation is not configured. Please contact support."
        )
    
    client = OpenAI(api_key=api_key)
    
    # Format lists for display
    additional_dx = ", ".join(data.additional_diagnoses) if data.additional_diagnoses else "None"
    med_history = ", ".join(data.medication_history) if data.medication_history else "None"
    
    prompt = f"""Generate a clinical care plan for the following patient:

Patient: {data.patient_first_name} {data.patient_last_name}
MRN: {data.patient_mrn}
Referring Provider: {data.referring_provider} (NPI: {data.referring_provider_npi})
Primary Diagnosis (ICD-10): {data.primary_diagnosis}
Medication: {data.medication_name}
Additional Diagnoses: {additional_dx}
Medication History: {med_history}

Patient Records:
{data.patient_records or 'No additional records provided'}

Please generate a care plan with ONLY the following four sections:

1. Problem List / Drug Therapy Problems (DTPs)
2. Goals (SMART)
3. Pharmacist Interventions / Plan
4. Monitoring Plan & Lab Schedule
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a clinical pharmacist assistant helping to generate care plans for specialty pharmacy patients."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception:
        # Don't expose internal error details to users
        raise CarePlanGenerationError(
            "Failed to generate care plan. Please try again or contact support."
        )
