"""Unit tests for business logic in services."""
import pytest
from unittest.mock import patch, MagicMock
from models import CarePlanRequest
from services import check_duplicate_warnings, check_blocking_provider_conflict, ProviderConflictError


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
        mock_db.find_previous_submission.return_value = None

        warnings = check_duplicate_warnings(sample_request)
        assert warnings == []

    @patch("services.db")
    def test_duplicate_mrn_warns(self, mock_db, sample_request):
        mock_db.find_care_plan_by_mrn.return_value = {"id": 1}
        mock_db.find_previous_submission.return_value = None

        warnings = check_duplicate_warnings(sample_request)
        assert len(warnings) == 1
        assert "MRN" in warnings[0]

    @patch("services.db")
    def test_previous_submission_warns(self, mock_db, sample_request):
        mock_db.find_care_plan_by_mrn.return_value = None
        mock_db.find_care_plan_by_patient_name.return_value = None
        mock_db.find_previous_submission.return_value = {"id": 1}

        warnings = check_duplicate_warnings(sample_request)
        assert len(warnings) == 1
        assert "previous date" in warnings[0].lower()


class TestProviderConflicts:
    """Tests for provider conflict blocking."""

    @patch("services.db")
    def test_no_conflict_passes(self, mock_db):
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = None

        # Should not raise
        check_blocking_provider_conflict("Dr. Smith", "1234567890")

    @patch("services.db")
    def test_npi_with_different_name_raises(self, mock_db):
        mock_db.find_provider_by_name.return_value = None
        mock_db.find_provider_by_npi.return_value = {"name": "Dr. Jones", "npi": "1234567890"}

        with pytest.raises(ProviderConflictError) as exc:
            check_blocking_provider_conflict("Dr. Smith", "1234567890")
        assert "Dr. Jones" in str(exc.value)

    @patch("services.db")
    def test_name_with_different_npi_raises(self, mock_db):
        mock_db.find_provider_by_npi.return_value = None
        mock_db.find_provider_by_name.return_value = {"name": "Dr. Smith", "npi": "9999999999"}

        with pytest.raises(ProviderConflictError) as exc:
            check_blocking_provider_conflict("Dr. Smith", "1234567890")
        assert "9999999999" in str(exc.value)
