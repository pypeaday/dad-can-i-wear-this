"""LLM-powered clothing recommendations and weather analysis using Ollama."""

from typing import Dict, List, Tuple
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from ollama import Client
import httpx
from . import safety

# Load environment variables from the root .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
load_dotenv(env_path)

# Get Ollama settings from environment or use defaults
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "dolphin3:latest")

# Configure Ollama client
client = Client(host=OLLAMA_HOST)

# Track Ollama availability
ollama_available = False


def check_ollama_available() -> bool:
    """Check if Ollama is running and available."""
    global ollama_available
    try:
        # Try to connect to Ollama's health endpoint
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=2.0)
        ollama_available = response.status_code == 200
        if ollama_available:
            print(f"Ollama is available at {OLLAMA_HOST}")
        else:
            print(f"Ollama returned status code {response.status_code}")
    except Exception as e:
        print(f"Ollama is not available: {e}")
        ollama_available = False
    return ollama_available


# Check Ollama availability on module load
check_ollama_available()


def get_basic_weather_summary(weather_data: Dict) -> str:
    """Generate a basic weather summary without using LLM."""
    temp = weather_data["temp"]
    feels_like = weather_data["feels_like"]
    conditions = weather_data["conditions"]
    location = weather_data.get("location", "")

    # Add location if available
    location_text = f" in {location}" if location else ""

    # Add time of day context
    time_context = (
        " tonight" if weather_data.get("time_of_day") == "night" else " today"
    )

    return f"It's {temp}°F{location_text}{time_context} (feels like {feels_like}°F) with {conditions}."


def get_weather_summary(weather_data: Dict) -> str:
    """Get an AI-generated summary of the weather conditions."""
    if not ollama_available:
        return get_basic_weather_summary(weather_data)

    try:
        prompt = f"""Given these weather conditions, create a natural, engaging weather summary that flows well.

Guidelines:
1. Start with a friendly greeting that includes the temperature and conditions
2. Add how it actually feels (using the "feels like" temperature)
3. Mention any notable weather factors (wind, humidity, etc.)
4. End with a brief mood-setting phrase about the day

Temperature Scale (°F):
• Below 32° → "frigid/freezing"
• 32-50° → "quite cold"
• 50-65° → "cool/crisp"
• 65-75° → "pleasant/mild"
• 75-85° → "warm/nice"
• Above 85° → "hot/very warm"

Weather data:
{json.dumps(weather_data, indent=2)}

Format your response as a flowing paragraph, not bullet points. Make it sound natural and conversational."""

        response = client.chat(
            model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}]
        )

        summary = response.message["content"].strip()
        return summary if summary else get_basic_weather_summary(weather_data)
    except Exception as e:
        print(f"Error getting weather summary: {e}")
        return get_basic_weather_summary(weather_data)


async def get_clothing_recommendations(
    weather_data: Dict,
) -> Tuple[str, List[str], List[str]]:
    """Get clothing recommendations and safety guidelines.

    Returns:
        Tuple containing:
        - Weather summary
        - Safety recommendations
        - Clothing recommendations
    """
    # Get weather summary (AI-powered if available, basic if not)
    summary = get_weather_summary(weather_data)

    # Get safety recommendations (these don't use LLM)
    safety_recs = safety.get_safety_recommendations(weather_data)

    # If Ollama isn't available, use standard recommendations
    if not ollama_available:
        clothing_recs = safety.get_standard_recommendations(weather_data)
        return summary, safety_recs, clothing_recs

    try:
        # Try to get AI-powered clothing recommendations
        prompt = f"""Based on these weather conditions and safety considerations, create clear, well-formatted clothing recommendations.

Format each recommendation like this:
👕 Base Layer: [recommendation]
👖 Bottoms: [recommendation]
🧥 Mid Layer: [recommendation] (if needed)
🧥 Outer Layer: [recommendation] (if needed)
🧤 Accessories: [recommendation]
👟 Footwear: [recommendation]

Guidelines:
• Start each item with an appropriate emoji
• Use clear, everyday language
• Only include layers needed for the weather
• Focus on both comfort and weather protection
• Keep descriptions concise but specific
• If certain layers aren't needed, skip them
• Consider both style and practicality

Weather data:
{json.dumps(weather_data, indent=2)}

Safety considerations:
{json.dumps(safety_recs, indent=2)}

Provide recommendations in the exact format shown above, maintaining consistent emoji usage and formatting."""

        response = client.chat(
            model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}]
        )

        # Get standard recommendations as a base
        standard_recs = safety.get_standard_recommendations(weather_data)

        # Parse the response and clean up
        ai_recs = [
            line.strip()
            for line in response.message["content"].split("\n")
            if line.strip()
        ]

        # Combine recommendations if AI provided enough suggestions
        if len(ai_recs) >= 3:
            # Create categories for organizing recommendations
            base_layer = []
            mid_layer = []
            outer_layer = []
            bottoms = []
            accessories = []
            footwear = []

            # Categorize standard recommendations
            for rec in standard_recs:
                if "Base layer" in rec:
                    base_layer.append(rec)
                elif "Mid layer" in rec:
                    mid_layer.append(rec)
                elif "Outer layer" in rec:
                    outer_layer.append(rec)
                elif "Bottoms" in rec:
                    bottoms.append(rec)
                elif any(
                    acc in rec.lower() for acc in ["scarf", "gloves", "hat", "umbrella"]
                ):
                    accessories.append(rec)
                elif any(foot in rec.lower() for foot in ["shoes", "boots"]):
                    footwear.append(rec)

            # Add AI recommendations to appropriate categories
            for rec in ai_recs:
                rec = rec.strip()
                if not rec:
                    continue

                # Categorize based on keywords
                if any(
                    base in rec.lower()
                    for base in ["base layer", "shirt", "t-shirt", "thermal"]
                ):
                    base_layer.append(rec)
                elif any(
                    mid in rec.lower() for mid in ["mid layer", "sweater", "fleece"]
                ):
                    mid_layer.append(rec)
                elif any(
                    outer in rec.lower() for outer in ["outer layer", "coat", "jacket"]
                ):
                    outer_layer.append(rec)
                elif any(
                    bottom in rec.lower() for bottom in ["pants", "shorts", "jeans"]
                ):
                    bottoms.append(rec)
                elif any(
                    acc in rec.lower() for acc in ["scarf", "gloves", "hat", "umbrella"]
                ):
                    accessories.append(rec)
                elif any(foot in rec.lower() for foot in ["shoes", "boots"]):
                    footwear.append(rec)
                else:
                    # If we can't categorize it, add to accessories as a catch-all
                    accessories.append(rec)

            # Combine all categories, removing duplicates while preserving emoji
            def remove_duplicates(items):
                seen = set()
                unique = []
                for item in items:
                    # Remove emoji for comparison
                    clean_item = "".join(c for c in item if c.isalnum()).lower()
                    if clean_item not in seen:
                        seen.add(clean_item)
                        unique.append(item)
                return unique

            clothing_recs = (
                remove_duplicates(base_layer)
                + remove_duplicates(bottoms)
                + remove_duplicates(mid_layer)
                + remove_duplicates(outer_layer)
                + remove_duplicates(accessories)
                + remove_duplicates(footwear)
            )
        else:
            print("AI response too short, using standard recommendations")
            clothing_recs = standard_recs

    except Exception as e:
        print(f"Error getting clothing recommendations: {e}")
        clothing_recs = safety.get_standard_recommendations(weather_data)

    # Periodically check if Ollama is still available
    check_ollama_available()

    return summary, safety_recs, clothing_recs
