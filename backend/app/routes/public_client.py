from fastapi import APIRouter, HTTPException
from app.database.supabase import supabase
from datetime import datetime, timedelta, timezone, date

router = APIRouter()

# ---------- IST TIMEZONE ----------
IST = timezone(timedelta(hours=5, minutes=30))


# ---------- DATE HELPER ----------
def to_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


@router.get("/public-client/{client_id}")
def get_public_client(client_id: str):
    res = (
        supabase
        .table("clients")
        .select(
            "id, shop_name, products_services, gmb_link, logo_url, area, is_active, start_date, end_date"
        )
        .eq("id", client_id)
        .execute()
    )

    client = res.data[0] if res.data else None

    if not client:
        raise HTTPException(status_code=404, detail="Invalid QR")

    # 🔒 Manual OFF
    if client.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Service inactive")

    today = datetime.now(IST).date()

    start_date = to_date(client.get("start_date"))
    end_date = to_date(client.get("end_date"))

    if start_date and today < start_date:
        raise HTTPException(status_code=403, detail="Service not started")

    if end_date and today > end_date:
        raise HTTPException(status_code=403, detail="Service expired")

    # ✅ SUCCESS RESPONSE
    return {
        "shop_name": client.get("shop_name"),
        "area": client.get("area"),

        "products_services": (
            client.get("products_services").split(",")
            if client.get("products_services")
            else []
        ),

        "gmb_link": client.get("gmb_link"),
        "logo_url": client.get("logo_url")  # 🔥 THIS WAS MISSING
    }