# routes/generate_review.py

from fastapi import APIRouter, HTTPException
from app.brain.ai_engine import generate_review
from app.routes.admin_data import get_admin_data
from app.database.supabase import supabase

router = APIRouter()

@router.post("/generate-review")
def generate_review_route(payload: dict):
    """
    REQUIRED:
    - client_id
    - rating (3–5)

    OPTIONAL:
    - language
    - product / products_services
    - area
    - experience
    """

    client_id = payload.get("client_id")
    rating = payload.get("rating")

    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")

    if not rating or rating < 3 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 3–5")

    # 1️⃣ Fetch admin + DB data (includes guard: active + expiry)
    admin_data = get_admin_data(client_id)

    language = payload.get("language", "English")
    product = payload.get("product") or payload.get("products_services")

    # 2️⃣ LOG QR REVIEW EVENT
    supabase.table("qr_review_logs").insert({
        "client_id": client_id,
        "rating": rating,
        "language": language,
        "product": product
    }).execute()

    # 3️⃣ Merge payload + admin data
    final_payload = {
        "client_id": client_id,
        "business_id": client_id,
        "industry": admin_data["industry"],
        "shop_name": admin_data.get("shop_name"),
        "rating": rating,
        "language": language,
        "product": product,
        "area": payload.get("area") or admin_data.get("area"),
        "experience": payload.get("experience"),
        "admin_data": {
            "contexts": admin_data.get("contexts", []),
            "trust_signals": admin_data.get("trust_signals", []),
            "services": admin_data.get("products_services", []),
            "areas": [admin_data.get("area")] if admin_data.get("area") else [],
            "seo_keywords": admin_data.get("seo_keywords", []),
            "tone": admin_data.get("tone"),
            "verbosity": admin_data.get("verbosity"),
        }
    }

    # 4️⃣ Generate review
    print("=== FINAL PAYLOAD SENT TO AI ===")
    print(final_payload)
    return generate_review(final_payload)
    