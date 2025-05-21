"""LLM-powered clothing recommendations and weather analysis using Ollama."""

from typing import Dict, List, Tuple
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from ollama import Client
import httpx
from . import safety
from .pydantic_ai_integration import validate_summary_ai, validate_recommendations_ai

# Load environment variables from the root .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
load_dotenv(env_path)

# Get Ollama settings from environment or use defaults
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "dolphin3:latest")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "5.0"))

# Configure Ollama client
client = Client(host=OLLAMA_HOST)

# Track Ollama availability
ollama_available = False


def check_ollama_available() -> bool:
    """Check if Ollama is running and available."""
    global ollama_available
    print(f"\n[INFO] Attempting to connect to Ollama at {OLLAMA_HOST}")
    
    # Try with timeout from environment and multiple attempts
    max_attempts = 3
    timeout_seconds = OLLAMA_TIMEOUT
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[INFO] Connection attempt {attempt}/{max_attempts} with {timeout_seconds}s timeout")
            
            # Try to connect to Ollama's health endpoint
            response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=timeout_seconds)
            
            if response.status_code == 200:
                ollama_available = True
                print(f"[SUCCESS] Ollama is available at {OLLAMA_HOST}")
                # Print available models
                try:
                    models = response.json()
                    print(f"[INFO] Available models: {models}")
                except Exception as json_err:
                    print(f"[WARNING] Could not parse models list: {json_err}")
                return True
            else:
                print(f"[ERROR] Ollama returned status code {response.status_code}")
                print(f"[DEBUG] Response content: {response.text[:200]}...")
        except httpx.ConnectError as e:
            print(f"[ERROR] Connection error to {OLLAMA_HOST}: {e}")
            print(f"[INFO] Make sure the Ollama server is running and accessible from this container")
        except httpx.TimeoutError:
            print(f"[ERROR] Connection timeout to {OLLAMA_HOST} after {timeout_seconds} seconds")
        except Exception as e:
            print(f"[ERROR] Unexpected error connecting to Ollama: {e}")
        
        # Only sleep between attempts, not after the last one
        if attempt < max_attempts:
            import time
            print(f"[INFO] Waiting 2 seconds before retry...")
            time.sleep(2)
    
    # If we get here, all attempts failed
    print(f"[CRITICAL] Failed to connect to Ollama at {OLLAMA_HOST} after {max_attempts} attempts")
    print(f"[INFO] The application will continue with basic weather summaries only")
    ollama_available = False
    return False


