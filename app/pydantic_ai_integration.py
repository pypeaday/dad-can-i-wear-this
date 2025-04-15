from pydantic_ai import Agent
from .models import WeatherSummary, ClothingRecommendations
from typing import Dict, List, Tuple

# Agent for weather summary
summary_agent = Agent[None, WeatherSummary](
    system_prompt="You are a helpful assistant for kids. Write a friendly, concise weather summary as a single paragraph, not a list. Include temperature, conditions, and any important notes."
)

# Agent for clothing recommendations
recommendations_agent = Agent[None, ClothingRecommendations](
    system_prompt="You are a helpful assistant for kids. Given weather and safety info, return clear, structured clothing and safety recommendations. Use emojis and concise, everyday language."
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
