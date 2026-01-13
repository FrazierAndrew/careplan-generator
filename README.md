# Care Plan Generator

A web application for pharmacies to automatically generate patient care plans.

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


## Running Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for care plan generation |
| `DATABASE_PATH` | No | Path to SQLite database file (default: `careplan.db`) |

## Project Structure

```
├── main.py          # FastAPI routes (transport layer)
├── services.py      # Business logic (duplicate detection, orchestration)
├── database.py      # SQLite CRUD operations
├── models.py        # Pydantic validation models
├── llm.py           # OpenAI integration
├── pdf_utils.py     # PDF text extraction utilities
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