# Check Ollama availability on module load
print("\n[INFO] Checking Ollama availability on startup...")
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
    """Get a comprehensive AI-generated weather summary for the entire day."""
    if not ollama_available:
        return get_basic_weather_summary(weather_data)

    try:
        # Get forecast data
        forecast_data = weather_data.get('forecast', [])
        print(f"\n[DEBUG] Processing daily forecast")
        print(f"[DEBUG] Found {len(forecast_data)} total forecast points")
        
        # Process forecast data to get temperature and condition trends throughout the day
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        
        # Get current time and date
        now = datetime.now(ZoneInfo("America/New_York"))
        today = now.date()
        current_hour = now.hour
        print(f"[DEBUG] Current date/time: {now}, Today: {today}, Current hour: {current_hour}")
        
        # Define time periods for the day
        morning_hours = (5, 12)  # 5 AM to 12 PM
        afternoon_hours = (12, 18)  # 12 PM to 6 PM
        evening_hours = (18, 23)  # 6 PM to 11 PM
        
        # Filter forecast points for today
        today_forecast = []
        if forecast_data:
            for point in forecast_data:
                timestamp = point.get("time", 0)
                if timestamp == 0:
                    continue
                    
                try:
                    point_time = datetime.fromtimestamp(timestamp / 1000, tz=ZoneInfo("America/New_York"))
                    
                    # Only include points for today
                    if point_time.date() == today:
                        today_forecast.append({
                            "time": point_time,
                            "hour": point_time.hour,
                            "temp": point.get("temp", 0),
                            "feels_like": point.get("feels_like", 0),
                            "description": point.get("description", "").lower()
                        })
                except Exception as e:
                    print(f"[DEBUG] Error processing timestamp {timestamp}: {e}")
        
        # Sort forecast by hour
        today_forecast.sort(key=lambda x: x["hour"])
        
        # Extract data for each time period
        morning_data = [p for p in today_forecast if morning_hours[0] <= p["hour"] < morning_hours[1]]
        afternoon_data = [p for p in today_forecast if afternoon_hours[0] <= p["hour"] < afternoon_hours[1]]
        evening_data = [p for p in today_forecast if evening_hours[0] <= p["hour"] < evening_hours[1]]
        
        # Get temperature ranges and conditions for each period
        periods_data = {}
        
        # Helper function to extract period data
        def extract_period_data(period_points, period_name):
            if not period_points:
                return None
                
            temps = [p["temp"] for p in period_points]
            min_temp = round(min(temps))
            max_temp = round(max(temps))
            
            if min_temp == max_temp:
                temp_range = f"{min_temp}°F"
            else:
                temp_range = f"{min_temp}-{max_temp}°F"
                
            # Get unique weather conditions
            conditions = list(set(p["description"] for p in period_points))
            
            # Get temperature trend (rising, falling, steady)
            if len(temps) > 1:
                first_temp = temps[0]
                last_temp = temps[-1]
                if last_temp - first_temp > 3:
                    trend = "rising"
                elif first_temp - last_temp > 3:
                    trend = "falling"
                else:
                    trend = "steady"
            else:
                trend = "steady"
                
            return {
                "temp_range": temp_range,
                "conditions": conditions,
                "trend": trend,
                "points": len(period_points)
            }
        
        # Extract data for each period
        if morning_data:
            periods_data["morning"] = extract_period_data(morning_data, "morning")
            print(f"[DEBUG] Morning data: {periods_data['morning']}")
        
        if afternoon_data:
            periods_data["afternoon"] = extract_period_data(afternoon_data, "afternoon")
            print(f"[DEBUG] Afternoon data: {periods_data['afternoon']}")
        
        if evening_data:
            periods_data["evening"] = extract_period_data(evening_data, "evening")
            print(f"[DEBUG] Evening data: {periods_data['evening']}")
            
        # Determine which periods to include based on current time
        periods_to_include = []
        
        if current_hour < morning_hours[0]:  # Before morning
            periods_to_include = ["morning", "afternoon", "evening"]
        elif current_hour < morning_hours[1]:  # During morning
            periods_to_include = ["morning", "afternoon", "evening"]
        elif current_hour < afternoon_hours[1]:  # During afternoon
            periods_to_include = ["afternoon", "evening"]
        elif current_hour < evening_hours[1]:  # During evening
            periods_to_include = ["evening"]
        
        # Filter periods data to only include relevant periods
        relevant_periods = {k: v for k, v in periods_data.items() if k in periods_to_include and v is not None}
        
        # Create a prompt for the LLM to generate a comprehensive daily forecast with bullet points
        prompt = f"""Create a concise, bullet-point weather forecast that describes how the weather will change throughout the day. 

Current conditions: {weather_data['temp']}°F (feels like {weather_data['feels_like']}°F) with {weather_data['conditions']}.

Forecast data for today:
{json.dumps(relevant_periods, indent=2)}

Guidelines:
1. Use BULLET POINTS for each key piece of information (not paragraphs)
2. Be SPECIFIC about temperature trends (rising, falling, steady)
3. Be SPECIFIC about weather conditions and when they might change
4. Focus on what's most relevant based on the current time ({current_hour}:00)
5. Make it practical for someone deciding what to wear
6. Include wind, precipitation, or other notable factors if present
7. Keep each bullet point SHORT and FOCUSED (5-10 words when possible)

Format your response with clear sections for each part of the day that's still relevant:
- If it's morning or earlier, include sections for morning, afternoon, and evening
- If it's afternoon, include sections for afternoon and evening
- If it's evening, just include the evening section

Use this format with HTML tags:
<h3>This Morning</h3>
<ul>
  <li>Temperature: 45-52°F, rising throughout morning</li>
  <li>Conditions: Light rain until 10am</li>
  <li>Wind: Light, 5-10 mph</li>
</ul>

<h3>This Afternoon</h3>
<ul>
  <li>Temperature: 52-58°F, steady</li>
  <li>Conditions: Partly cloudy</li>
  <li>Wind: Moderate, 10-15 mph</li>
</ul>

<h3>This Evening</h3>
<ul>
  <li>Temperature: 48-52°F, falling after sunset</li>
  <li>Conditions: Clear skies</li>
  <li>Wind: Light, 5 mph</li>
</ul>

Only include sections for times that are still relevant based on the current time ({current_hour}:00).
"""

        # Get the forecast from the LLM
        response = client.chat(
            model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}]
        )

        summary = response.message["content"].strip()
        print(f"[DEBUG] LLM response length: {len(summary)}")
        print(f"[DEBUG] LLM response preview: {summary[:100]}...")
        
        # If the LLM didn't return HTML formatted content, add basic formatting
        if "<h3>" not in summary:
            print("[DEBUG] Adding HTML formatting to LLM response")
            # Split by newlines and look for section headers
            lines = summary.split('\n')
            formatted_lines = []
            in_bullet_list = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("This Morning") or line.startswith("This Afternoon") or line.startswith("This Evening"):
                    # Close any open list before starting a new section
                    if in_bullet_list:
                        formatted_lines.append("</ul>")
                        in_bullet_list = False
                    formatted_lines.append(f"<h3>{line}</h3>")
                    # Start a new bullet list
                    formatted_lines.append("<ul>")
                    in_bullet_list = True
                elif line.startswith("-") or line.startswith("*"):
                    # This is a bullet point
                    if not in_bullet_list:
                        formatted_lines.append("<ul>")
                        in_bullet_list = True
                    # Remove the bullet character and format as list item
                    bullet_text = line[1:].strip()
                    formatted_lines.append(f"<li>{bullet_text}</li>")
                else:
                    # Regular text
                    if in_bullet_list:
                        # If we were in a list but this isn't a bullet point, close the list
                        formatted_lines.append("</ul>")
                        in_bullet_list = False
                    formatted_lines.append(f"<p>{line}</p>")
            
            # Close any open list at the end
            if in_bullet_list:
                formatted_lines.append("</ul>")
                
            summary = "\n".join(formatted_lines)
        
        return summary if summary else get_basic_weather_summary(weather_data)
    except Exception as e:
        print(f"Error getting weather summary: {e}")
        import traceback
        traceback.print_exc()
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
    print(f"[DEBUG] Generated weather summary: {summary[:100]}...")
    
    # Skip validation for HTML content as it will strip the HTML tags
    # Only validate if it's a basic summary (no HTML tags)
    if "<h3>" not in summary and "<p>" not in summary:
        summary = await validate_summary_ai(weather_data, summary)
        print("[DEBUG] Validated basic summary with pydantic-ai")
    else:
        print("[DEBUG] Skipping validation for HTML summary to preserve formatting")

    # Get safety recommendations (these don't use LLM)
    safety_recs = safety.get_safety_recommendations(weather_data)

    # If Ollama isn't available, use standard recommendations
    if not ollama_available:
        clothing_recs = safety.get_standard_recommendations(weather_data)
        # Validate recommendations with pydantic-ai
        _, clothing_recs = await validate_recommendations_ai(weather_data, safety_recs, clothing_recs)
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

        # Parse LLM output (basic split, could improve)
        clothing_recs = [line.strip() for line in response['message']['content'].split('\n') if line.strip() and any(c in line for c in [':','Base Layer','Bottoms','Outer Layer','Accessories','Footwear'])]
        # Validate recommendations with pydantic-ai
        _, clothing_recs = await validate_recommendations_ai(weather_data, safety_recs, clothing_recs)
        return summary, safety_recs, clothing_recs
    except Exception as e:
        print(f"Error getting AI-powered clothing recommendations: {e}")
        clothing_recs = safety.get_standard_recommendations(weather_data)
        _, clothing_recs = await validate_recommendations_ai(weather_data, safety_recs, clothing_recs)
        return summary, safety_recs, clothing_recs

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
