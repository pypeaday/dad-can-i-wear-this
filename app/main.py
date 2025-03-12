from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Dad, Can I Wear This?")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

DEFAULT_ZIP = os.getenv("DEFAULT_ZIP_CODE", "10001")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "default_zip": DEFAULT_ZIP}
    )

@app.post("/weather", response_class=HTMLResponse)
async def get_weather(request: Request, zip_code: str = Form(...)):
    async with httpx.AsyncClient() as client:
        # Get current weather
        current_response = await client.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={
                "zip": f"{zip_code},us",
                "appid": OPENWEATHER_API_KEY,
                "units": "imperial"
            }
        )
        weather_data = current_response.json()
        
        # Get forecast data
        lat = weather_data['coord']['lat']
        lon = weather_data['coord']['lon']
        forecast_response = await client.get(
            "http://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "imperial"
            }
        )
        forecast_data = forecast_response.json()
        
        # Process forecast data for the next 24 hours
        forecast = []
        for item in forecast_data['list'][:8]:  # 8 points = 24 hours (3-hour intervals)
            forecast.append({
                'time': item['dt'],
                'temp': item['main']['temp'],
                'feels_like': item['main']['feels_like'],
                'description': item['weather'][0]['main']
            })
        
    temp = weather_data["main"]["temp"]
    feels_like = weather_data["main"]["feels_like"]
    conditions = weather_data["weather"][0]["main"].lower()
    wind_speed = weather_data["wind"]["speed"]
    
    recommendations = []
    
    # Add temperature context
    if abs(temp - feels_like) > 5:
        recommendations.append(f"🌡️ It's {temp:.1f}°F but feels like {feels_like:.1f}°F")
    
    # Coat/Jacket recommendations
    if feels_like < 32:
        recommendations.append("❄️ You need a heavy winter coat today!")
    elif feels_like < 45:
        recommendations.append("🧥 Wear a warm coat!")
    elif feels_like < 60:
        recommendations.append("🧥 A light jacket or hoodie would be good.")
    elif feels_like < 70:
        recommendations.append("👕 A long-sleeve shirt should be fine. Maybe bring a light jacket just in case!")
    else:
        recommendations.append("👕 T-shirt weather! No coat needed.")
    
    # Hat recommendations
    if feels_like < 40 or (wind_speed > 15 and feels_like < 50):
        recommendations.append("🧢 Wear a warm hat - it's cold out there!")
    
    # Footwear recommendations
    if conditions in ["rain", "drizzle", "thunderstorm"]:
        recommendations.append("👢 Wear rain boots or waterproof shoes!")
    elif conditions == "snow":
        recommendations.append("❄️ Wear snow boots or waterproof shoes!")
    else:
        recommendations.append("👟 Regular shoes are fine today.")
    
    # Additional layers
    if feels_like < 50:
        recommendations.append("🧥 Layer up! Wear a sweater or sweatshirt under your coat.")
    elif feels_like < 65 and wind_speed > 10:
        recommendations.append("🌬️ It's a bit breezy - a sweatshirt would be good.")
    
    # Rain gear
    if conditions in ["rain", "drizzle", "thunderstorm"]:
        recommendations.append("☔ Bring an umbrella!")
        if wind_speed > 10:
            recommendations.append("🧥 A rain jacket might be better than an umbrella - it's windy!")
    
    # Extreme weather warnings
    if conditions == "thunderstorm":
        recommendations.append("⚡ Watch out for thunderstorms today!")
    elif conditions == "snow":
        recommendations.append("❄️ Dress warm - it's snowing!")
    elif wind_speed > 20:
        recommendations.append("💨 Very windy today - dress accordingly!")
        
    return templates.TemplateResponse(
        "weather_response.html",
        {
            "request": request,
            "temp": temp,
            "conditions": conditions,
            "recommendations": recommendations,
            "forecast": forecast
        }
    )
