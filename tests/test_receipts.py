import pytest

@pytest.mark.asyncio
async def test_receipt_export(client):
    await client.post("/api/receipts", json={"merchant": "Cafe", "raw_text": "Latte 4.50\nMuffin 3.25"})
    ex = await client.post("/api/reports/export", json={"title": "Q1"})
    assert ex.status_code == 200
    assert "merchant" in ex.json()["csv"]
