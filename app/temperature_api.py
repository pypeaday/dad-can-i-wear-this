from fastapi import APIRouter
from fastapi.responses import JSONResponse
import httpx
import os
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


@router.get("/api/temperature-data/{zip_code}")
async def get_temperature_data(zip_code: str):
    """API endpoint to get temperature chart data for a specific zip code"""
    async with httpx.AsyncClient() as client:
        # Get current weather
        current_response = await client.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={
                "zip": f"{zip_code},us",
                "appid": OPENWEATHER_API_KEY,
                "units": "imperial",
            },
        )
        
        if current_response.status_code != 200:
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to fetch weather data"}
            )
        
        weather_data = current_response.json()
        
        # Get forecast data
        try:
            lat = float(weather_data["coord"]["lat"])
            lon = float(weather_data["coord"]["lon"])
            
            forecast_response = await client.get(
                "http://api.openweathermap.org/data/2.5/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "imperial",
                    "cnt": 40,
                },
            )
            
            if forecast_response.status_code != 200:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Failed to fetch forecast data"}
                )
            
            forecast_data = forecast_response.json()
            
            # Process forecast data for chart
            chart_data = []
            now = datetime.now(ZoneInfo("America/New_York"))
            today = now.date()
            
            # Add current weather point
            current_temp = weather_data.get("main", {}).get("temp")
            current_feels = weather_data.get("main", {}).get("feels_like")
            current_time = datetime.fromtimestamp(
                weather_data.get("dt", 0), tz=ZoneInfo("America/New_York")
            )
            
            chart_data.append({
                "time": current_time.strftime("%H:%M"),
                "timestamp": weather_data.get("dt", 0) * 1000,
                "temp": round(float(current_temp), 1),
                "feels_like": round(float(current_feels), 1),
                "is_current": True
            })
            
            # Add forecast points for today
            for item in forecast_data.get("list", []):
                timestamp = item.get("dt", 0)
                if timestamp <= 0:
                    continue
                    
                forecast_time = datetime.fromtimestamp(
                    timestamp, tz=ZoneInfo("America/New_York")
                )
                
                # Only include today's data
                if forecast_time.date() == today:
                    temp = item.get("main", {}).get("temp")
                    feels_like = item.get("main", {}).get("feels_like")
                    
                    if temp is not None and feels_like is not None:
                        chart_data.append({
                            "time": forecast_time.strftime("%H:%M"),
                            "timestamp": timestamp * 1000,
                            "temp": round(float(temp), 1),
                            "feels_like": round(float(feels_like), 1),
                            "is_current": False
                        })
            
            # Sort by timestamp
            chart_data.sort(key=lambda x: x["timestamp"])
            
            return JSONResponse(content={
                "location": weather_data.get("name", "Unknown"),
                "data": chart_data
            })
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Error processing forecast data: {str(e)}"}
            )
