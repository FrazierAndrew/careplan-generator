"""
Transport layer - HTTP routes only.
Handles request/response, delegates to services for business logic.
"""
import csv
import io
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from database import init_db, get_all_care_plans
from models import CarePlanRequest
from services import create_care_plan, DuplicateSubmissionError, ProviderConflictError
from pdf_utils import extract_text_from_pdf

app = FastAPI(title="Care Plan Generator")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the care plan input form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit")
async def submit_care_plan(
    patient_first_name: str = Form(...),
    patient_last_name: str = Form(...),
    referring_provider: str = Form(...),
    referring_provider_npi: str = Form(...),
    patient_mrn: str = Form(...),
    primary_diagnosis: str = Form(...),
    medication_name: str = Form(...),
    additional_diagnoses: str = Form(""),
    medication_history: str = Form(""),
    patient_records: str = Form(""),
    patient_records_file: UploadFile | None = File(None),
):
    """
    Submit a new care plan request.
    Validates input, generates care plan via LLM, and saves to database.
    Accepts optional PDF file upload for patient records.
    """
    # Combine text input with PDF content if provided
    combined_records = patient_records
    if patient_records_file and patient_records_file.filename:
        if not patient_records_file.filename.lower().endswith(".pdf"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "errors": ["Only PDF files are supported for patient records upload"]}
            )
        try:
            file_bytes = await patient_records_file.read()
            pdf_text = extract_text_from_pdf(file_bytes)
            if combined_records:
                combined_records = f"{combined_records}\n\n--- Extracted from PDF ---\n\n{pdf_text}"
            else:
                combined_records = pdf_text
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"success": False, "errors": [str(e)]}
            )
    
    # Validate input
    try:
        data = CarePlanRequest(
            patient_first_name=patient_first_name,
            patient_last_name=patient_last_name,
            referring_provider=referring_provider,
            referring_provider_npi=referring_provider_npi,
            patient_mrn=patient_mrn,
            primary_diagnosis=primary_diagnosis,
            medication_name=medication_name,
            additional_diagnoses=additional_diagnoses,
            medication_history=medication_history,
            patient_records=combined_records,
        )
    except ValidationError as e:
        errors = [err["msg"] for err in e.errors()]
        return JSONResponse(
            status_code=400,
            content={"success": False, "errors": errors}
        )
    
    # Create care plan (business logic)
    try:
        result = create_care_plan(data)
    except DuplicateSubmissionError as e:
        return JSONResponse(
            status_code=409,
            content={"success": False, "errors": [str(e)]}
        )
    except ProviderConflictError as e:
        return JSONResponse(
            status_code=409,
            content={"success": False, "errors": [str(e)]}
        )
    
    return JSONResponse(content={
        "success": True,
        "id": result.id,
        "warnings": result.warnings,
        "generated_plan": result.generated_plan
    })


@app.get("/export")
async def export_care_plans():
    """Export all care plans as CSV for pharma reporting."""
    care_plans = get_all_care_plans()
    
    if not care_plans:
        return JSONResponse(content={"error": "No care plans to export"}, status_code=404)
    
    # Create CSV in memory - include all fields
    output = io.StringIO()
    fieldnames = [
        "id", "patient_first_name", "patient_last_name", "patient_mrn",
        "referring_provider", "referring_provider_npi", "primary_diagnosis",
        "medication_name", "additional_diagnoses", "medication_history",
        "patient_records", "generated_plan", "created_at"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(care_plans)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=care_plans_export.csv"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
