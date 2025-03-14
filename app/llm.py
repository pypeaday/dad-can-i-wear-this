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
env_path = root_dir / '.env'
load_dotenv(env_path)

# Get Ollama settings from environment or use defaults
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')

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
    temp = weather_data['temp']
    feels_like = weather_data['feels_like']
    conditions = weather_data['conditions']
    location = weather_data.get('location', '')
    
    # Add location if available
    location_text = f" in {location}" if location else ""
    
    # Add time of day context
    time_context = " tonight" if weather_data.get('time_of_day') == 'night' else " today"
    
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
        
        response = client.chat(model=OLLAMA_MODEL, messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        summary = response.message['content'].strip()
        return summary if summary else get_basic_weather_summary(weather_data)
    except Exception as e:
        print(f"Error getting weather summary: {e}")
        return get_basic_weather_summary(weather_data)

async def get_clothing_recommendations(weather_data: Dict) -> Tuple[str, List[str], List[str]]:
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
        prompt = f"""Based on these weather conditions and safety considerations, what specific clothing items should someone wear? 
Be practical and specific. Format each recommendation on a new line with an emoji.

IMPORTANT: ALWAYS include a specific recommendation for pants/shorts based on the temperature:
- Below 32°F: Heavy pants, thermal underwear
- 32-50°F: Long pants, possibly thermal for lower end
- 50-65°F: Long pants or jeans
- 65-75°F: Light pants or shorts depending on preference
- 75-85°F: Shorts or light pants
- Above 85°F: Shorts

All temperatures are in Fahrenheit (°F):
- Below 32°F is freezing (heavy winter clothing needed)
- 32-50°F is cold (winter coat, layers)
- 50-65°F is cool (light jacket or sweater)
- 65-75°F is mild (long sleeves or light layers)
- 75-85°F is warm (short sleeves)
- Above 85°F is hot (very light clothing)

Weather data:
{json.dumps(weather_data, indent=2)}

Safety considerations:
{json.dumps(safety_recs, indent=2)}

Clothing recommendations:"""
        
        response = client.chat(model=OLLAMA_MODEL, messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        # Parse the response and clean up
        ai_recs = [line.strip() for line in response.message['content'].split('\n') if line.strip()]
        
        # Ensure we have enough recommendations
        if len(ai_recs) >= 3:
            clothing_recs = ai_recs
        else:
            print("AI response too short, using standard recommendations")
            clothing_recs = safety.get_standard_recommendations(weather_data)
            
    except Exception as e:
        print(f"Error getting clothing recommendations: {e}")
        clothing_recs = safety.get_standard_recommendations(weather_data)
    
    # Periodically check if Ollama is still available
    check_ollama_available()
    
    return summary, safety_recs, clothing_recs
