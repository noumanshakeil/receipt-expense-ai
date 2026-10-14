from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import receipts as svc

class ReceiptIn(BaseModel):
    merchant: str = Field(min_length=2)
    raw_text: str = Field(min_length=5)

class ReportIn(BaseModel):
    title: str = "Expense report"

router = APIRouter()

@router.post("/receipts")
async def ingest(payload: ReceiptIn, db: AsyncSession = Depends(get_db)):
    rec = await svc.ingest_text(db, payload.merchant, payload.raw_text)
    return {"id": rec.id, "category": rec.category, "total": rec.total}

@router.get("/receipts")
async def list_receipts(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_receipts(db)
    return {"receipts": [{"id": r.id, "merchant": r.merchant, "category": r.category, "total": r.total} for r in rows]}

@router.post("/receipts/{receipt_id}/categorize")
async def categorize(receipt_id: str, db: AsyncSession = Depends(get_db)):
    try:
        rec = await svc.categorize_with_llm(db, receipt_id)
        return {"id": rec.id, "category": rec.category}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

@router.post("/reports/export")
async def export_report(payload: ReportIn, db: AsyncSession = Depends(get_db)):
    rep = await svc.export_report(db, payload.title)
    return {"id": rep.id, "title": rep.title, "csv": rep.csv_body}
