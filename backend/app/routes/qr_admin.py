from fastapi import APIRouter, HTTPException
from app.database.supabase import supabase
from datetime import datetime

router = APIRouter()

@router.post("/admin/assign-qr")
def assign_qr(payload: dict):
    token = payload.get("token")
    client_id = payload.get("client_id")

    if not token or not client_id:
        raise HTTPException(status_code=400, detail="token and client_id required")

    qr = (
        supabase
        .table("qr_tokens")
        .select("*")
        .eq("token", token)
        .single()
        .execute()
        .data
    )

    if not qr:
        raise HTTPException(status_code=404, detail="QR not found")

    supabase.table("qr_tokens").update({
        "client_id": client_id,
        "assigned_at": datetime.utcnow()
    }).eq("token", token).execute()

    return {"status": "assigned"}


@router.post("/admin/unassign-qr")
def unassign_qr(payload: dict):
    token = payload.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="token required")

    supabase.table("qr_tokens").update({
        "client_id": None,
        "assigned_at": None
    }).eq("token", token).execute()

    return {"status": "unassigned"}
