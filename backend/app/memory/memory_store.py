# app/memory/memory_store.py

from app.database.supabase import supabase

# 1️⃣ Recent reviews nikalna (per business)
def get_recent_reviews(business_id: str, industry: str, limit: int = 50):
    res = (
        supabase
        .table("review_memory")
        .select("review_text, fingerprint")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []

# 2️⃣ Review memory me save karna
def save_review(
    business_id: str,
    industry: str,
    review_text: str,
    fingerprint: str
):
    supabase.table("review_memory").insert({
        "business_id": business_id,
        "industry": industry,
        "review_text": review_text,
        "fingerprint": fingerprint
    }).execute()