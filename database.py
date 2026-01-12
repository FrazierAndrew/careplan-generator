"""
Database layer - Pure CRUD operations only.
No business logic or interpretation of data.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List

DATABASE_PATH = Path("careplan.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS care_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_first_name TEXT NOT NULL,
                patient_last_name TEXT NOT NULL,
                referring_provider TEXT NOT NULL,
                referring_provider_npi TEXT NOT NULL,
                patient_mrn TEXT NOT NULL,
                primary_diagnosis TEXT NOT NULL,
                medication_name TEXT NOT NULL,
                additional_diagnoses TEXT,
                medication_history TEXT,
                patient_records TEXT,
                generated_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                npi TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# --- Care Plan queries ---

def find_care_plan_by_mrn(mrn: str) -> Optional[dict]:
    """Find a care plan by patient MRN."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM care_plans WHERE patient_mrn = ?", (mrn,))
        row = cursor.fetchone()
        return dict(row) if row else None


def find_care_plan_by_patient_name(first_name: str, last_name: str) -> Optional[dict]:
    """Find a care plan by patient name (case-insensitive)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM care_plans 
               WHERE LOWER(patient_first_name) = LOWER(?) 
               AND LOWER(patient_last_name) = LOWER(?)""",
            (first_name, last_name)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def find_care_plan_by_order(mrn: str, medication_name: str, primary_diagnosis: str) -> Optional[dict]:
    """Find a care plan matching the exact order criteria."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM care_plans 
               WHERE patient_mrn = ? 
               AND LOWER(medication_name) = LOWER(?) 
               AND LOWER(primary_diagnosis) = LOWER(?)""",
            (mrn, medication_name, primary_diagnosis)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def insert_care_plan(data: dict, generated_plan: str) -> int:
    """Insert a care plan and return the new ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO care_plans 
               (patient_first_name, patient_last_name, referring_provider, 
                referring_provider_npi, patient_mrn, primary_diagnosis, 
                medication_name, additional_diagnoses, medication_history, 
                patient_records, generated_plan)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["patient_first_name"],
                data["patient_last_name"],
                data["referring_provider"],
                data["referring_provider_npi"],
                data["patient_mrn"],
                data["primary_diagnosis"],
                data["medication_name"],
                data.get("additional_diagnoses", ""),
                data.get("medication_history", ""),
                data.get("patient_records", ""),
                generated_plan
            )
        )
        return cursor.lastrowid


def get_all_care_plans() -> List[dict]:
    """Get all care plans for export."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM care_plans ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# --- Provider queries ---

def find_provider_by_npi(npi: str) -> Optional[dict]:
    """Find a provider by NPI."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM providers WHERE npi = ?", (npi,))
        row = cursor.fetchone()
        return dict(row) if row else None


def find_provider_by_name(name: str) -> Optional[dict]:
    """Find a provider by name (case-insensitive)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM providers WHERE LOWER(name) = LOWER(?)", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def insert_provider(name: str, npi: str) -> bool:
    """Insert a provider if not exists. Returns True if inserted."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO providers (name, npi) VALUES (?, ?)",
            (name, npi)
        )
        return cursor.rowcount > 0
