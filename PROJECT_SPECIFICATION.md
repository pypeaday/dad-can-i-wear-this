# Dad Can I Wear This? - Project Specification

## Overview
A weather-based clothing recommendation web application that provides intelligent outfit suggestions based on current and forecasted weather conditions, with beautiful temperature visualizations.

## Core Features

### 1. Weather-Based Clothing Recommendations
- **Input**: ZIP code or location
- **Analysis**: Current weather + 24-hour forecast
- **Output**: Specific clothing recommendations with reasoning
- **Intelligence**: LLM-powered suggestions considering:
  - Temperature (actual + feels-like)
  - Precipitation probability
  - Wind conditions
  - Humidity levels
  - Time of day context

### 2. Advanced Temperature Visualization
- **Smooth Curve Graphs**: Catmull-Rom spline interpolation for natural temperature curves
- **Dual Temperature Lines**: 
  - Actual temperature (green gradient)
  - Feels-like temperature (blue gradient, dashed)
- **Current Time Indicator**: 
  - Multi-layered glow effect (wide/medium/core)
  - Solid red vertical line with breathing animation
- **Current Day Background**: 
  - Subtle blue shading for "today" timespan
  - Gentle pulsing animation
- **Interactive Elements**:
  - Hover tooltips with exact temperature/time
  - Responsive design
  - Professional gradients and shadows

### 3. User Experience
- **Clean Interface**: Modern, dark-themed UI
- **Fast Response**: Immediate weather data display
- **Mobile Responsive**: Works on all device sizes
- **Error Handling**: Graceful degradation with fallback data
- **Loading States**: Clear feedback during API calls

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **LLM Integration**: Ollama with qwen2:7b-instruct-q5_K_M model
- **Weather API**: OpenWeatherMap API
- **Template Engine**: Jinja2
- **Deployment**: Docker + Docker Compose

### Frontend Stack
- **Pure Web Technologies**: HTML5, CSS3, Vanilla JavaScript
- **No External Dependencies**: Self-contained for reliability
- **SVG Graphics**: Scalable temperature visualizations
- **CSS Animations**: Smooth, non-intrusive effects

### Data Flow
1. User enters ZIP code
2. Fetch current weather + 24h forecast from OpenWeatherMap
3. Generate temperature graph with smooth curves
4. Send weather data to LLM for clothing analysis
5. Display recommendations with visual temperature context

## Graph Implementation Details

### Curve Generation
- **Algorithm**: Catmull-Rom spline interpolation
- **Parameters**: 
  - Tension: 0.4 (curve smoothness)
  - Smoothing: 0.3 (natural flow)
- **Control Points**: Advanced calculation for natural curves
- **Edge Handling**: Proper endpoint management

### Visual Styling
- **Temperature Lines**:
  - Actual: Green gradient (#43a047 → #66bb6a), 4px stroke
  - Feels-like: Blue gradient (#1976d2 → #42a5f5), 3px dashed
- **Data Points**: 
  - Glow halos with white borders
  - Interactive tooltips
  - 6px radius circles
- **Current Time Line**:
  - Triple-layer glow (12px/6px/3px)
  - Solid red core (#e53e3e)
  - Extends beyond chart boundaries
- **Current Day Background**:
  - Light blue (#f0f8ff) with 20-35% opacity
  - 4-second breathing animation
  - Behind all other elements

### Responsive Design
- **Adaptive Scaling**: Chart adjusts to container size
- **Mobile Optimization**: Touch-friendly interactions
- **Dark Theme Integration**: Consistent with app styling
- **Professional Polish**: Rounded caps, drop shadows, gradients

## Configuration

### Environment Variables
```bash
OPENWEATHER_API_KEY=your_api_key_here
DEFAULT_ZIP_CODE=12345
OLLAMA_HOST=http://babyblue-aurora:11434
OLLAMA_MODEL=qwen2:7b-instruct-q5_K_M
OLLAMA_TIMEOUT=10.0
```

### Docker Setup
- **Port**: 8083:8000 (external:internal)
- **Volumes**: ./app:/app/app
- **Network**: Host gateway for Ollama access
- **Restart Policy**: unless-stopped

## File Structure
```
/
├── app/
│   ├── main.py              # FastAPI application
│   ├── llm.py               # Ollama LLM integration
│   ├── weather.py           # OpenWeather API client
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Complete styling + animations
│   │   └── js/
│   │       └── temperature-graph.js  # Advanced graph rendering
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Landing page
│       └── weather_response.html  # Results with graph
├── docker-compose.yml       # Container orchestration
├── docker-entrypoint.sh     # Container startup script
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## Quality Standards

### Code Quality
- **Pure Implementation**: No external JS libraries
- **Error Resilience**: Comprehensive error handling
- **Fallback Data**: Realistic temperature curves when API fails
- **Clean Architecture**: Separation of concerns
- **Documentation**: Clear, maintainable code

### Visual Quality
- **Professional Appearance**: Polished, modern design
- **Smooth Animations**: 60fps performance
- **Consistent Theming**: Dark mode throughout
- **Accessibility**: Clear contrast, readable fonts
- **Performance**: Fast loading, responsive interactions

### User Experience
- **Immediate Feedback**: Loading states and progress indicators
- **Clear Communication**: Helpful error messages
- **Intuitive Interface**: Self-explanatory interactions
- **Reliable Operation**: Graceful degradation
- **Mobile First**: Touch-optimized design

## Success Criteria

### Functional Requirements
- ✅ Accurate weather data retrieval
- ✅ Intelligent clothing recommendations
- ✅ Beautiful temperature visualizations
- ✅ Responsive design across devices
- ✅ Error handling and fallbacks

### Technical Requirements
- ✅ Docker containerization
- ✅ Environment-based configuration
- ✅ LLM integration with Ollama
- ✅ Pure web technologies (no external deps)
- ✅ Professional code quality

### Visual Requirements
- ✅ Smooth temperature curves (Catmull-Rom splines)
- ✅ Multi-layered current time indicator
- ✅ Current day background highlighting
- ✅ Professional gradients and animations
- ✅ Dark theme consistency

## Future Enhancements
- Multiple location support
- Weather alerts integration
- Clothing preference learning
- Extended forecast periods
- Social sharing features
- Outfit photo suggestions
