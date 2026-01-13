"""Integration tests using FastAPI TestClient."""
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

# Set up test database before importing app
os.environ.setdefault("DATABASE_PATH", "test_careplan.db")

from main import app
from database import init_db, DATABASE_PATH


@pytest.fixture(scope="module")
def client():
    """Create test client with fresh database and mocked LLM."""
    # Remove test db if exists
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    init_db()
    
    # Mock the LLM to avoid needing real API key in tests
    with patch("services.generate_care_plan", return_value="[Test Generated Care Plan]"):
        with TestClient(app) as c:
            yield c
    
    # Cleanup
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()


class TestAPI:
    """Integration tests for the API endpoints."""

    def test_home_page_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Care Plan" in response.text

    def test_submit_valid_care_plan(self, client):
        response = client.post("/submit", data={
            "patient_first_name": "Test",
            "patient_last_name": "Patient",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "111111",
            "primary_diagnosis": "E11.9",
            "medication_name": "TestMed",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data
        assert "generated_plan" in data

    def test_submit_invalid_npi_fails(self, client):
        response = client.post("/submit", data={
            "patient_first_name": "Test",
            "patient_last_name": "Patient",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "123",  # Invalid
            "patient_mrn": "222222",
            "primary_diagnosis": "E11.9",
            "medication_name": "TestMed",
        })
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_submit_invalid_icd10_fails(self, client):
        response = client.post("/submit", data={
            "patient_first_name": "Test",
            "patient_last_name": "Patient",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "333333",
            "primary_diagnosis": "INVALID",  # Invalid
            "medication_name": "TestMed",
        })
        assert response.status_code == 400

    def test_duplicate_mrn_returns_warning(self, client):
        # First submission
        client.post("/submit", data={
            "patient_first_name": "First",
            "patient_last_name": "Patient",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "444444",
            "primary_diagnosis": "E11.9",
            "medication_name": "Med1",
        })
        
        # Second submission with same MRN
        response = client.post("/submit", data={
            "patient_first_name": "Second",
            "patient_last_name": "Patient",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "444444",  # Same MRN
            "primary_diagnosis": "J45.20",
            "medication_name": "Med2",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["warnings"]) > 0
        assert "MRN" in data["warnings"][0]

    def test_export_returns_csv(self, client):
        response = client.get("/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "patient_first_name" in response.text

    def test_exact_duplicate_same_day_blocked(self, client):
        # First submission
        response1 = client.post("/submit", data={
            "patient_first_name": "Duplicate",
            "patient_last_name": "Test",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "555555",
            "primary_diagnosis": "E11.9",
            "medication_name": "SameMed",
        })
        assert response1.status_code == 200
        
        # Exact same submission (same name + medication + same day) should be blocked
        response2 = client.post("/submit", data={
            "patient_first_name": "Duplicate",
            "patient_last_name": "Test",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "555555",
            "primary_diagnosis": "E11.9",
            "medication_name": "SameMed",  # Same medication
        })
        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False
        assert "already submitted today" in data["errors"][0]
