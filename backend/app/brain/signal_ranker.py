# brain/signal_ranker.py

import random
import re

def normalize(text: str) -> set:
    """Lowercase + words set"""
    if not text:
        return set()
    words = re.findall(r"\w+", text.lower())
    return set(words)

def score_signal(base_words: set, signal: str) -> int:
    """How many words match"""
    signal_words = normalize(signal)
    return len(base_words & signal_words)

def rank_list(base_words: set, items: list, top_n=1):
    """Rank list by relevance score"""
    scored = []
    for item in items:
        score = score_signal(base_words, item)
        if score > 0:
            scored.append((item, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [item for item, _ in scored[:top_n]]

def rank_signals(product: str, area: str, admin_data: dict):
    """
    admin_data expects:
    {
      contexts: [],
      trust_signals: [],
      services: [],
      areas: [],
      seo_keywords: []
    }
    """

    # 🔹 Base meaning (user intent)
    base_text = f"{product or ''} {area or ''}"
    base_words = normalize(base_text)

    ranked = {}

    # 🔸 Context (most important)
    ranked["context"] = rank_list(
        base_words,
        admin_data.get("contexts", []),
        top_n=1
    )

    # 🔸 Trust signal (only 1, subtle)
    ranked["trust"] = rank_list(
        base_words,
        admin_data.get("trust_signals", []),
        top_n=1
    )

    # 🔸 Service / Product
    ranked["service"] = rank_list(
        base_words,
        admin_data.get("services", []),
        top_n=1
    )

    # 🔸 Area (local relevance)
    ranked["area"] = rank_list(
        base_words,
        admin_data.get("areas", []),
        top_n=1
    )

    # 🔸 SEO (NEVER force, random soft pick)
    seo = admin_data.get("seo_keywords", [])
    ranked["seo"] = random.sample(seo, 1) if seo else []

    return ranked