from pydantic_ai import Agent
from .models import WeatherSummary, ClothingRecommendations
from typing import Dict, List, Tuple

# Agent for weather summary (child-friendly, HTML list + Wear line)
summary_agent = Agent[None, WeatherSummary](
    system_prompt=(
        "You speak to a 5-year-old using tiny words. "
        "Given `weather` and a draft `summary`, return a very short HTML list with 3–5 bullets and one final Wear line.\n"
        "Rules:\n"
        "- Use <ul> with <li> bullets only (no paragraphs except final wear).\n"
        "- Each bullet under 8 words, simple words (warm, cold, rainy, windy).\n"
        "- Mention how it feels (hot/cold) and if wet/windy.\n"
        "- End with <p>Wear: ...</p> using simple items.\n"
        "- Do not mention exact times; use morning/afternoon/evening.\n"
    )
)

# Agent for clothing recommendations (child-friendly, concise, emoji categories)
recommendations_agent = Agent[None, ClothingRecommendations](
    system_prompt=(
        "You speak to a 5-year-old using tiny words. Given `weather`, `safety`, and current `clothing`, "
        "return up to 6 lines in this order, skipping lines not needed:\n"
        "👕 Base Layer: ...\n👖 Bottoms: ...\n🧥 Mid Layer: ...\n🧥 Outer Layer: ...\n🧤 Accessories: ...\n👟 Footwear: ...\n"
        "Rules:\n"
        "- Each line under 8 words, clear and concrete.\n"
        "- Start with the emoji and category exactly.\n"
        "- Match weather and safety (e.g., rain -> rain coat).\n"
        "- Use everyday items; skip fancy terms.\n"
    )
)

# Validate and generate summary using pydantic-ai
async def validate_summary_ai(weather_data: Dict, raw_summary: str) -> str:
    try:
        result = await summary_agent.run({"summary": raw_summary, "weather": weather_data})
        return result.output.summary
    except Exception:
        return raw_summary

# Validate/generate recommendations using pydantic-ai
async def validate_recommendations_ai(weather_data: Dict, safety: List[str], clothing: List[str]) -> Tuple[List[str], List[str]]:
    try:
        result = await recommendations_agent.run({"safety": safety, "clothing": clothing, "weather": weather_data})
        return result.output.safety, result.output.clothing
    except Exception:
        return safety, clothing
