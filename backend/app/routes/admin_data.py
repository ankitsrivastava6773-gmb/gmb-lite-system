from fastapi import APIRouter, HTTPException
from datetime import datetime, date, timezone, timedelta
from app.database.supabase import supabase

router = APIRouter()

# ---------- DATE HELPER (CRITICAL FIX) ----------
def to_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


# ---------- STRING → LIST + VERBOSITY LIMIT ----------
def split_limit(value, limit):
    """
    Converts comma separated string into list
    and limits items based on verbosity.
    """
    if not value:
        return []
    items = [v.strip() for v in value.split(",") if v.strip()]
    return items[:limit]


def check_client_status(client: dict):
    """
    CENTRAL SINGLE SOURCE OF TRUTH
    This decides whether AI generation is allowed or not.
    """

    # 🔴 Manual active switch (soft stop)
    if client.get("is_active") is False:
        raise HTTPException(
            status_code=403,
            detail="Service inactive"
        )

    # 🔴 Date based expiry (IST – production safe)
    start_date = to_date(client.get("start_date"))
    end_date = to_date(client.get("end_date"))

    if start_date or end_date:
        IST = timezone(timedelta(hours=5, minutes=30))
        today = datetime.now(IST).date()

        # Service not started yet
        if start_date and today < start_date:
            raise HTTPException(
                status_code=403,
                detail="Service not started"
            )

        # Service expired
        if end_date and today > end_date:
            raise HTTPException(
                status_code=403,
                detail="Service expired"
            )


@router.get("/admin-data/{client_id}")
def get_admin_data(client_id: str):
    # 1️⃣ Client + type join (single fetch)
    res = (
        supabase
        .table("clients")
        .select("*, client_types(*)")
        .eq("id", client_id)
        .execute()
    )

    client = res.data[0] if res.data else None

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # 2️⃣ CENTRAL GUARD (AI ON/OFF + DATE LOGIC)
    check_client_status(client)

    ctype = client.get("client_types") or {}

    # 🔴 verbosity default (industry safe)
    verbosity = client.get("verbosity") or ctype.get("verbosity") or 2

    # 🔴 DEBUG VISIBILITY (unchanged, but meaningful now)
    print("=== ADMIN DATA RETURNED ===")
    print({
        "context_raw": client.get("context"),
        "trust_signals_raw": client.get("trust_signals"),
        "seo_keywords_raw": client.get("seo_keywords"),
        "products_services_raw": client.get("products_services"),
        "tone": client.get("tone"),
        "verbosity": verbosity
    })

    # 3️⃣ FINAL MERGED PAYLOAD (client > type fallback)
    return {
        "industry": ctype.get("type_name"),

        # 🔴 STATUS INFO
        "is_active": client.get("is_active"),
        "start_date": client.get("start_date"),
        "end_date": client.get("end_date"),
        "shop_name": client.get("shop_name"),

        # 🔴 CONTENT DATA (PRODUCTION FIXED)
        "contexts": split_limit(
            client.get("context") or ctype.get("context"),
            verbosity
        ),

        "trust_signals": split_limit(
            client.get("trust_signals") or ctype.get("trust_signals"),
            verbosity
        ),

        "seo_keywords": split_limit(
            client.get("seo_keywords") or ctype.get("seo_keywords"),
            3
        ),

        "products_services": split_limit(
            client.get("products_services") or ctype.get("products_services"),
            3
        ),

        "area": client.get("area"),

        # 🔴 AI BEHAVIOUR CONTROLS
        "tone": client.get("tone") or ctype.get("tone"),
        "verbosity": verbosity,
    }