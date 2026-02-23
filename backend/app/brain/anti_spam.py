# brain/anti_spam.py
import re
import os
from supabase import create_client
from collections import Counter

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# ================= HELPERS =================

def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

def words(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").lower())

def normalize_set(text: str) -> set:
    return set(words(text))

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(len(a), 1)

# ---------- STRUCTURE FINGERPRINT ----------

def structure_fingerprint(text: str) -> str:
    """
    Sentence-length pattern: S/M/L
    """
    pattern = []
    for s in sentences(text):
        w = len(s.split())
        if w <= 6:
            pattern.append("S")
        elif w <= 14:
            pattern.append("M")
        else:
            pattern.append("L")
    return "-".join(pattern)

# ---------- OPENING / ENDING ----------

def opening_phrase(text: str) -> str:
    s = sentences(text)
    return " ".join(words(s[0])[:6]) if s else ""

def ending_phrase(text: str) -> str:
    s = sentences(text)
    return " ".join(words(s[-1])[-6:]) if s else ""

# ---------- MEANING FINGERPRINT ----------

def meaning_signature(text: str) -> Counter:
    """
    Rough semantic weight (emotion + experience)
    """
    buckets = {
        "emotion": ["happy", "satisfied", "comfortable", "relaxed", "impressed", "great"],
        "service": ["staff", "service", "team", "helpful", "support"],
        "experience": ["experience", "visit", "time", "process"],
    }

    tokens = words(text)
    sig = Counter()

    for k, vocab in buckets.items():
        for v in vocab:
            sig[k] += tokens.count(v)

    return sig

def meaning_similarity(a: Counter, b: Counter) -> float:
    common = sum((a & b).values())
    total = max(sum(a.values()), 1)
    return common / total

# ================= CORE =================

def is_duplicate(
    business_id: str,
    industry: str,
    new_text: str,
    text_threshold: float = 0.32,
    meaning_threshold: float = 0.6
) -> bool:
    """
    HARD anti-spam:
    - Opening repeat
    - Ending repeat
    - Structure repeat
    - Text similarity
    - Meaning similarity
    """

    res = (
        supabase
        .table("review_memory")
        .select("review_text, fingerprint")
        .eq("business_id", business_id)
        .eq("industry", industry)
        .order("created_at", desc=True)
        .limit(60)
        .execute()
    )

    rows = res.data or []

    new_words = normalize_set(new_text)
    new_fp = structure_fingerprint(new_text)
    new_open = opening_phrase(new_text)
    new_end = ending_phrase(new_text)
    new_meaning = meaning_signature(new_text)

    for r in rows:
        old_text = r.get("review_text") or ""
        old_fp = r.get("fingerprint") or ""

        # 1️⃣ Structure hard block
        if old_fp == new_fp:
            return True

        # 2️⃣ Opening hard block
        if opening_phrase(old_text) == new_open:
            return True

        # 3️⃣ Ending hard block
        if ending_phrase(old_text) == new_end:
            return True

        # 4️⃣ Text similarity
        if jaccard(new_words, normalize_set(old_text)) > text_threshold:
            return True

        # 5️⃣ Meaning similarity
        if meaning_similarity(new_meaning, meaning_signature(old_text)) > meaning_threshold:
            return True

    return False


def save_review_memory(
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