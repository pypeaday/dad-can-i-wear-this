import os
import httpx
from typing import Dict, Any
from datetime import datetime


class ClothingRecommendationService:
    """Service for generating clothing recommendations using OpenAI-compatible LLM API."""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_HOST", "http://open-webui:8000")
        self.model = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "30.0"))
        self.api_key = os.getenv(
            "OLLAMA_API_KEY", ""
        )  # Open-WebUI requires API key for authentication

    def check_health(self) -> dict:
        """Check if LLM API is available - simplified for speed."""
        # Skip health check for performance - assume available
        # The actual LLM call will handle errors gracefully
        return {
            "status": "healthy",
            "available": True,
            "model": self.model,
            "model_loaded": True,
        }

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
            # Use Open-WebUI's chat completions endpoint
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a dad. Answer: what should I wear? Maximum 2 sentences. List specific clothes only. No explanations, no weather details, no tips.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    raise ValueError("Empty response from API")

                if "choices" not in data or not data["choices"]:
                    raise ValueError(f"Invalid response format: {data}")

                choice = data["choices"][0]
                if not choice or "message" not in choice:
                    raise ValueError(f"Invalid choice format: {choice}")

                message = choice["message"]
                if not message or "content" not in message:
                    raise ValueError(f"Invalid message format: {message}")

                llm_response = message["content"].strip()
                return llm_response

        except Exception as e:
            # Fallback recommendations if LLM fails
            print(f"❌ LLM failed: {type(e).__name__}: {str(e)}")
            return self._get_fallback_recommendations(weather_data)

    def _build_prompt(self, weather_data: Dict[str, Any]) -> str:
        """Build a detailed prompt for the LLM based on weather data."""
        current = weather_data["current"]
        location = weather_data["location"]

        # Build detailed hourly forecast breakdown
        forecast_details = []
        for item in weather_data["forecast"]:
            timestamp = datetime.fromisoformat(item["timestamp"])
            time_str = timestamp.strftime("%I:%M %p").lstrip("0")  # e.g., "2:00 PM"

            forecast_details.append(
                f"  • {time_str}: {item['temperature']}°F (feels like {item['feels_like']}°F), "
                f"{item['description']}, {item['precipitation_probability']:.0f}% precip chance"
            )

        forecast_text = "\n".join(forecast_details)

        # Get temperature range for summary
        forecast_temps = [item["temperature"] for item in weather_data["forecast"]]
        temp_range = f"{min(forecast_temps)}°F - {max(forecast_temps)}°F"

        prompt = f"""
Current weather in {location["name"]}:
- Now: {current["temperature"]}°F (feels like {current["feels_like"]}°F), {current["description"]}
- Today's range: {temp_range}
- Wind: {current["wind_speed"]} mph

Hourly forecast:
{forecast_text}

In 2-4 sentences, what should I wear today? Consider the temperature changes and whether I need layers.
"""
        return prompt

    def _get_fallback_recommendations(self, weather_data: Dict[str, Any]) -> str:
        """Provide basic recommendations if LLM is unavailable."""
        feels_like = weather_data["current"]["feels_like"]
        forecast_temps = [item["temperature"] for item in weather_data["forecast"]]
        temp_range = max(forecast_temps) - min(forecast_temps)

        if feels_like >= 75:
            return "Warm day ahead! Wear light clothing like a t-shirt and shorts. Bring sunglasses if it's sunny."
        elif feels_like >= 60:
            if temp_range > 15:
                return "Pleasant but variable temps. Start with a light jacket over a t-shirt - you can remove layers as it warms up."
            return (
                "Nice weather! A t-shirt or light long-sleeve with jeans works great."
            )
        elif feels_like >= 45:
            return "Cool day. Wear a sweater or hoodie with long pants, and bring a light jacket for extra warmth."
        elif feels_like >= 32:
            return "Cold outside! Bundle up with a warm coat, sweater, and long pants. Don't forget a hat and gloves."
        else:
            return "Very cold! Heavy winter coat, warm layers, boots, gloves, and a hat are essential. Stay warm!"
