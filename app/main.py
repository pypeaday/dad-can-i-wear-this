import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from .weather import WeatherService
from .llm import ClothingRecommendationService
from .__about__ import __version__

# Load environment variables
load_dotenv()

app = FastAPI(title="Dad Can I Wear This?", version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors."""
    from fastapi.responses import FileResponse
    return FileResponse("app/static/favicon.ico")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Services
weather_service = WeatherService()
llm_service = ClothingRecommendationService()

def get_system_info():
    """Get system information for footer display."""
    ollama_health = llm_service.check_health()
    return {
        "app_version": __version__,
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2:7b-instruct-q5_K_M"),
        "ollama_status": ollama_health["status"],
        "ollama_available": ollama_health["available"]
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with ZIP code input form."""
    default_zip = os.getenv("DEFAULT_ZIP_CODE", "12345")
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "default_zip_code": default_zip,
            **get_system_info()
        }
    )

@app.post("/weather", response_class=HTMLResponse)
async def get_weather_recommendations(
    request: Request,
    zip_code: str = Form(...)
):
    """Get weather data and clothing recommendations."""
    try:
        # Get weather data
        print(f"🌤️ Fetching weather data for ZIP: {zip_code}")
        weather_data = await weather_service.get_weather_data(zip_code)
        print(f"✅ Weather data received: {weather_data is not None}")
        
        # Get clothing recommendations from LLM
        print("🤖 Getting LLM recommendations...")
        recommendations = await llm_service.get_recommendations(weather_data)
        print(f"✅ Recommendations received: {len(recommendations) if recommendations else 0} chars")
        
        return templates.TemplateResponse(
            "weather_response.html",
            {
                "request": request,
                "weather_data": weather_data,
                "recommendations": recommendations,
                "zip_code": zip_code,
                **get_system_info()
            }
        )
    except Exception as e:
        print(f"❌ Error in weather endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse(
            "weather_response.html",
            {
                "request": request,
                "error": str(e),
                "zip_code": zip_code,
                "weather_data": None,  # Explicitly set to None
                **get_system_info()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
