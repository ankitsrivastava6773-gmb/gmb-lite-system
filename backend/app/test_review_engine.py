import random
from datetime import datetime

OPENINGS = [
    "Honestly,", "Overall,", "Just sharing my experience,",
    "Wanted to mention,", "Quick note —"
]

NARRATIVES = [
    "Feeling → Service → Result",
    "Service → Moment → Feeling",
    "Problem → Relief → Afterthought",
    "Short & casual"
]

ENDINGS = [
    "Would visit again.",
    "Felt worth it.",
    "Happy with the experience.",
    "Glad I came here."
]

def generate_review_test(
    product,
    area,
    rating,
    language="English"
):
    opening = random.choice(OPENINGS)
    narrative = random.choice(NARRATIVES)
    ending = random.choice(ENDINGS)

    body = f"""
I tried {product} in {area}.
The experience felt natural and smooth.
Nothing felt forced or fake.
"""

    review = f"{opening} {body.strip()} {ending}"

    return {
        "review": review,
        "meta": {
            "rating": rating,
            "narrative": narrative,
            "generated_at": datetime.utcnow().isoformat()
        }
    }