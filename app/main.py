from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.templating import _TemplateResponse
import httpx
from pathlib import Path
import os
import random
import tomli
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from .llm import get_clothing_recommendations


# Load version from pyproject.toml
def get_version():
    try:
        with open(Path(__file__).resolve().parent.parent / "pyproject.toml", "rb") as f:
            return tomli.load(f)["project"]["version"]
    except Exception:
        return "unknown"


# Load environment variables from the root .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
load_dotenv(env_path)

VERSION = get_version()
app = FastAPI(title="Dad, Can I Wear This?", version=VERSION)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


DEFAULT_ZIP = os.getenv("DEFAULT_ZIP_CODE", "10001")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "default_zip": DEFAULT_ZIP, "version": VERSION},
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
                "units": "imperial",
            },
        )
        weather_data = current_response.json()

        # Get forecast data
        try:
            # Validate coordinates
            if "coord" not in weather_data or not isinstance(
                weather_data["coord"], dict
            ):
                print("Invalid coordinates in weather data")
                forecast = []
                return

            try:
                lat = float(weather_data["coord"]["lat"])
                lon = float(weather_data["coord"]["lon"])
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error parsing coordinates: {e}")
                forecast = []
                return

            # Fetch forecast data using 5-day/3-hour forecast API
            forecast_response = await client.get(
                "http://api.openweathermap.org/data/2.5/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "imperial",
                    "cnt": 40,  # Get maximum number of points (5 days)
                },
            )

            # Debug logging
            print("Fetching forecast data from OpenWeatherMap API...")

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

            if not isinstance(forecast_data, dict) or "list" not in forecast_data:
                print("Invalid forecast data format")
                forecast = []
                return

            # Process forecast data
            forecast = []
            forecast_items = forecast_data.get("list", [])

            if not forecast_items:
                print("Empty forecast list")
                forecast = []
                return

            # Get current time and date in ET
            now = datetime.now(ZoneInfo("America/New_York"))
            today = now.date()

            # Sort forecast items by timestamp to ensure chronological order
            forecast_items.sort(key=lambda x: x.get("dt", 0))

            # Add a small random variation to each forecast point to create more natural-looking data
            # This is for visualization purposes only and helps avoid flat lines
            random.seed(today.toordinal())  # Use consistent seed based on date

            # Debug logging for forecast data
            print("\nRaw forecast data from OpenWeatherMap API (3-hour intervals):")
            print("----------------------------------------")
            print("Note: API returns forecast points every 3 hours")
            print("Timezone: America/New_York")

            # Print all forecast times to debug
            print("\nAll forecast times from API:")
            for item in forecast_items:
                timestamp = item.get("dt", 0)
                if timestamp > 0:
                    forecast_time = datetime.fromtimestamp(
                        timestamp, tz=ZoneInfo("America/New_York")
                    )
                    print(f"  * {forecast_time.strftime('%Y-%m-%d %I:%M %p')}")
            print("Today's date:", today)
            print("Current time:", now.strftime("%I:%M %p"))
            print("\nAll available forecast points:")
            for item in forecast_items:
                dt = datetime.fromtimestamp(
                    item.get("dt", 0), tz=ZoneInfo("America/New_York")
                )
                temp = item.get("main", {}).get("temp")
                feels_like = item.get("main", {}).get("feels_like")
                print(
                    f"- {dt.strftime('%Y-%m-%d %I:%M %p')}: {temp}°F (feels like {feels_like}°F)"
                )

            # Initialize forecast list with current weather
            current_time = datetime.fromtimestamp(
                weather_data.get("dt", 0), tz=ZoneInfo("America/New_York")
            )
            current_temp = weather_data.get("main", {}).get("temp")
            current_feels = weather_data.get("main", {}).get("feels_like")

            print("\nCurrent conditions:")
            print(f"Time: {current_time.strftime('%I:%M %p')}")
            print(f"Temperature: {current_temp}°F")
            print(f"Feels like: {current_feels}°F")

            # Initialize forecast list
            forecast = []

            # Track all hours we have data for (to detect gaps)
            hours_with_data = set()

            # Always add current weather data (the chart will filter by time window)
            forecast.append(
                {
                    "time": weather_data.get("dt", 0) * 1000,
                    "temp": round(float(current_temp), 1),
                    "feels_like": round(float(current_feels), 1),
                    "description": weather_data.get("weather", [{}])[0].get(
                        "main", "Unknown"
                    ),
                }
            )
            print("[Added current conditions to data set]")

            print("\nProcessing forecast points (3-hour intervals):")
            for item in forecast_items:
                try:
                    # Get timestamp and convert to ET
                    timestamp = item.get("dt", 0)
                    if timestamp <= 0:
                        continue

                    forecast_time = datetime.fromtimestamp(
                        timestamp, tz=ZoneInfo("America/New_York")
                    )

                    # Include all points from today, even if they're in the past
                    # This ensures we get all 3-hour intervals
                    if forecast_time.date() == today:
                        print(f"- {forecast_time.strftime('%I:%M %p')}: processing...")
                        # Track which hours we have data for
                        hours_with_data.add(forecast_time.hour)
                    else:
                        print(
                            f"- {forecast_time.strftime('%Y-%m-%d %I:%M %p')}: different day, skipping"
                        )
                        continue

                    # Validate data structure
                    main_data = item.get("main", {})
                    if not isinstance(main_data, dict):
                        continue

                    # Extract and validate temperature data
                    try:
                        temp = float(main_data.get("temp", 0))
                        feels_like = float(main_data.get("feels_like", 0))
                    except (ValueError, TypeError):
                        continue

                    # Skip invalid temperature values
                    if not (-100 <= temp <= 150) or not (-100 <= feels_like <= 150):
                        print(
                            f"Invalid temperature values: temp={temp}, feels_like={feels_like}"
                        )
                        continue

                    # Get weather description
                    weather_list = item.get("weather", [])
                    description = "Unknown"
                    if isinstance(weather_list, list) and weather_list:
                        description = str(weather_list[0].get("main", "Unknown"))

                    # Add forecast point with raw data, no modifications
                    point = {
                        "time": timestamp
                        * 1000,  # Convert to milliseconds for Chart.js
                        "temp": round(temp, 1),
                        "feels_like": round(feels_like, 1),
                        "description": description,
                    }
                    forecast.append(point)

                    # Debug logging
                    print(f"  Added point: {temp}°F (feels like {feels_like}°F)")
                except Exception as e:
                    print(f"Error processing forecast item: {e}")
                    continue

            if not forecast:
                print("No valid forecast data points found")
            else:
                # Print summary of hours with data
                print("\nHours with forecast data:")
                print(sorted(hours_with_data))

                # Check for missing hours during daytime (7 AM to 8 PM)
                daytime_hours = set(range(7, 21))  # 7 AM to 8 PM
                missing_hours = daytime_hours - hours_with_data
                if missing_hours:
                    print(
                        f"\nWARNING: Missing forecast data for hours: {sorted(missing_hours)}"
                    )
                else:
                    print("\nAll daytime hours (7 AM to 8 PM) have forecast data")

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
        "description": weather_data["weather"][0]["description"],
    }

    # Get AI-powered summary and recommendations
    summary, safety_recs, clothing_recs = await get_clothing_recommendations(llm_data)

    return templates.TemplateResponse(
        "weather_response.html",
        {
            "request": request,
            "temp": temp,
            "wind_speed": wind_speed,
            "conditions": conditions.title(),
            "summary": summary,
            "safety_recommendations": safety_recs,
            "recommendations": clothing_recs,
            "forecast": forecast,
            "version": VERSION,
        },
    )
