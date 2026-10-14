# Dev server for receipt-expense-ai
$env:LLM_MODE = "mock"
uvicorn backend.main:app --reload --port 8000
