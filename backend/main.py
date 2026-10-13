"""Receipt Expense AI — FastAPI backend + Jinja UI."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .llm import complete

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "data" / "store.json"
FIELDS = ['merchant', 'total', 'category']

app = FastAPI(title="Receipt Expense AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))


def load_store() -> dict:
    if not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        payload = {"receipts": [
  {
    "id": "rc1",
    "merchant": "Cafe",
    "total": 12.5,
    "category": "meals"
  }
]}
        DATA.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json.loads(DATA.read_text(encoding="utf-8"))


def save_store(store: dict) -> None:
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(store, indent=2), encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "receipt-expense-ai", "llm_mode": settings.llm_mode}


@app.get("/api/receipts")
def list_items() -> dict:
    store = load_store()
    return {"receipts": store.get("receipts", [])}


@app.post("/api/receipts")
def create_item(payload: dict) -> dict:
    store = load_store()
    item = {"id": uuid.uuid4().hex[:8]}
    for key in FIELDS:
        item[key] = payload.get(key)
    store.setdefault("receipts", []).insert(0, item)
    save_store(store)
    return item


@app.post("/api/categorize")
def run_action(payload: dict) -> dict:
    """Suggest expense category and line items."""
    prompt = (
        "You are the AI engine for Receipt Expense AI.\n"
        "Task: Suggest expense category and line items.\n"
        f"Input JSON: {json.dumps(payload)[:4000]}"
    )
    text = complete(prompt)
    return {"ok": True, "action": "categorize", "result": text, "mode": settings.llm_mode}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, last_result: str | None = None) -> HTMLResponse:
    store = load_store()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Receipt Expense AI",
            "description": "Receipt capture to expense lines with category suggestions and approval UI.",
            "resource": "receipts",
            "action": "categorize",
            "action_desc": "Suggest expense category and line items",
            "items": store.get("receipts", []),
            "llm_mode": settings.llm_mode,
            "last_result": last_result,
        },
    )


@app.post("/ui/create", response_class=HTMLResponse)
async def ui_create(request: Request) -> HTMLResponse:
    form = await request.form()
    data = {k: form.get(k) for k in FIELDS}
    create_item(data)
    return home(request)


@app.post("/ui/action", response_class=HTMLResponse)
async def ui_action(request: Request, prompt: str = Form("demo")) -> HTMLResponse:
    result = run_action({"prompt": prompt})
    store = load_store()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Receipt Expense AI",
            "description": "Receipt capture to expense lines with category suggestions and approval UI.",
            "resource": "receipts",
            "action": "categorize",
            "action_desc": "Suggest expense category and line items",
            "items": store.get("receipts", []),
            "llm_mode": settings.llm_mode,
            "last_result": result.get("result"),
        },
    )
