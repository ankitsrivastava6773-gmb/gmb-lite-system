# routes/qr_token.py

from fastapi import APIRouter, HTTPException
from app.database.supabase import supabase
import uuid
from datetime import datetime

router = APIRouter(prefix="/admin/qr", tags=["QR Tokens"])

# 1️⃣ CREATE BULK QR TOKENS
@router.post("/create")
def create_qr_tokens(count: int = 50):
    tokens = []

    for _ in range(count):
        token = uuid.uuid4().hex[:12]
        tokens.append({
            "token": token
        })

    supabase.table("qr_tokens").insert(tokens).execute()

    return {
        "created": len(tokens),
        "tokens": [t["token"] for t in tokens]
    }


# 2️⃣ LIST FREE QR TOKENS
@router.get("/free")
def get_free_qr_tokens():
    data = (
        supabase
        .table("qr_tokens")
        .select("*")
        .is_("client_id", None)
        .eq("is_active", True)
        .execute()
        .data
    )

    return data or []


# 3️⃣ ASSIGN QR TO CLIENT
@router.post("/assign")
def assign_qr(token: str, client_id: str):
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
        raise HTTPException(status_code=404, detail="Invalid QR token")

    if qr.get("client_id"):
        raise HTTPException(status_code=400, detail="QR already assigned")

    supabase.table("qr_tokens").update({
        "client_id": client_id,
        "assigned_at": datetime.utcnow()
    }).eq("token", token).execute()

    return {"status": "assigned", "token": token}


# 4️⃣ UNASSIGN QR (MAKE REUSABLE)
@router.post("/unassign")
def unassign_qr(token: str):
    supabase.table("qr_tokens").update({
        "client_id": None,
        "assigned_at": None
    }).eq("token", token).execute()

    return {"status": "unassigned", "token": token}


# 5️⃣ DISABLE QR (SECURITY)
@router.post("/disable")
def disable_qr(token: str):
    supabase.table("qr_tokens").update({
        "is_active": False
    }).eq("token", token).execute()

    return {"status": "disabled", "token": token}