import os
import ollama
from typing import Dict, Any

class ClothingRecommendationService:
    """Service for generating clothing recommendations using Ollama LLM."""
    
    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2:7b-instruct-q5_K_M")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "10.0"))
        
        # Initialize Ollama client
        self.client = ollama.Client(host=self.host)
    
    async def get_recommendations(self, weather_data: Dict[str, Any]) -> str:
        """
        Generate clothing recommendations based on weather data.
        
        Args:
            weather_data: Weather data from WeatherService
            
        Returns:
            String containing clothing recommendations
        """
        prompt = self._build_prompt(weather_data)
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful clothing advisor. Provide practical, specific clothing recommendations based on weather conditions. Be concise but thorough, focusing on comfort and appropriateness for the weather."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            )
            
            return response["message"]["content"].strip()
            
        except Exception as e:
            # Fallback recommendations if LLM fails
            return self._get_fallback_recommendations(weather_data)
    
    def _build_prompt(self, weather_data: Dict[str, Any]) -> str:
        """Build a detailed prompt for the LLM based on weather data."""
        current = weather_data["current"]
        location = weather_data["location"]
        
        # Get forecast summary
        forecast_temps = [item["temperature"] for item in weather_data["forecast"]]
        temp_range = f"{min(forecast_temps)}°F - {max(forecast_temps)}°F"
        
        # Check for precipitation
        precip_chances = [item["precipitation_probability"] for item in weather_data["forecast"]]
        max_precip = max(precip_chances) if precip_chances else 0
        
        prompt = f"""
Current weather in {location["name"]}:
- Temperature: {current["temperature"]}°F (feels like {current["feels_like"]}°F)
- Conditions: {current["description"]}
- Humidity: {current["humidity"]}%
- Wind: {current["wind_speed"]} mph

24-hour forecast:
- Temperature range: {temp_range}
- Max precipitation chance: {max_precip:.0f}%

Please recommend specific clothing items considering:
1. Current temperature and how it feels
2. Expected temperature changes throughout the day
3. Precipitation probability
4. Wind conditions
5. Humidity levels

Provide practical advice for someone asking "Dad, can I wear this?" Include specific clothing items and explain your reasoning briefly.
"""
        return prompt
    
    def _get_fallback_recommendations(self, weather_data: Dict[str, Any]) -> str:
        """Provide basic recommendations if LLM is unavailable."""
        current_temp = weather_data["current"]["temperature"]
        feels_like = weather_data["current"]["feels_like"]
        
        if feels_like >= 75:
            return "It's warm today! Light clothing recommended: t-shirt, shorts or light pants, and comfortable shoes. Consider sunglasses if sunny."
        elif feels_like >= 60:
            return "Pleasant weather! A light shirt or blouse with pants or jeans would be perfect. You might want a light jacket for later."
        elif feels_like >= 45:
            return "Cool weather. Wear a sweater or hoodie with long pants. Consider a light jacket if you'll be outside for long periods."
        elif feels_like >= 32:
            return "Cold weather! Bundle up with a warm coat, sweater, long pants, and closed-toe shoes. Don't forget gloves and a hat."
        else:
            return "Very cold! Wear heavy winter clothing: insulated coat, warm layers, winter boots, gloves, and a warm hat. Stay warm!"
