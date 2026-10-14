from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import receipts as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    rows = await svc.list_receipts(db)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Receipt Expense AI", "receipts": rows})

@router.post("/ui/receipts")
async def ui_receipt(merchant: str = Form(...), raw_text: str = Form(...), db: AsyncSession = Depends(get_db)):
    await svc.ingest_text(db, merchant, raw_text)
    return RedirectResponse("/", status_code=303)
