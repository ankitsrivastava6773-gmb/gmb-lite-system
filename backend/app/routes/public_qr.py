from fastapi import APIRouter, HTTPException
from app.database.supabase import supabase

router = APIRouter()   # ✅ THIS LINE WAS MISSING

@router.get("/r/{token}")
def resolve_qr_token(token: str):
    res = (
        supabase
        .table("qr_tokens")
        .select("client_id, is_active")
        .eq("token", token)
        .execute()
    )

    row = res.data[0] if res.data else None

    if not row:
        raise HTTPException(status_code=404, detail="Invalid QR")

    if row.get("is_active") is False:
        raise HTTPException(status_code=403, detail="QR inactive")

    if not row.get("client_id"):
        raise HTTPException(status_code=404, detail="QR not assigned")

    return {
        "client_id": row["client_id"]
    }