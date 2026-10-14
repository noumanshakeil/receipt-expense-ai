from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

def utcnow(): return datetime.utcnow()

class Receipt(Base):
    __tablename__ = "receipts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    merchant: Mapped[str] = mapped_column(String(160), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True, default="uncategorized")
    total: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class LineItem(Base):
    __tablename__ = "line_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    receipt_id: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str] = mapped_column(String(240))
    amount: Mapped[float] = mapped_column(Float, default=0.0)

class ExpenseReport(Base):
    __tablename__ = "expense_reports"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    csv_body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
