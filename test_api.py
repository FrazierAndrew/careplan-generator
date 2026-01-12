"""
Test script for Care Plan API - run against the live server.
Usage: python test_api.py
"""
import requests
import os

BASE_URL = "http://localhost:8001"


def reset_database():
    """Delete and reinitialize the database for clean test runs."""
    from database import init_db
    
    db_path = "careplan.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Deleted careplan.db")
    
    init_db()
    print("✅ Initialized fresh database\n")


def submit(data, expected_success=True, description=""):
    """Submit a care plan and print results."""
    resp = requests.post(f"{BASE_URL}/submit", data=data)
    result = resp.json()
    
    patient = f"{data.get('patient_first_name')} {data.get('patient_last_name')}"
    print(f"{'─' * 60}")
    print(f"TEST: {description or patient}")
    print(f"Status: {resp.status_code}")
    
    if result.get("success"):
        print(f"✅ Success - Care Plan ID: {result.get('id')}")
        if result.get("warnings"):
            print("⚠️  Warnings:")
            for w in result["warnings"]:
                print(f"   - {w}")
    else:
        print(f"❌ Failed - Errors: {result.get('errors')}")
    
    # Check if result matches expectation
    if result.get("success") != expected_success:
        print(f"🚨 UNEXPECTED: expected success={expected_success}")
    
    print()
    return resp


def run_tests():
    print("\n" + "=" * 60)
    print("CARE PLAN API TEST SUITE")
    print("=" * 60 + "\n")
    
    # --- Valid submissions ---
    
    submit(
        {
            "patient_first_name": "John",
            "patient_last_name": "Doe",
            "referring_provider": "Dr. Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "123456",
            "primary_diagnosis": "E11.9",
            "medication_name": "Humira",
            "patient_records": "Patient has Type 2 diabetes, well controlled on current regimen.",
        },
        expected_success=True,
        description="Valid first submission"
    )
    
    submit(
        {
            "patient_first_name": "Jane",
            "patient_last_name": "Smith",
            "referring_provider": "Dr. Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "654321",
            "primary_diagnosis": "J45.20",
            "medication_name": "Dupixent",
        },
        expected_success=True,
        description="Valid second patient, same provider"
    )
    
    # --- Duplicate warnings ---
    
    submit(
        {
            "patient_first_name": "Johnny",
            "patient_last_name": "Different",
            "referring_provider": "Dr. Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "123456",  # Same MRN as John Doe
            "primary_diagnosis": "J45.20",
            "medication_name": "Dupixent",
        },
        expected_success=True,  # Should succeed but with warning
        description="Duplicate MRN - should WARN"
    )
    
    submit(
        {
            "patient_first_name": "John",
            "patient_last_name": "Doe",
            "referring_provider": "Dr. Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "999888",  # Different MRN
            "primary_diagnosis": "E11.9",
            "medication_name": "Ozempic",
        },
        expected_success=True,  # Should succeed but with warning
        description="Duplicate patient name - should WARN"
    )
    
    submit(
        {
            "patient_first_name": "John",
            "patient_last_name": "Doe",
            "referring_provider": "Dr. Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "123456",
            "primary_diagnosis": "E11.9",  # Same diagnosis
            "medication_name": "Humira",   # Same medication
        },
        expected_success=True,  # Should succeed but with warning
        description="Duplicate order (same patient+med+diagnosis) - should WARN"
    )
    
    # --- Provider conflicts ---
    
    submit(
        {
            "patient_first_name": "Alice",
            "patient_last_name": "Wonder",
            "referring_provider": "Dr. Smith",  # Same provider name
            "referring_provider_npi": "9999999999",  # Different NPI!
            "patient_mrn": "111111",
            "primary_diagnosis": "E11.9",
            "medication_name": "Trulicity",
        },
        expected_success=True,  # Should succeed but with warning
        description="Provider name with different NPI - should WARN"
    )
    
    submit(
        {
            "patient_first_name": "Bob",
            "patient_last_name": "Builder",
            "referring_provider": "Dr. Different Name",  # Different name
            "referring_provider_npi": "1234567890",  # Same NPI as Dr. Smith
            "patient_mrn": "222222",
            "primary_diagnosis": "E11.9",
            "medication_name": "Jardiance",
        },
        expected_success=True,  # Should succeed but with warning
        description="Different provider name with existing NPI - should WARN"
    )
    
    # --- Validation failures ---
    
    submit(
        {
            "patient_first_name": "Bad",
            "patient_last_name": "NPI",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "123",  # Too short
            "patient_mrn": "333333",
            "primary_diagnosis": "E11.9",
            "medication_name": "Test",
        },
        expected_success=False,
        description="Invalid NPI (too short) - should FAIL"
    )
    
    submit(
        {
            "patient_first_name": "Bad",
            "patient_last_name": "MRN",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1111111111",
            "patient_mrn": "12345",  # Too short (5 digits)
            "primary_diagnosis": "E11.9",
            "medication_name": "Test",
        },
        expected_success=False,
        description="Invalid MRN (too short) - should FAIL"
    )
    
    submit(
        {
            "patient_first_name": "Bad",
            "patient_last_name": "ICD",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "1111111111",
            "patient_mrn": "444444",
            "primary_diagnosis": "INVALID",  # Not a valid ICD-10
            "medication_name": "Test",
        },
        expected_success=False,
        description="Invalid ICD-10 code - should FAIL"
    )
    
    submit(
        {
            "patient_first_name": "Bad",
            "patient_last_name": "NPI Letters",
            "referring_provider": "Dr. Test",
            "referring_provider_npi": "123456789A",  # Has a letter
            "patient_mrn": "555555",
            "primary_diagnosis": "E11.9",
            "medication_name": "Test",
        },
        expected_success=False,
        description="NPI with letters - should FAIL"
    )
    
    print("=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if "--reset" in sys.argv:
        reset_database()
    
    run_tests()
