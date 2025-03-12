"""LLM-powered clothing recommendations and weather analysis using Ollama."""

from typing import Dict, List, Tuple
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from ollama import Client
from . import safety

# Load environment variables from the root .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Get Ollama settings from environment or use defaults
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')

print(f"Using Ollama model: {OLLAMA_MODEL} at {OLLAMA_HOST}")

# Configure Ollama client
client = Client(host=OLLAMA_HOST)

def get_weather_summary(weather_data: Dict) -> str:
    """Get an AI-generated summary of the weather conditions."""
    try:
        prompt = f"""Given these weather conditions, provide a brief, friendly summary in 2-3 sentences. 
Focus on how it feels and what to expect. Be conversational but informative.

Weather data:
{json.dumps(weather_data, indent=2)}

Summary:"""
        
        response = client.chat(model=OLLAMA_MODEL, messages=[{
            'role': 'user',
            'content': prompt
        }])
        
        return response.message['content'].strip()
    except Exception as e:
        print(f"Error getting weather summary: {e}")
        # Fallback to a basic summary if LLM fails
        temp = weather_data['temp']
        feels_like = weather_data['feels_like']
        conditions = weather_data['conditions']
        return f"It's {temp}°F (feels like {feels_like}°F) with {conditions}."

async def get_clothing_recommendations(weather_data: Dict) -> Tuple[str, List[str], List[str]]:
    """Get clothing recommendations and safety guidelines.
    
    Returns:
        Tuple containing:
        - Weather summary
        - Safety recommendations
        - Clothing recommendations
    """
    # Get AI-powered weather summary
    summary = get_weather_summary(weather_data)
    
    # Get safety recommendations
    safety_recs = safety.get_safety_recommendations(weather_data)
    
    try:
        # Try to get AI-powered clothing recommendations
        prompt = f"""Based on these weather conditions and safety considerations, what specific clothing items should someone wear? 
Be practical and specific. Format each recommendation on a new line with an emoji.

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
        
        # Fallback to standard recommendations if AI response is too short
        if len(ai_recs) < 3:
            clothing_recs = safety.get_standard_recommendations(weather_data)
        else:
            clothing_recs = ai_recs
            
    except Exception as e:
        print(f"Error getting clothing recommendations: {e}")
        # Fallback to standard recommendations if LLM fails
        clothing_recs = safety.get_standard_recommendations(weather_data)
    
    return summary, safety_recs, clothing_recs
