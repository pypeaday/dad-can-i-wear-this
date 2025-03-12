from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime
from .llm import get_clothing_recommendations

# Load environment variables from the root .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

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
        try:
            # Validate coordinates
            if 'coord' not in weather_data or not isinstance(weather_data['coord'], dict):
                print("Invalid coordinates in weather data")
                forecast = []
                return

            try:
                lat = float(weather_data['coord']['lat'])
                lon = float(weather_data['coord']['lon'])
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error parsing coordinates: {e}")
                forecast = []
                return
            
            # Fetch forecast data
            forecast_response = await client.get(
                "http://api.openweathermap.org/data/2.5/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "imperial"
                }
            )
            
            # Validate response
            if forecast_response.status_code != 200:
                print(f"Forecast API error: {forecast_response.status_code}")
                forecast = []
                return

            try:
                forecast_data = forecast_response.json()
            except Exception as e:
                print(f"Error parsing forecast response: {e}")
                forecast = []
                return
            
            if not isinstance(forecast_data, dict) or 'list' not in forecast_data:
                print("Invalid forecast data format")
                forecast = []
                return

            # Process forecast data for the next 24 hours
            forecast = []
            forecast_items = forecast_data.get('list', [])
            
            if not forecast_items:
                print("Empty forecast list")
                forecast = []
                return

            # Take first 8 items (24 hours, 3-hour intervals)
            for item in forecast_items[:8]:
                try:
                    # Validate data structure
                    if not isinstance(item, dict):
                        continue

                    main_data = item.get('main', {})
                    if not isinstance(main_data, dict):
                        continue

                    weather_list = item.get('weather', [])
                    if not isinstance(weather_list, list) or not weather_list:
                        continue

                    # Extract and validate temperature data
                    try:
                        temp = float(main_data.get('temp', 0))
                        feels_like = float(main_data.get('feels_like', 0))
                    except (ValueError, TypeError):
                        continue

                    # Skip invalid temperature values
                    if not (-100 <= temp <= 150) or not (-100 <= feels_like <= 150):
                        print(f"Invalid temperature values: temp={temp}, feels_like={feels_like}")
                        continue

                    # Format forecast point
                    forecast_point = {
                        'time': int(item.get('dt', 0)),
                        'temp': round(temp, 1),
                        'feels_like': round(feels_like, 1),
                        'description': str(weather_list[0].get('main', 'Unknown'))
                    }

                    # Validate forecast point
                    if forecast_point['time'] <= 0:
                        print("Invalid timestamp")
                        continue

                    forecast.append(forecast_point)

                except Exception as e:
                    print(f"Error processing forecast item: {e}")
                    continue

            if not forecast:
                print("No valid forecast data points found")

        except Exception as e:
            print(f"Error fetching forecast data: {e}")
            forecast = []
    
    # Extract weather data
    temp = weather_data["main"]["temp"]
    feels_like = weather_data["main"]["feels_like"]
    conditions = weather_data["weather"][0]["main"].lower()
    wind_speed = weather_data["wind"]["speed"]
    
    # Get current hour to determine time of day
    current_hour = datetime.now().hour
    time_of_day = "night" if current_hour < 6 or current_hour > 18 else "day"
    
    # Prepare weather data for LLM
    llm_data = {
        "temp": temp,
        "feels_like": feels_like,
        "conditions": conditions,
        "wind_speed": wind_speed,
        "time_of_day": time_of_day,
        "humidity": weather_data["main"]["humidity"],
        "location": weather_data["name"],
        "description": weather_data["weather"][0]["description"]
    }
    
    # Get AI-powered summary and recommendations
    summary, safety_recs, clothing_recs = await get_clothing_recommendations(llm_data)
        
    return templates.TemplateResponse(
        "weather_response.html",
        {
            "request": request,
            "temp": temp,
            "conditions": conditions.title(),
            "summary": summary,
            "safety_recommendations": safety_recs,
            "recommendations": clothing_recs,
            "forecast": forecast
        }
    )
