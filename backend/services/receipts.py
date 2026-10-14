from __future__ import annotations
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.llm import get_llm
from backend.models import ExpenseReport, LineItem, Receipt
from backend.services.io_export import dump_csv
from backend.utils.ids import short_id
from backend.vision.pipeline import run_offline_pipeline

_AMT = re.compile(r"\$?\s*(\d+(?:\.\d{2})?)")
_LINE = re.compile(r"^(.+?)\s+(\d+\.\d{2})\s*$", re.M)

def _guess_category(merchant: str, text: str) -> str:
    blob = (merchant + " " + text).lower()
    if any(w in blob for w in ("uber", "lyft", "taxi", "fuel", "gas")):
        return "travel"
    if any(w in blob for w in ("coffee", "cafe", "restaurant", "food")):
        return "meals"
    if any(w in blob for w in ("aws", "github", "software", "saas")):
        return "software"
    return "general"

def _parse_lines(text: str) -> list[tuple[str, float]]:
    items: list[tuple[str, float]] = []
    for m in _LINE.finditer(text):
        items.append((m.group(1).strip()[:240], float(m.group(2))))
    if not items:
        for m in _AMT.finditer(text):
            items.append(("item", float(m.group(1))))
            break
    return items[:20]

async def ingest_text(session: AsyncSession, merchant: str, raw_text: str) -> Receipt:
    pipe = run_offline_pipeline(raw_text, steps=["normalize", "ocr"])
    body = pipe["text"]
    category = _guess_category(merchant, body)
    amounts = [a for _, a in _parse_lines(body)]
    total = round(sum(amounts), 2) if amounts else 0.0
    rec = Receipt(id=short_id(), merchant=merchant.strip()[:160], raw_text=body, category=category, total=total)
    session.add(rec)
    await session.flush()
    for desc, amt in _parse_lines(body):
        session.add(LineItem(id=short_id(), receipt_id=rec.id, description=desc, amount=amt))
    await session.commit()
    await session.refresh(rec)
    return rec

async def list_receipts(session: AsyncSession) -> list[Receipt]:
    return list((await session.execute(select(Receipt).order_by(Receipt.created_at.desc()))).scalars())

async def categorize_with_llm(session: AsyncSession, receipt_id: str) -> Receipt:
    rec = await session.get(Receipt, receipt_id)
    if not rec:
        raise ValueError("receipt not found")
    llm = get_llm()
    hint = await llm.complete(f"Categorize receipt for {rec.merchant}: {rec.raw_text[:300]}", system="Reply with one word category.")
    rec.category = (hint.split()[0] if hint else rec.category).lower()[:64]
    await session.commit()
    await session.refresh(rec)
    return rec

async def export_report(session: AsyncSession, title: str) -> ExpenseReport:
    receipts = await list_receipts(session)
    rows = [{"merchant": r.merchant, "category": r.category, "total": r.total} for r in receipts]
    csv_body = dump_csv(["merchant", "category", "total"], rows)
    rep = ExpenseReport(id=short_id(), title=title[:160], csv_body=csv_body)
    session.add(rep)
    await session.commit()
    await session.refresh(rep)
    return rep
