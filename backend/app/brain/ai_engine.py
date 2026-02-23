# brain/ai_engine.py
import os
from app.core.openai_client import client

from app.brain.signal_ranker import rank_signals
from app.brain.prompt_builder import build_prompt
from app.brain.opening_engine import pick_opening
from app.brain.ending_engine import pick_ending

# 🔐 HARD ANTI-SPAM (fingerprint)
from app.brain.fingerprint_checker import (
    is_fingerprint_duplicate,
    save_fingerprint
)

# Phase-2 memory
from app.memory.memory_store import get_recent_reviews
from app.memory.narrative_usage import is_narrative_allowed, mark_narrative_used


NARRATIVES = [
    "Feeling → Service → Result",
    "Service → Moment → Feeling",
    "Problem → Relief → Afterthought",
    "Short & casual",
    "Busy customer style"
]


def generate_review(payload: dict):
    """
    REQUIRED:
    business_id
    industry
    rating
    language
    """

    business_id = payload["business_id"]
    industry = payload["industry"]
    rating = payload.get("rating", 4)
    shop_name = payload.get("shop_name")
    print("SHOP NAME RECEIVED:", payload.get("shop_name"))

    # ---------------- OPENING ----------------
    opening = pick_opening(
        business_id=business_id,
        industry=industry,
        rating=rating
    )

    # ---------------- OVERRIDES ----------------
    tone = payload.get("tone")
    verbosity = payload.get("verbosity")

    admin_data = payload.get("admin_data", {})

    # ---------------- SIGNAL RANKING (CONTROLLED PICK) ----------------
    ranked = rank_signals(
        product=payload.get("product"),
        area=payload.get("area"),
        admin_data=admin_data
    )

    # ---------------- SAFE DEFAULTS (CRITICAL) ----------------
    ranked.setdefault("context", [])
    ranked.setdefault("trust", [])
    ranked.setdefault("service", [])
    ranked.setdefault("area", [])
    ranked.setdefault("seo", [])

    # HARD LIMITS (industry safe)
    if ranked.get("context"):
        ranked["context"] = ranked["context"][:2]   # max 2 contexts
    
    if ranked.get("trust"):
        ranked["trust"] = ranked["trust"][:1]       # max 1 trust signal

    if ranked.get("service"):
        ranked["service"] = ranked["service"][:1]   # max 1 service

    if ranked.get("area"):
        ranked["area"] = ranked["area"][:1]         # max 1 area

    # ---------------- NARRATIVE ----------------
    narrative = None
    for n in NARRATIVES:
        if is_narrative_allowed(business_id, industry, n):
            narrative = n
            break

    if not narrative:
        narrative = NARRATIVES[0]

    # ---------------- PROMPT ----------------
    prompt = build_prompt(
        rating=rating,
        language=payload.get("language"),
        experience=payload.get("experience"),
        ranked=ranked,
        tone_override=tone,
        verbosity=verbosity,
        opening=opening
    )

    prompt += f"\n\nNarrative style:\n{narrative}"

    # ---------------- VERBOSITY HARD LIMIT ----------------
    if verbosity == 1:
        prompt += "\n\nWrite a very short review (20–30 words)."
    elif verbosity == 2:
        prompt += "\n\nWrite a short review (35–50 words)."
    elif verbosity == 3:
        prompt += "\n\nWrite a medium-length review (60–80 words)."
    elif verbosity == 4:
        prompt += "\n\nWrite a detailed review (90–120 words)."
    elif verbosity == 5:
        prompt += "\n\nWrite a long but natural review (130–160 words)."

    # ---------------- OPENAI CALL ----------------
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = res.choices[0].message.content

    # ---------------- VERBOSITY HARD LIMIT (PRODUCTION FIX) ----------------
    verbosity_limits = {
        1: 25,
        2: 45,
        3: 70,
        4: 110,
        5: 160
    }

    limit = verbosity_limits.get(verbosity, 70)

    words = text.split()
    if len(words) > limit:
        text = " ".join(words[:limit])
        if not text.endswith((".", "!", "?")):
            text = text.rstrip(", ") + "."

    # ---------------- APPLY OPENING ----------------
    text = opening + ". " + text.lstrip()

    shop_name = payload.get("shop_name")

    if shop_name:
        import random
        
        if random.random() < 0.4:
            sentences = text.split(". ")

            if len(sentences) >= 2:
                insert_at = len(sentences) // 2
                sentences[insert_at] = (
                    f"I recently visited {shop_name} and " + sentences[insert_at].lower()
                )

                text = ". ".join(sentences)

    # ---------------- HARD FINGERPRINT CHECK ----------------
    if is_fingerprint_duplicate(business_id, industry, text):
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\nRewrite completely with a different structure and flow."
                }
            ]
        )
        text = res.choices[0].message.content
        text = opening + ". " + text.lstrip()

    # ---------------- APPLY ENDING ----------------
    ending = pick_ending(business_id, industry, rating)
    text = text.rstrip(". ") + ". " + ending

    # ---------------- SOFT MEMORY CHECK ----------------
    recent = get_recent_reviews(business_id, industry)

    for r in recent:
        if r.get("review_text") and r["review_text"][:80] in text:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt + "\nRewrite with different wording and emotion."
                    }
                ]
            )
            text = res.choices[0].message.content
            text = opening + ". " + text.lstrip()
            text = text.rstrip(". ") + ". " + ending
            break

    # ---------------- SAVE MEMORY ----------------
    save_fingerprint(
        business_id=business_id,
        industry=industry,
        review_text=text
    )

    mark_narrative_used(
        business_id=business_id,
        industry=industry,
        narrative=narrative
    )

    return {
        "review": text,
        "debug": {
            "business_id": business_id,
            "industry": industry,
            "narrative": narrative,
            "tone_used": tone or "rating_based",
            "verbosity_used": verbosity or "default",
            "used_context": ranked.get("context"),
            "used_trust": ranked.get("trust"),
            "used_service": ranked.get("service"),
            "used_area": ranked.get("area"),
            "used_seo": ranked.get("seo")
        }
    }