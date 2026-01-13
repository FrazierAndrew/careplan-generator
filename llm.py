import os
from openai import OpenAI
from models import CarePlanRequest


def generate_care_plan(data: CarePlanRequest) -> str:
    """Generate a care plan using OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[ERROR: OPENAI_API_KEY not set - care plan generation skipped]"
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Generate a clinical care plan for the following patient:

Patient: {data.patient_first_name} {data.patient_last_name}
MRN: {data.patient_mrn}
Referring Provider: {data.referring_provider} (NPI: {data.referring_provider_npi})
Primary Diagnosis (ICD-10): {data.primary_diagnosis}
Medication: {data.medication_name}
Additional Diagnoses: {data.additional_diagnoses or 'None'}
Medication History: {data.medication_history or 'None'}

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
    except Exception as e:
        return f"[ERROR generating care plan: {str(e)}]"
