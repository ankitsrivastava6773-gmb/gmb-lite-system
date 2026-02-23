# routes/qr_stats.py

from fastapi import APIRouter, HTTPException
from app.database.supabase import supabase

router = APIRouter()

@router.get("/admin/qr-stats/{client_id}")
def get_qr_stats(client_id: str):
    logs = (
        supabase
        .table("qr_review_logs")
        .select("rating, language, product, created_at")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    if logs is None:
        raise HTTPException(status_code=404, detail="No QR data found")

    total = len(logs)

    breakdown = {3: 0, 4: 0, 5: 0}
    rating_sum = 0
    last_scan = None

    for l in logs:
        r = l.get("rating")
        if r in breakdown:
            breakdown[r] += 1
            rating_sum += r

    if logs:
        last_scan = logs[0].get("created_at")

    return {
        "client_id": client_id,
        "total_scans": total,
        "avg_rating": round(rating_sum / total, 2) if total else 0,
        "rating_breakdown": breakdown,
        "last_scan": last_scan
    }