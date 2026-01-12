# Care Plan Generator

A bare-bones web application for specialty pharmacies to generate patient care plans using AI.

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
   python main.py
   ```

5. **Open in browser:**
   Navigate to http://localhost:8000

## Features

- HTML web form for patient data entry
- Pydantic validation for all inputs
- SQLite database for storing care plans
- OpenAI integration for generating care plans
- Duplicate detection warnings for:
  - Patients (by MRN or name)
  - Orders (same patient, medication, diagnosis)
  - Providers (NPI mismatches)
- Download generated care plan as text file

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for care plan generation |

## Project Structure

```
├── main.py          # FastAPI application
├── models.py        # Pydantic validation models
├── database.py      # SQLite database functions
├── templates/
│   └── index.html   # Web form
├── requirements.txt # Python dependencies
└── README.md
```
