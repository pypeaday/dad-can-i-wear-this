import os
import httpx
from typing import Dict, Any, List
from datetime import datetime, timezone

class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable is required")
        
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_weather_data(self, zip_code: str) -> Dict[str, Any]:
        """
        Fetch current weather and 24-hour forecast for the given ZIP code.
        
        Args:
            zip_code: ZIP code to get weather for
            
        Returns:
            Dictionary containing current weather and forecast data
        """
        async with httpx.AsyncClient() as client:
            # Get current weather
            current_response = await client.get(
                f"{self.base_url}/weather",
                params={
                    "zip": zip_code,
                    "appid": self.api_key,
                    "units": "imperial"
                }
            )
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Get 5-day forecast (we'll use first 24 hours)
            forecast_response = await client.get(
                f"{self.base_url}/forecast",
                params={
                    "zip": zip_code,
                    "appid": self.api_key,
                    "units": "imperial"
                }
            )
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Process and return structured data
            return self._process_weather_data(current_data, forecast_data)
    
    def _process_weather_data(self, current: Dict[str, Any], forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw API data into structured format."""
        
        # Extract current weather
        current_weather = {
            "temperature": round(current["main"]["temp"]),
            "feels_like": round(current["main"]["feels_like"]),
            "humidity": current["main"]["humidity"],
            "description": current["weather"][0]["description"].title(),
            "wind_speed": current["wind"]["speed"],
            "wind_direction": current["wind"].get("deg", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Extract forecast data (next 24 hours)
        forecast_list = []
        current_time = datetime.now(timezone.utc)
        
        for item in forecast["list"][:8]:  # 8 items = 24 hours (3-hour intervals)
            forecast_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            
            forecast_list.append({
                "timestamp": forecast_time.isoformat(),
                "temperature": round(item["main"]["temp"]),
                "feels_like": round(item["main"]["feels_like"]),
                "humidity": item["main"]["humidity"],
                "description": item["weather"][0]["description"].title(),
                "precipitation_probability": item.get("pop", 0) * 100,  # Convert to percentage
                "wind_speed": item["wind"]["speed"]
            })
        
        return {
            "location": {
                "name": forecast["city"]["name"],
                "country": forecast["city"]["country"]
            },
            "current": current_weather,
            "forecast": forecast_list,
            "generated_at": current_time.isoformat()
        }
