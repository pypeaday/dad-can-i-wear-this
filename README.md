# Dad, Can I Wear This?

A simple, mobile-first web application that helps answer weather-related clothing questions like "Do I need a coat?" or "Should I bring an umbrella?" Built with FastAPI and HTMX for a snappy, modern experience with a clean dark theme.

## Features

- Simple ZIP code-based weather lookup
- Instant clothing recommendations
- Mobile-first dark theme
- Clean, modern UI with HTMX for smooth interactions

## Setup

1. Create a virtual environment (do not commit to git):
   ```bash
   python -m venv .venv
   ```

2. Copy the example environment file and update with your values:
   ```bash
   cp .env.example .env
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Get an API key:
   - Sign up for a free API key at [OpenWeatherMap](https://openweathermap.org/api)
   - Add your API key and default ZIP code to `.env`

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
- Jinja2 - Template rendering
