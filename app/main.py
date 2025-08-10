from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
from pathlib import Path
import os
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from .llm import get_clothing_recommendations, OLLAMA_MODEL
from .__about__ import __version__

# Load environment variables from the root .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
load_dotenv(env_path)

VERSION = __version__
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
        {
            "request": request,
            "default_zip": DEFAULT_ZIP,
            "version": VERSION,
            "model": OLLAMA_MODEL,
        },
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
                raise Exception("Missing/invalid coords in current weather")

            try:
                lat = float(weather_data["coord"]["lat"])
                lon = float(weather_data["coord"]["lon"])
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error parsing coordinates: {e}")
                forecast = []
                raise Exception("Failed to parse coords")

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
                raise Exception("Forecast API non-200")

            try:
                forecast_data = forecast_response.json()
            except Exception as e:
                print(f"Error parsing forecast response: {e}")
                forecast = []
                raise Exception("Failed to parse forecast JSON")

            if not isinstance(forecast_data, dict) or "list" not in forecast_data:
                print("Invalid forecast data format")
                forecast = []
                raise Exception("Invalid forecast data format")

            # Process forecast data
            forecast = []
            forecast_items = forecast_data.get("list", [])

            if not forecast_items:
                print("Empty forecast list")
                forecast = []
                raise Exception("Empty forecast list")

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

            # Track precipitation probability (max for today)
            max_pop_pct = 0

            # Always add current weather data (the chart will filter by time window)
            current_point = {
                "time": weather_data.get("dt", 0) * 1000,
                "temp": round(float(current_temp), 1),
                "feels_like": round(float(current_feels), 1),
                "description": weather_data.get("weather", [{}])[0].get(
                    "main", "Unknown"
                ),
            }
            forecast.append(current_point)
            print("[Added current conditions to data set]")
            
            # Add current hour to hours_with_data
            current_hour = current_time.hour
            hours_with_data.add(current_hour)

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

                    # Include all points from today and early tomorrow for better trend visualization
                    # Also include points from late yesterday if available
                    tomorrow = today + timedelta(days=1)
                    yesterday = today - timedelta(days=1)
                    
                    # Accept data from yesterday evening through tomorrow morning
                    if ((forecast_time.date() == yesterday and forecast_time.hour >= 18) or
                        forecast_time.date() == today or
                        (forecast_time.date() == tomorrow and forecast_time.hour <= 11)):
                        print(f"- {forecast_time.strftime('%Y-%m-%d %I:%M %p')}: processing...")
                        # Track which hours we have data for
                        if forecast_time.date() == today:
                            hours_with_data.add(forecast_time.hour)
                            # Track precipitation probability for today (if present on item)
                            try:
                                pop = float(item.get("pop", 0.0))
                                if 0.0 <= pop <= 1.0:
                                    max_pop_pct = max(max_pop_pct, int(round(pop * 100)))
                            except Exception:
                                pass
                    else:
                        print(
                            f"- {forecast_time.strftime('%Y-%m-%d %I:%M %p')}: outside extended window, skipping"
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

                # Check for missing hours during daytime (5 AM to 11 PM)
                daytime_hours = set(range(5, 24))  # 5 AM to 11 PM
                missing_hours = daytime_hours - hours_with_data
                
                # Create a complete temperature dataset using pandas
                print("\nCreating complete temperature dataset using pandas...")
                
                # Convert forecast data to pandas DataFrame
                df_data = []
                for point in forecast:
                    # Convert milliseconds to datetime
                    time_dt = datetime.fromtimestamp(point["time"] / 1000, tz=ZoneInfo("America/New_York"))
                    df_data.append({
                        "time": time_dt,
                        "hour": time_dt.hour,
                        "temp": point["temp"],
                        "feels_like": point["feels_like"],
                        "description": point["description"]
                    })
                
                # Create DataFrame
                df = pd.DataFrame(df_data)
                
                # Print the data we have
                print("\nExisting data points:")
                for _, row in df.sort_values("hour").iterrows():
                    print(f"  {row['hour']}:00 - {row['temp']}°F (feels like {row['feels_like']}°F)")
                
                # Get the full range of hours we want to display (5 AM to 11 PM)
                all_hours = list(range(5, 24))
                
                # Find missing hours
                existing_hours = df["hour"].unique()
                missing_hours = [h for h in all_hours if h not in existing_hours]
                print(f"\nMissing hours: {missing_hours}")
                
                # If we have missing hours, create a complete dataset with all hours
                if missing_hours:
                    # Create a new DataFrame with all hours
                    all_hours_data = []
                    
                    for hour in all_hours:
                        # If we have data for this hour, use it
                        if hour in existing_hours:
                            hour_data = df[df["hour"] == hour].iloc[0].to_dict()
                            all_hours_data.append(hour_data)
                        else:
                            # Create a new timestamp for this hour
                            time_dt = datetime(today.year, today.month, today.day, hour, 0, tzinfo=ZoneInfo("America/New_York"))
                            
                            # For morning hours (before current time), we need to estimate temperatures
                            current_hour = now.hour
                            
                            if hour < current_hour:
                                # Get the closest data points we have
                                df_sorted = df.sort_values("hour")
                                next_hour_idx = df_sorted[df_sorted["hour"] > hour].index.min() if any(df_sorted["hour"] > hour) else None
                                
                                if next_hour_idx is not None:
                                    # We have a data point after this hour, use it as reference
                                    next_hour_data = df.loc[next_hour_idx]
                                    next_hour = next_hour_data["hour"]
                                    next_temp = next_hour_data["temp"]
                                    next_feels_like = next_hour_data["feels_like"]
                                    
                                    # Morning temperatures are typically 5-15°F cooler than daytime
                                    # Early morning (5-7 AM) is coolest, then gradually warms up
                                    if hour < 7:
                                        # Early morning: 12-15°F cooler than reference point
                                        temp_diff = -15 + (hour - 5) * 1.5  # -15°F at 5 AM, -12°F at 7 AM
                                    else:
                                        # Later morning: gradually warming up to reference point
                                        # Calculate how far we are between 7 AM and the reference point
                                        hours_from_7am = hour - 7
                                        hours_total = next_hour - 7
                                        progress = hours_from_7am / hours_total if hours_total > 0 else 0
                                        temp_diff = -12 * (1 - progress)  # Start at -12°F, approach 0 as we get closer to reference
                                    
                                    # Calculate estimated temperatures
                                    estimated_temp = round(next_temp + temp_diff, 1)
                                    estimated_feels_like = round(next_feels_like + temp_diff * 1.1, 1)  # Feels even cooler
                                    
                                    print(f"  Estimating {hour}:00 AM: {estimated_temp}°F (reference: {next_hour}:00 at {next_temp}°F)")
                                else:
                                    # No later points, use the earliest point we have and make it cooler
                                    earliest_data = df_sorted.iloc[0]
                                    earliest_temp = earliest_data["temp"]
                                    earliest_feels_like = earliest_data["feels_like"]
                                    
                                    # Make early morning 10-15°F cooler
                                    temp_diff = -15 + (hour - 5) * 1.0 if hour >= 5 else -15
                                    estimated_temp = round(earliest_temp + temp_diff, 1)
                                    estimated_feels_like = round(earliest_feels_like + temp_diff * 1.1, 1)
                                    
                                    print(f"  Estimating {hour}:00 AM: {estimated_temp}°F (based on earliest data: {earliest_temp}°F)")
                                
                                # Add the estimated data point
                                all_hours_data.append({
                                    "time": time_dt,
                                    "hour": hour,
                                    "temp": estimated_temp,
                                    "feels_like": estimated_feels_like,
                                    "description": "Estimated"
                                })
                            else:
                                # For future hours, we'll interpolate between existing points
                                # This is handled by the chart.js library, so we'll skip these hours
                                pass
                    
                    # Create a new DataFrame with all hours
                    if all_hours_data:
                        complete_df = pd.DataFrame(all_hours_data)
                        complete_df = complete_df.sort_values("hour")
                        
                        # Convert back to forecast format
                        forecast = []
                        for _, row in complete_df.iterrows():
                            # Convert datetime to milliseconds timestamp
                            timestamp_ms = int(row["time"].timestamp() * 1000)
                            
                            forecast.append({
                                "time": timestamp_ms,
                                "temp": row["temp"],
                                "feels_like": row["feels_like"],
                                "description": row["description"]
                            })
                        
                        print("\nCreated complete temperature dataset with all hours")

                # Check for missing hours again after interpolation
                if missing_hours:
                    print(
                        f"\nWARNING: Missing forecast data for hours: {sorted(missing_hours)}"
                    )
                else:
                    print("\nAll daytime hours (5 AM to 11 PM) have forecast data")

        except Exception as e:
            print(f"Error fetching forecast data: {e}")
            forecast = []
            # Ensure precipitation probability has a default
            max_pop_pct = 0

    # Extract weather data
    temp = round(weather_data["main"]["temp"])
    feels_like = weather_data["main"].get("feels_like")
    # Compute today's high/low from forecast
    today = datetime.now(ZoneInfo("America/New_York")).date()
    today_temps = [pt["temp"] for pt in forecast if datetime.fromtimestamp(pt["time"] / 1000, tz=ZoneInfo("America/New_York")).date() == today]
    temp_max = round(max(today_temps)) if today_temps else temp
    temp_min = round(min(today_temps)) if today_temps else temp
    if feels_like is None:
        feels_like = temp
    else:
        feels_like = round(feels_like)
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
        "forecast": forecast,  # Add forecast data for time-specific summaries
    }

    # Get AI-powered summary and recommendations
    summary, safety_recs, clothing_recs = await get_clothing_recommendations(llm_data)

    return templates.TemplateResponse(
        "weather_response.html",
        {
            "request": request,
            "temp": temp,
            "feels_like": feels_like,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "wind_speed": wind_speed,
            "conditions": conditions.title(),
            "summary": summary,
            "safety_recommendations": safety_recs,
            "recommendations": clothing_recs,
            "forecast": forecast,
            # Precipitation probability percentage for umbrella logic
            "pop": max_pop_pct,
            "version": VERSION,
            "model": OLLAMA_MODEL,
        },
    )
