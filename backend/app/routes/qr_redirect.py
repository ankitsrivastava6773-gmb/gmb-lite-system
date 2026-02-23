from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.database.supabase import supabase
from datetime import datetime, timezone

router = APIRouter()

@router.get("/r/{token}")
def qr_redirect(token: str):
    """
    QR ENTRY POINT
    token → client_id → /review/{client_id}
    """

    # 1️⃣ Token lookup
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
        raise HTTPException(status_code=404, detail="Invalid QR")

    # 2️⃣ Token active check
    if qr.get("is_active") is False:
        raise HTTPException(status_code=403, detail="QR disabled")

    client_id = qr.get("client_id")

    # 3️⃣ Unassigned QR (blank card)
    if not client_id:
        raise HTTPException(
            status_code=403,
            detail="QR not assigned to any client"
        )

    # 4️⃣ Redirect to PUBLIC REVIEW PAGE
    return RedirectResponse(
        url=f"/review/{client_id}",
        status_code=302
    )