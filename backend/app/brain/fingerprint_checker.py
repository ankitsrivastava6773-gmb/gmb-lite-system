# app/brain/fingerprint_checker.py
import re
from difflib import SequenceMatcher
from app.database.supabase import supabase

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def structure_fingerprint(text: str) -> str:
    """
    Sentence length pattern fingerprint
    S = short, M = medium, L = long
    """
    sentences = re.split(r"[.!?]", text)
    pattern = []

    for s in sentences:
        w = len(s.strip().split())
        if w == 0:
            continue
        if w <= 6:
            pattern.append("S")
        elif w <= 14:
            pattern.append("M")
        else:
            pattern.append("L")

    return "-".join(pattern)

def is_fingerprint_duplicate(
    business_id: str,
    industry: str,
    new_text: str,
    similarity_threshold: float = 0.55
) -> bool:
    """
    HARD anti-spam check:
    - structure fingerprint
    - semantic similarity
    """

    new_norm = normalize(new_text)
    new_fp = structure_fingerprint(new_text)

    res = (
        supabase
        .table("review_memory")
        .select("review_text, fingerprint")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .order("created_at", desc=True)
        .limit(40)
        .execute()
    )

    rows = res.data or []

    for r in rows:
        old_text = r.get("review_text") or ""
        old_fp = r.get("fingerprint") or ""

        # 1️⃣ Structure repeat = BLOCK
        if old_fp == new_fp and new_fp:
            return True

        # 2️⃣ Semantic similarity
        old_norm = normalize(old_text)
        ratio = SequenceMatcher(None, new_norm, old_norm).ratio()

        if ratio >= similarity_threshold:
            return True

    return False

def save_fingerprint(
    business_id: str,
    industry: str,
    review_text: str
):
    supabase.table("review_memory").insert({
        "business_id": business_id,
        "industry": industry,
        "review_text": review_text,
        "fingerprint": structure_fingerprint(review_text)
    }).execute()