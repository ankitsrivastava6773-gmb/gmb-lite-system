# brain/prompt_builder.py

def rating_tone(rating: int):
    if rating >= 5:
        return "very positive and happy"
    if rating == 4:
        return "positive but natural"
    if rating == 3:
        return "neutral and honest"
    return "calm and factual"

def verbosity_hint(level: int | None):
    if not level:
        return "medium length"
    if level <= 2:
        return "short and crisp"
    if level == 3:
        return "balanced length"
    return "detailed but natural"

def build_prompt(
    rating: int,
    language: str,
    experience: str | None,
    ranked: dict,
    tone_override: str | None = None,
    verbosity: int | None = None,
    opening: str | None = None
):
    tone = tone_override or rating_tone(rating)
    length_style = verbosity_hint(verbosity)

    context = ranked.get("context", [])
    trust = ranked.get("trust", [])
    service = ranked.get("service", [])
    area = ranked.get("area", [])
    seo = ranked.get("seo", [])

    prompt = f"""
Start the review naturally like this:
"{opening}"

Continue naturally as a real human would.

Write a REAL human Google review.

Language: {language}
Rating: {rating} stars
Tone: {tone}
Length: {length_style}

Rules:
- First person only
- No marketing language
- No emojis
- Natural imperfections allowed
- Do NOT sound promotional

Context (use only if natural):
{context[0] if context else "None"}

Service / Product:
{service[0] if service else "None"}

Trust signal (implicit):
{trust[0] if trust else "None"}

Area hint:
{area[0] if area else "None"}

SEO hint (max one, subtle):
{seo[0] if seo else "None"}

User experience:
{experience if experience else "Not specified"}

Write like a real customer.
"""
    return prompt.strip()