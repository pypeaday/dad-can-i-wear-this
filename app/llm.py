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

        # Get standard recommendations as a base set
        clothing_recs = standard_recs.copy()

        # Parse and clean up AI response
        ai_recs = [
            line.strip()
            for line in response.message["content"].split("\n")
            if line.strip()
        ]

        # Helper function to extract emoji from a string
        def extract_emoji(text):
            return "".join(c for c in text if not c.isalnum() and not c.isspace())

        # Helper function to clean text for comparison
        def clean_text(text):
            return "".join(c.lower() for c in text if c.isalnum())

        # Process AI recommendations
        for ai_rec in ai_recs:
            ai_rec = ai_rec.strip()
            if not ai_rec:
                continue

            # Extract emoji if present, otherwise use a default
            emoji = extract_emoji(ai_rec) or "👕 "

            # Clean up the recommendation text
            clean_ai_rec = clean_text(ai_rec)

            # Check if this recommendation is unique
            is_unique = True
            for i, std_rec in enumerate(clothing_recs):
                if clean_text(std_rec) == clean_ai_rec:
                    # Update existing recommendation with AI version if it has emoji
                    if emoji and not extract_emoji(std_rec):
                        clothing_recs[i] = ai_rec
                    is_unique = False
                    break

            # Add new unique recommendations
            if is_unique:
                # Ensure recommendation has proper formatting
                if not any(
                    category in ai_rec.lower()
                    for category in [
                        "layer",
                        "bottoms",
                        "accessories",
                        "footwear",
                        "shoes",
                        "boots",
                    ]
                ):
                    # Add appropriate category if missing
                    if any(
                        item in clean_ai_rec for item in ["shirt", "thermal", "tshirt"]
                    ):
                        ai_rec = (
                            f"{emoji}Base Layer: {ai_rec.split(':', 1)[-1].strip()}"
                        )
                    elif any(
                        item in clean_ai_rec for item in ["pants", "shorts", "jeans"]
                    ):
                        ai_rec = f"{emoji}Bottoms: {ai_rec.split(':', 1)[-1].strip()}"
                    elif any(item in clean_ai_rec for item in ["sweater", "fleece"]):
                        ai_rec = f"{emoji}Mid Layer: {ai_rec.split(':', 1)[-1].strip()}"
                    elif any(item in clean_ai_rec for item in ["coat", "jacket"]):
                        ai_rec = (
                            f"{emoji}Outer Layer: {ai_rec.split(':', 1)[-1].strip()}"
                        )
                    elif any(
                        item in clean_ai_rec
                        for item in ["scarf", "gloves", "hat", "umbrella"]
                    ):
                        ai_rec = (
                            f"{emoji}Accessories: {ai_rec.split(':', 1)[-1].strip()}"
                        )
                    elif any(item in clean_ai_rec for item in ["shoes", "boots"]):
                        ai_rec = f"{emoji}Footwear: {ai_rec.split(':', 1)[-1].strip()}"

                clothing_recs.append(ai_rec)

        # Ensure we have at least one recommendation for each essential category
        categories = {
            "Base Layer": "👕 Base Layer: Appropriate for the weather",
            "Bottoms": "👖 Bottoms: Appropriate for the weather",
            "Footwear": "👟 Footwear: Appropriate shoes for the conditions",
        }

        for category, default_rec in categories.items():
            if not any(category.lower() in rec.lower() for rec in clothing_recs):
                clothing_recs.append(default_rec)

        # Sort recommendations by category
        category_order = [
            "Base Layer",
            "Bottoms",
            "Mid Layer",
            "Outer Layer",
            "Accessories",
            "Footwear",
        ]
        clothing_recs.sort(
            key=lambda x: next(
                (i for i, cat in enumerate(category_order) if cat.lower() in x.lower()),
                len(category_order),
            )
        )

    except Exception as e:
        print(f"Error getting clothing recommendations: {e}")
        clothing_recs = safety.get_standard_recommendations(weather_data)

    # Periodically check if Ollama is still available
    check_ollama_available()

    return summary, safety_recs, clothing_recs
