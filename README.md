# Care Plan Generator

A web application for specialty pharmacies to automatically generate patient care plans using AI.

## Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --reload --port 8001
   ```

5. **Open in browser:**
   Navigate to http://localhost:8001

## Features

- HTML web form for patient data entry
- Pydantic validation for all inputs (NPI, MRN, ICD-10 codes)
- SQLite database for storing care plans
- OpenAI integration for generating care plans
- Duplicate detection warnings for:
  - Patients (by MRN or name)
  - Orders (same patient, medication, diagnosis)
  - Providers (NPI mismatches)
- Download generated care plan as text file
- CSV export for pharma reporting (`GET /export`)

## Running Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for care plan generation |

## Project Structure

```
├── main.py          # FastAPI routes (transport layer)
├── services.py      # Business logic (duplicate detection, orchestration)
├── database.py      # SQLite CRUD operations
├── models.py        # Pydantic validation models
├── llm.py           # OpenAI integration
├── templates/
│   └── index.html   # Web form
├── tests/
│   ├── test_models.py       # Unit tests for validation
│   ├── test_services.py     # Unit tests for business logic
│   └── test_integration.py  # API integration tests
├── test_api.py      # Manual API test script
├── requirements.txt
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web form for data entry |
| `/submit` | POST | Submit care plan request |
| `/export` | GET | Download all care plans as CSV |
