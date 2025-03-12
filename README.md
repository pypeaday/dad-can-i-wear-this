# Dad, Can I Wear This?

A smart, mobile-first web application that helps answer weather-related clothing questions like "Do I need a coat?" or "Should I bring an umbrella?" Built with FastAPI, HTMX, and Ollama for AI-powered recommendations in a clean dark theme.

## Features

- Simple ZIP code-based weather lookup
- AI-powered clothing recommendations using local LLM
- 24-hour temperature forecast visualization
- Mobile-first dark theme
- Clean, modern UI with HTMX for smooth interactions

## Setup

1. Create a virtual environment (do not commit to git):
   ```bash
   python -m venv .venv
   ```

2. Install Ollama:
   - Follow installation instructions at [Ollama.ai](https://ollama.ai)
   - Start the Mistral model:
     ```bash
     ollama run mistral
     ```

3. Copy the example environment file and update with your values:
   ```bash
   cp .env.example .env
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Get an API key:
   - Sign up for a free API key at [OpenWeatherMap](https://openweathermap.org/api)
   - Add your API key and default ZIP code to `.env`
   - Optionally configure Ollama settings in `.env`

## Running the Application

From the project root:

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000 in your browser.

## Tech Stack

- FastAPI - Modern Python web framework
- HTMX - Simple and powerful frontend interactions
- OpenWeatherMap API - Weather data
- Ollama - Local LLM for smart recommendations
- Chart.js - Temperature forecast visualization
- Jinja2 - Template rendering

## Environment Variables

- `OPENWEATHER_API_KEY` - Your OpenWeather API key
- `DEFAULT_ZIP_CODE` - Default ZIP code for weather lookup
- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Ollama model to use (default: mistral)
