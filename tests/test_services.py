"""Unit tests for business logic in services."""
import pytest
from unittest.mock import patch, MagicMock
from models import CarePlanRequest
from services import check_duplicate_warnings, check_provider_conflicts


@pytest.fixture
def sample_request():
    return CarePlanRequest(
        patient_first_name="John",
        patient_last_name="Doe",
        referring_provider="Dr. Smith",
        referring_provider_npi="1234567890",
        patient_mrn="123456",
        primary_diagnosis="E11.9",
        medication_name="Humira",
    )


class TestDuplicateWarnings:
    """Tests for duplicate detection logic."""

    @patch("services.db")
    def test_no_duplicates_returns_empty(self, mock_db, sample_request):
        mock_db.find_care_plan_by_mrn.return_value = None
        mock_db.find_care_plan_by_patient_name.return_value = None
        mock_db.find_care_plan_by_order.return_value = None
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = None

        warnings = check_duplicate_warnings(sample_request)
        assert warnings == []

    @patch("services.db")
    def test_duplicate_mrn_warns(self, mock_db, sample_request):
        mock_db.find_care_plan_by_mrn.return_value = {"id": 1}
        mock_db.find_care_plan_by_order.return_value = None
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = None

        warnings = check_duplicate_warnings(sample_request)
        assert len(warnings) == 1
        assert "MRN" in warnings[0]

    @patch("services.db")
    def test_duplicate_order_warns(self, mock_db, sample_request):
        mock_db.find_care_plan_by_mrn.return_value = None
        mock_db.find_care_plan_by_patient_name.return_value = None
        mock_db.find_care_plan_by_order.return_value = {"id": 1}
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = None

        warnings = check_duplicate_warnings(sample_request)
        assert len(warnings) == 1
        assert "order" in warnings[0].lower()


class TestProviderConflicts:
    """Tests for provider conflict detection."""

    @patch("services.db")
    def test_no_conflict_returns_empty(self, mock_db):
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = None

        warnings = check_provider_conflicts("Dr. Smith", "1234567890")
        assert warnings == []

    @patch("services.db")
    def test_npi_with_different_name_warns(self, mock_db):
        mock_db.find_provider_by_npi.return_value = {"name": "Dr. Jones", "npi": "1234567890"}
        mock_db.find_provider_by_name.return_value = None

        warnings = check_provider_conflicts("Dr. Smith", "1234567890")
        assert len(warnings) == 1
        assert "Dr. Jones" in warnings[0]

    @patch("services.db")
    def test_name_with_different_npi_warns(self, mock_db):
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = {"name": "Dr. Smith", "npi": "9999999999"}

        warnings = check_provider_conflicts("Dr. Smith", "1234567890")
        assert len(warnings) == 1
        assert "9999999999" in warnings[0]
