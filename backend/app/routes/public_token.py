from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime, date, timezone, timedelta
from app.database.supabase import supabase

router = APIRouter()

# ---------- IST TIMEZONE ----------
IST = timezone(timedelta(hours=5, minutes=30))


# ---------- DATE HELPER ----------
def to_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


@router.get("/r/{token}")
def resolve_qr_token(token: str):
    """
    FLOW:
    /r/{token}
      → validate token
      → find client
      → validate client status
      → REDIRECT to /review/{client_id}
    """

    # 1️⃣ Fetch token (SAFE)
    res = (
        supabase
        .table("qr_tokens")
        .select("token, client_id, is_active")
        .eq("token", token)
        .execute()
    )

    qr = res.data[0] if res.data else None

    if not qr:
        raise HTTPException(status_code=404, detail="Invalid QR")

    if qr.get("is_active") is False:
        raise HTTPException(status_code=403, detail="QR inactive")

    client_id = qr.get("client_id")
    if not client_id:
        raise HTTPException(status_code=403, detail="QR not assigned")

    # 2️⃣ Fetch client (SAFE)
    res_client = (
        supabase
        .table("clients")
        .select("id, is_active, start_date, end_date")
        .eq("id", client_id)
        .execute()
    )

    client = res_client.data[0] if res_client.data else None

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # 3️⃣ Manual OFF check
    if client.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Service inactive")

    # 4️⃣ Date validation (IST safe)
    today = datetime.now(IST).date()

    start_date = to_date(client.get("start_date"))
    end_date = to_date(client.get("end_date"))

    if start_date and today < start_date:
        raise HTTPException(status_code=403, detail="Service not started")

    if end_date and today > end_date:
        raise HTTPException(status_code=403, detail="Service expired")

    # 5️⃣ ✅ FINAL REDIRECT
    return RedirectResponse(
        url=f"/review/{client_id}",
        status_code=302
    )