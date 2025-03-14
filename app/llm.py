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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

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
        prompt = f"""Given these weather conditions, provide a brief, friendly summary in 2-3 sentences. 
Focus on how it feels and what to expect. Be conversational but informative.

IMPORTANT: All temperatures are in Fahrenheit (°F):
- Below 32°F is freezing
- 32-50°F is cold
- 50-65°F is cool
- 65-75°F is mild
- 75-85°F is warm
- Above 85°F is hot

Weather data:
{json.dumps(weather_data, indent=2)}

Summary:"""

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
        prompt = f"""Based on these weather conditions and safety considerations, recommend clothing using a layering system:
1. Base layer (against skin)
2. Mid layer (insulation)
3. Outer layer (weather protection)
4. Accessories (hat, gloves, etc.)

Format each recommendation on a new line with an emoji. Consider these temperature guidelines:

Base Layer:
- Below 30°F: Thermal underwear/heat tech
- 30-45°F: Long sleeve shirt
- Above 45°F: T-shirt/short sleeves

Bottoms:
- Below 32°F: Heavy pants with thermal layer
- 32-50°F: Long pants, possibly thermal
- 50-65°F: Long pants/jeans
- 65-75°F: Light pants or shorts
- 75-85°F: Shorts or very light pants
- Above 85°F: Shorts

Mid Layer (if needed):
- Below 40°F: Fleece/wool sweater
- 40-55°F: Light sweater
- Above 55°F: Optional based on preference

Outer Layer:
- Below 32°F: Heavy winter coat
- 32-45°F: Winter coat
- 45-60°F: Light jacket
- Above 60°F: Optional windbreaker if windy

Accessories:
- Below 40°F: Scarf, gloves, warm hat
- Above 75°F: Sun hat recommended

Weather data:
{json.dumps(weather_data, indent=2)}

Safety considerations:
{json.dumps(safety_recs, indent=2)}

Clothing recommendations:"""

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
