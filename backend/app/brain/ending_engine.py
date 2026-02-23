import random
import os
from datetime import datetime
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# ---------------- CONFIG ----------------
USAGE_LIMIT = 10

ENDINGS = {
    5: [
        "I’ll definitely be coming back.",
        "Overall, it was totally worth it.",
        "Really happy with the experience.",
        "Glad I chose this place."
    ],
    4: [
        "Overall, it was a good experience.",
        "Happy with how things turned out.",
        "Would consider coming back."
    ],
    3: [
        "It was okay overall.",
        "Decent experience, nothing major to complain about."
    ]
}

# ---------------- CORE ----------------
def pick_ending(business_id: str, industry: str, rating: int) -> str:
    """
    Production-grade ending picker
    - Rating based pool
    - DB exhaustion (usage limit)
    - Safe fallback
    """

    pool = ENDINGS.get(rating, ENDINGS[4])
    random.shuffle(pool)

    for ending in pool:
        resp = (
            supabase
            .table("ending_usage")
            .select("usage_count")
            .eq("business_id", business_id)
            .eq("industry", industry)
            .eq("ending_text", ending)
            .maybe_single()   # ✅ FIX: zero row safe
            .execute()
        )

        row = resp.data if resp else None

        if not row or row.get("usage_count", 0) < USAGE_LIMIT:
            _mark_ending_used(business_id, industry, ending)
            return ending

    # ---- fallback: least used ending ----
    least = (
        supabase
        .table("ending_usage")
        .select("ending_text")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .order("usage_count")
        .limit(1)
        .execute()
        .data
    )

    ending = least[0]["ending_text"] if least else random.choice(pool)
    _mark_ending_used(business_id, industry, ending)
    return ending


def _mark_ending_used(business_id: str, industry: str, ending: str):
    supabase.table("ending_usage").upsert(
        {
            "business_id": business_id,
            "industry": industry,
            "ending_text": ending,
            "usage_count": 1,
            "last_used": datetime.utcnow().isoformat()
        },
        on_conflict="business_id,industry,ending_text"
    ).execute()