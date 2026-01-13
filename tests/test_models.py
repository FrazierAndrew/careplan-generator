"""Unit tests for Pydantic validation models."""
import pytest
from pydantic import ValidationError
from models import CarePlanRequest, is_valid_icd10


class TestICD10Validation:
    """Tests for ICD-10 code validation."""

    def test_valid_icd10_codes(self):
        assert is_valid_icd10("E11.9") is True
        assert is_valid_icd10("J45.20") is True
        assert is_valid_icd10("I10") is True
        assert is_valid_icd10("A00.0") is True

    def test_invalid_icd10_codes(self):
        assert is_valid_icd10("INVALID") is False
        assert is_valid_icd10("123") is False
        assert is_valid_icd10("E1") is False
        assert is_valid_icd10("") is False


class TestCarePlanRequest:
    """Tests for CarePlanRequest validation."""

    @pytest.fixture
    def valid_data(self):
        return {
            "patient_first_name": "John",
            "patient_last_name": "Doe",
            "referring_provider": "Dr. Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "123456",
            "primary_diagnosis": "E11.9",
            "medication_name": "Humira",
        }

    def test_valid_request(self, valid_data):
        request = CarePlanRequest(**valid_data)
        assert request.patient_first_name == "John"
        assert request.primary_diagnosis == "E11.9"

    # NPI validation
    def test_npi_must_be_10_digits(self, valid_data):
        valid_data["referring_provider_npi"] = "123"
        with pytest.raises(ValidationError) as exc:
            CarePlanRequest(**valid_data)
        assert "10" in str(exc.value)

    def test_npi_must_be_digits_only(self, valid_data):
        valid_data["referring_provider_npi"] = "123456789A"
        with pytest.raises(ValidationError) as exc:
            CarePlanRequest(**valid_data)
        assert "digits" in str(exc.value)

    # MRN validation
    def test_mrn_must_be_6_digits(self, valid_data):
        valid_data["patient_mrn"] = "123"
        with pytest.raises(ValidationError) as exc:
            CarePlanRequest(**valid_data)
        assert "6" in str(exc.value)

    def test_mrn_must_be_digits_only(self, valid_data):
        valid_data["patient_mrn"] = "12345A"
        with pytest.raises(ValidationError) as exc:
            CarePlanRequest(**valid_data)
        assert "digits" in str(exc.value)

    # Primary diagnosis validation
    def test_primary_diagnosis_must_be_valid_icd10(self, valid_data):
        valid_data["primary_diagnosis"] = "INVALID"
        with pytest.raises(ValidationError) as exc:
            CarePlanRequest(**valid_data)
        assert "ICD-10" in str(exc.value)

    def test_primary_diagnosis_normalized_to_uppercase(self, valid_data):
        valid_data["primary_diagnosis"] = "e11.9"
        request = CarePlanRequest(**valid_data)
        assert request.primary_diagnosis == "E11.9"

    # Additional diagnoses validation
    def test_additional_diagnoses_valid(self, valid_data):
        valid_data["additional_diagnoses"] = "I10, E78.5"
        request = CarePlanRequest(**valid_data)
        assert request.additional_diagnoses == "I10, E78.5"

    def test_additional_diagnoses_invalid_code(self, valid_data):
        valid_data["additional_diagnoses"] = "I10, INVALID, E78.5"
        with pytest.raises(ValidationError) as exc:
            CarePlanRequest(**valid_data)
        assert "INVALID" in str(exc.value)

    def test_additional_diagnoses_empty_allowed(self, valid_data):
        valid_data["additional_diagnoses"] = ""
        request = CarePlanRequest(**valid_data)
        assert request.additional_diagnoses == ""
