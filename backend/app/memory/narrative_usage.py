import os
from supabase import create_client
from datetime import datetime, timezone

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

MAX_USE_PER_NARRATIVE = 5  # ek style max 5 baar

# 1️⃣ Check karo: ye narrative abhi allowed hai ya nahi
def is_narrative_allowed(business_id: str, industry: str, narrative: str) -> bool:
    res = (
        supabase
        .table("narrative_usage")
        .select("usage_count")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .eq("narrative", narrative)
        .limit(1)
        .execute()
    )

    if not res.data:
        return True  # first time → allowed

    return res.data[0]["usage_count"] < 3


# 2️⃣ Jab narrative use ho jaaye to count badhao
def mark_narrative_used(business_id: str, industry: str, narrative: str):
    # pehle check: row hai ya nahi
    res = (
        supabase
        .table("narrative_usage")
        .select("id, usage_count")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .eq("narrative", narrative)
        .limit(1)
        .execute()
    )

    # ❗ first time → INSERT
    if not res.data:
        supabase.table("narrative_usage").insert({
            "business_id": business_id,
            "industry": industry,
            "narrative": narrative,
            "usage_count": 1
        }).execute()
        return

    # existing → UPDATE
    row = res.data[0]
    supabase.table("narrative_usage").update({
        "usage_count": row["usage_count"] + 1
    }).eq("id", row["id"]).execute()