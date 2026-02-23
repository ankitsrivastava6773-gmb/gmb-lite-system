import random
import os
from supabase import create_client
from datetime import datetime
from app.core.openai_client import client   # ✅ already used infra

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# ---------------- CONFIG ----------------
USAGE_LIMIT = 10

# ⛑️ HARD FALLBACK POOLS (UNCHANGED)
OPENING_POOLS = {
    "positive": [
        "Recently, I had the chance to visit this place",
        "I wasn’t sure what to expect at first",
        "During my recent visit here",
        "I decided to try this place after hearing about it",
        "I had been meaning to visit this place for a while"
    ],
    "neutral": [
        "I visited this place recently",
        "I stopped by this place not long ago",
        "I had a visit here recently"
    ]
}

# ---------------- HELPERS ----------------
def rating_bucket(rating: int) -> str:
    return "positive" if rating >= 4 else "neutral"


def _mark_opening_used(
    business_id: str,
    industry: str,
    opening: str
):
    supabase.table("opening_usage").upsert(
        {
            "business_id": business_id,
            "industry": industry,
            "opening_text": opening,
            "usage_count": 1,
            "last_used": datetime.utcnow().isoformat()
        },
        on_conflict="business_id,industry,opening_text"
    ).execute()


# ---------------- AI OPENING GENERATOR ----------------
def _generate_ai_opening(
    industry: str,
    rating: int
) -> str | None:
    """
    Generates a short, natural review opening.
    Returns None if AI fails (so fallback can kick in).
    """

    tone = "positive" if rating >= 4 else "neutral"

    prompt = (
        f"Write ONE short, natural opening sentence for a Google review.\n"
        f"Industry: {industry}\n"
        f"Tone: {tone}\n"
        f"Rules:\n"
        f"- Human, casual\n"
        f"- No marketing words\n"
        f"- No emojis\n"
        f"- Max 15 words\n"
        f"- Do NOT mention Google or rating\n"
    )

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )

        text = res.choices[0].message.content.strip()

        if len(text.split()) < 4:
            return None

        return text.rstrip(".")
    except Exception:
        return None


# ---------------- CORE ----------------
def pick_opening(
    business_id: str,
    industry: str,
    rating: int
) -> str:
    """
    Production-grade opening picker
    ✔ AI-generated dynamic opening (PRIMARY)
    ✔ DB exhaustion protection
    ✔ Hard fallback pool (NEVER FAILS)
    """

    # ✅ 1️⃣ TRY AI FIRST
    ai_opening = _generate_ai_opening(industry, rating)
    if ai_opening:
        _mark_opening_used(business_id, industry, ai_opening)
        return ai_opening

    # ⛑️ 2️⃣ FALLBACK TO EXISTING POOL (UNCHANGED LOGIC)
    bucket = rating_bucket(rating)
    pool = OPENING_POOLS.get(bucket, OPENING_POOLS["positive"])
    random.shuffle(pool)

    for opening in pool:
        resp = (
            supabase
            .table("opening_usage")
            .select("usage_count")
            .eq("business_id", business_id)
            .eq("industry", industry)
            .eq("opening_text", opening)
            .maybe_single()
            .execute()
        )

        row = resp.data if resp else None

        if not row or row.get("usage_count", 0) < USAGE_LIMIT:
            _mark_opening_used(business_id, industry, opening)
            return opening

    # -------- HARD FALLBACK (NEVER FAILS) --------
    least_resp = (
        supabase
        .table("opening_usage")
        .select("opening_text")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .order("usage_count", desc=False)
        .limit(1)
        .execute()
    )

    least = least_resp.data or []
    opening = least[0]["opening_text"] if least else random.choice(pool)

    _mark_opening_used(business_id, industry, opening)
    return opening