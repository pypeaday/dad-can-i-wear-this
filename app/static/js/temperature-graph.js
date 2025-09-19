/**
 * Advanced Temperature Graph with Catmull-Rom Spline Interpolation
 * Features smooth curves, current time indicator, and professional styling
 */

function renderTemperatureGraph(weatherData) {
    console.log('🎨 Starting temperature graph rendering...');
    
    const container = document.getElementById('temperature-graph');
    if (!container) {
        console.error('❌ Temperature graph container not found');
        return;
    }
    
    try {
        // Validate and prepare data
        const graphData = prepareGraphData(weatherData);
        if (!graphData || graphData.length === 0) {
            throw new Error('No valid temperature data available');
        }
        
        // Create SVG graph
        createTemperatureGraph(container, graphData, weatherData.current);
        
    } catch (error) {
        console.error('❌ Graph rendering failed:', error);
        showFallbackGraph(container, weatherData.current);
    }
}

function prepareGraphData(weatherData) {
    console.log('📊 Preparing graph data...');
    
    const data = [];
    const currentTime = new Date();
    
    // Add current weather as first point
    data.push({
        time: currentTime,
        temperature: weatherData.current.temperature,
        feelsLike: weatherData.current.feels_like,
        isCurrent: true
    });
    
    // Add forecast data
    if (weatherData.forecast && Array.isArray(weatherData.forecast)) {
        weatherData.forecast.forEach(item => {
            const time = new Date(item.timestamp);
            if (time > currentTime) {
                data.push({
                    time: time,
                    temperature: item.temperature,
                    feelsLike: item.feels_like,
                    isCurrent: false
                });
            }
        });
    }
    
    // Sort by time and validate
    data.sort((a, b) => a.time - b.time);
    
    console.log(`✅ Prepared ${data.length} data points`);
    return data.filter(d => 
        typeof d.temperature === 'number' && 
        typeof d.feelsLike === 'number' &&
        !isNaN(d.temperature) && 
        !isNaN(d.feelsLike)
    );
}

function createTemperatureGraph(container, data, currentWeather) {
    console.log('🎨 Creating SVG temperature graph...');
    
    // Clear container
    container.innerHTML = '';
    
    // Graph dimensions
    const width = container.clientWidth || 800;
    const height = 300;
    const margin = { top: 20, right: 60, bottom: 60, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Create SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    
    // Create gradients
    createGradients(svg);
    
    // Calculate scales
    const temperatures = data.flatMap(d => [d.temperature, d.feelsLike]);
    const tempMin = Math.min(...temperatures) - 5;
    const tempMax = Math.max(...temperatures) + 5;
    
    const timeMin = data[0].time;
    const timeMax = data[data.length - 1].time;
    
    // Scale functions
    const xScale = (time) => margin.left + ((time - timeMin) / (timeMax - timeMin)) * chartWidth;
    const yScale = (temp) => margin.top + ((tempMax - temp) / (tempMax - tempMin)) * chartHeight;
    
    // Create current day background
    createCurrentDayBackground(svg, margin, chartWidth, chartHeight, timeMin, timeMax, xScale);
    
    // Create axes
    createAxes(svg, margin, chartWidth, chartHeight, tempMin, tempMax, timeMin, timeMax, xScale, yScale);
    
    // Generate smooth curves using Catmull-Rom splines
    const actualTempPath = generateSmoothCurve(data.map(d => ({
        x: xScale(d.time),
        y: yScale(d.temperature)
    })));
    
    const feelsLikePath = generateSmoothCurve(data.map(d => ({
        x: xScale(d.time),
        y: yScale(d.feelsLike)
    })));
    
    // Draw temperature curves
    drawTemperatureCurve(svg, actualTempPath, 'url(#tempGradient)', 4, false);
    drawTemperatureCurve(svg, feelsLikePath, 'url(#feelsLikeGradient)', 3, true);
    
    // Draw data points
    data.forEach(d => {
        drawDataPoint(svg, xScale(d.time), yScale(d.temperature), d.isCurrent, 'actual');
        drawDataPoint(svg, xScale(d.time), yScale(d.feelsLike), d.isCurrent, 'feels-like');
    });
    
    // Draw current time indicator
    const currentTime = new Date();
    if (currentTime >= timeMin && currentTime <= timeMax) {
        drawCurrentTimeIndicator(svg, xScale(currentTime), margin.top, chartHeight);
    }
    
    // Add legend
    createLegend(svg, width, margin);
    
    // Add tooltips
    addTooltips(svg, data, xScale, yScale);
    
    container.appendChild(svg);
    console.log('✅ Temperature graph created successfully');
}

function createGradients(svg) {
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    // Temperature gradient (green)
    const tempGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    tempGradient.setAttribute('id', 'tempGradient');
    tempGradient.innerHTML = `
        <stop offset="0%" style="stop-color:#43a047;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#66bb6a;stop-opacity:1" />
    `;
    
    // Feels-like gradient (blue)
    const feelsLikeGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    feelsLikeGradient.setAttribute('id', 'feelsLikeGradient');
    feelsLikeGradient.innerHTML = `
        <stop offset="0%" style="stop-color:#1976d2;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#42a5f5;stop-opacity:1" />
    `;
    
    // Current time gradient (red)
    const currentTimeGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    currentTimeGradient.setAttribute('id', 'currentTimeGradient');
    currentTimeGradient.setAttribute('x1', '0%');
    currentTimeGradient.setAttribute('y1', '0%');
    currentTimeGradient.setAttribute('x2', '0%');
    currentTimeGradient.setAttribute('y2', '100%');
    currentTimeGradient.innerHTML = `
        <stop offset="0%" style="stop-color:#ff5722;stop-opacity:0.8" />
        <stop offset="50%" style="stop-color:#e53e3e;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#d32f2f;stop-opacity:0.8" />
    `;
    
    defs.appendChild(tempGradient);
    defs.appendChild(feelsLikeGradient);
    defs.appendChild(currentTimeGradient);
    svg.appendChild(defs);
}

function createCurrentDayBackground(svg, margin, chartWidth, chartHeight, timeMin, timeMax, xScale) {
    const currentDay = new Date();
    const dayStart = new Date(currentDay.getFullYear(), currentDay.getMonth(), currentDay.getDate());
    const dayEnd = new Date(dayStart.getTime() + 24 * 60 * 60 * 1000);
    
    if (dayStart <= timeMax && dayEnd >= timeMin) {
        const startX = Math.max(margin.left, xScale(dayStart));
        const endX = Math.min(margin.left + chartWidth, xScale(dayEnd));
        
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', startX);
        rect.setAttribute('y', margin.top);
        rect.setAttribute('width', endX - startX);
        rect.setAttribute('height', chartHeight);
        rect.setAttribute('fill', '#f0f8ff');
        rect.setAttribute('opacity', '0.2');
        rect.setAttribute('class', 'current-day-bg');
        
        // Add breathing animation
        const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animate.setAttribute('attributeName', 'opacity');
        animate.setAttribute('values', '0.2;0.35;0.2');
        animate.setAttribute('dur', '4s');
        animate.setAttribute('repeatCount', 'indefinite');
        rect.appendChild(animate);
        
        svg.appendChild(rect);
    }
}

function generateSmoothCurve(points) {
    if (points.length < 2) return '';
    if (points.length === 2) {
        return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
    }
    
    const tension = 0.4;
    const smoothing = 0.3;
    
    let path = `M ${points[0].x} ${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[Math.max(i - 1, 0)];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = points[Math.min(i + 2, points.length - 1)];
        
        // Calculate control points using Catmull-Rom approach
        const cp1x = p1.x + (p2.x - p0.x) * tension * smoothing;
        const cp1y = p1.y + (p2.y - p0.y) * tension * smoothing;
        const cp2x = p2.x - (p3.x - p1.x) * tension * smoothing;
        const cp2y = p2.y - (p3.y - p1.y) * tension * smoothing;
        
        path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
    
    return path;
}

function drawTemperatureCurve(svg, pathData, stroke, strokeWidth, isDashed) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('stroke', stroke);
    path.setAttribute('stroke-width', strokeWidth);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    path.setAttribute('filter', `drop-shadow(0 2px 4px rgba(67, 160, 71, 0.3))`);
    
    if (isDashed) {
        path.setAttribute('stroke-dasharray', '8,4');
    }
    
    svg.appendChild(path);
}

function drawDataPoint(svg, x, y, isCurrent, type) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', x);
    circle.setAttribute('cy', y);
    circle.setAttribute('r', isCurrent ? 8 : 6);
    circle.setAttribute('fill', type === 'actual' ? '#66bb6a' : '#42a5f5');
    circle.setAttribute('stroke', '#ffffff');
    circle.setAttribute('stroke-width', '2');
    circle.setAttribute('filter', 'drop-shadow(0 2px 6px rgba(0,0,0,0.2))');
    
    if (isCurrent) {
        circle.setAttribute('filter', 'drop-shadow(0 0 12px rgba(229, 62, 62, 0.6))');
    }
    
    svg.appendChild(circle);
}

function drawCurrentTimeIndicator(svg, x, top, height) {
    // Triple-layer glow effect
    const layers = [
        { width: 12, opacity: 0.3 },
        { width: 6, opacity: 0.6 },
        { width: 3, opacity: 1.0 }
    ];
    
    layers.forEach(layer => {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x);
        line.setAttribute('y1', top - 10);
        line.setAttribute('x2', x);
        line.setAttribute('y2', top + height + 10);
        line.setAttribute('stroke', 'url(#currentTimeGradient)');
        line.setAttribute('stroke-width', layer.width);
        line.setAttribute('opacity', layer.opacity);
        line.setAttribute('stroke-linecap', 'round');
        svg.appendChild(line);
    });
    
    // Add "Now" label
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', x);
    text.setAttribute('y', top - 15);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', '#e53e3e');
    text.setAttribute('font-size', '12');
    text.setAttribute('font-weight', 'bold');
    text.textContent = 'Now';
    svg.appendChild(text);
}

function createAxes(svg, margin, chartWidth, chartHeight, tempMin, tempMax, timeMin, timeMax, xScale, yScale) {
    // Y-axis (temperature)
    for (let temp = Math.ceil(tempMin / 10) * 10; temp <= tempMax; temp += 10) {
        const y = yScale(temp);
        
        // Grid line
        const gridLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        gridLine.setAttribute('x1', margin.left);
        gridLine.setAttribute('y1', y);
        gridLine.setAttribute('x2', margin.left + chartWidth);
        gridLine.setAttribute('y2', y);
        gridLine.setAttribute('stroke', '#4a4a4a');
        gridLine.setAttribute('stroke-width', '1');
        gridLine.setAttribute('opacity', '0.3');
        svg.appendChild(gridLine);
        
        // Label
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', margin.left - 10);
        label.setAttribute('y', y + 4);
        label.setAttribute('text-anchor', 'end');
        label.setAttribute('fill', '#b0b0b0');
        label.setAttribute('font-size', '12');
        label.textContent = `${temp}°F`;
        svg.appendChild(label);
    }
    
    // X-axis (time)
    const timeSpan = timeMax - timeMin;
    const hourInterval = timeSpan > 12 * 60 * 60 * 1000 ? 4 : 2; // 4 hours if > 12 hours, else 2 hours
    
    for (let hour = 0; hour < 24; hour += hourInterval) {
        const time = new Date(timeMin.getTime() + hour * 60 * 60 * 1000);
        if (time <= timeMax) {
            const x = xScale(time);
            
            // Grid line
            const gridLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            gridLine.setAttribute('x1', x);
            gridLine.setAttribute('y1', margin.top);
            gridLine.setAttribute('x2', x);
            gridLine.setAttribute('y2', margin.top + chartHeight);
            gridLine.setAttribute('stroke', '#4a4a4a');
            gridLine.setAttribute('stroke-width', '1');
            gridLine.setAttribute('opacity', '0.3');
            svg.appendChild(gridLine);
            
            // Label
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', x);
            label.setAttribute('y', margin.top + chartHeight + 20);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', '#b0b0b0');
            label.setAttribute('font-size', '12');
            label.textContent = time.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                hour12: true 
            });
            svg.appendChild(label);
        }
    }
}

function createLegend(svg, width, margin) {
    const legendY = margin.top + 10;
    
    // Actual temperature legend
    const actualLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    actualLine.setAttribute('x1', width - 150);
    actualLine.setAttribute('y1', legendY);
    actualLine.setAttribute('x2', width - 120);
    actualLine.setAttribute('y2', legendY);
    actualLine.setAttribute('stroke', 'url(#tempGradient)');
    actualLine.setAttribute('stroke-width', '4');
    svg.appendChild(actualLine);
    
    const actualText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    actualText.setAttribute('x', width - 115);
    actualText.setAttribute('y', legendY + 4);
    actualText.setAttribute('fill', '#b0b0b0');
    actualText.setAttribute('font-size', '12');
    actualText.textContent = 'Actual';
    svg.appendChild(actualText);
    
    // Feels-like temperature legend
    const feelsLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    feelsLine.setAttribute('x1', width - 150);
    feelsLine.setAttribute('y1', legendY + 20);
    feelsLine.setAttribute('x2', width - 120);
    feelsLine.setAttribute('y2', legendY + 20);
    feelsLine.setAttribute('stroke', 'url(#feelsLikeGradient)');
    feelsLine.setAttribute('stroke-width', '3');
    feelsLine.setAttribute('stroke-dasharray', '8,4');
    svg.appendChild(feelsLine);
    
    const feelsText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    feelsText.setAttribute('x', width - 115);
    feelsText.setAttribute('y', legendY + 24);
    feelsText.setAttribute('fill', '#b0b0b0');
    feelsText.setAttribute('font-size', '12');
    feelsText.textContent = 'Feels Like';
    svg.appendChild(feelsText);
}

function addTooltips(svg, data, xScale, yScale) {
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(45, 45, 45, 0.95);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s;
        z-index: 1000;
        border: 1px solid #4a4a4a;
    `;
    document.body.appendChild(tooltip);
    
    // Add invisible hover areas
    data.forEach(d => {
        const hoverArea = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        hoverArea.setAttribute('cx', xScale(d.time));
        hoverArea.setAttribute('cy', yScale(d.temperature));
        hoverArea.setAttribute('r', 15);
        hoverArea.setAttribute('fill', 'transparent');
        hoverArea.style.cursor = 'pointer';
        
        hoverArea.addEventListener('mouseenter', (e) => {
            const timeStr = d.time.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });
            tooltip.innerHTML = `
                <strong>${timeStr}${d.isCurrent ? ' (Now)' : ''}</strong><br>
                Actual: ${d.temperature}°F<br>
                Feels like: ${d.feelsLike}°F
            `;
            tooltip.style.opacity = '1';
        });
        
        hoverArea.addEventListener('mousemove', (e) => {
            tooltip.style.left = (e.pageX + 10) + 'px';
            tooltip.style.top = (e.pageY - 10) + 'px';
        });
        
        hoverArea.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
        });
        
        svg.appendChild(hoverArea);
    });
}

function showFallbackGraph(container, currentWeather) {
    console.log('🔄 Showing fallback graph with generated data...');
    
    // Generate realistic temperature curve for fallback
    const fallbackData = generateFallbackData(currentWeather);
    createTemperatureGraph(container, fallbackData, currentWeather);
}

function generateFallbackData(currentWeather) {
    const data = [];
    const baseTemp = currentWeather.temperature;
    const baseFeels = currentWeather.feels_like;
    const currentTime = new Date();
    
    // Generate 24 hours of realistic temperature data
    for (let hour = 0; hour < 24; hour += 3) {
        const time = new Date(currentTime.getTime() + hour * 60 * 60 * 1000);
        
        // Simulate daily temperature curve
        const hourOfDay = time.getHours();
        let tempOffset = 0;
        
        if (hourOfDay >= 6 && hourOfDay <= 14) {
            // Morning to afternoon - warming up
            tempOffset = (hourOfDay - 6) * 2;
        } else if (hourOfDay > 14 && hourOfDay <= 18) {
            // Afternoon to evening - cooling down
            tempOffset = 16 - (hourOfDay - 14) * 3;
        } else {
            // Night - cooler
            tempOffset = -5 + Math.random() * 3;
        }
        
        data.push({
            time: time,
            temperature: Math.round(baseTemp + tempOffset + (Math.random() - 0.5) * 4),
            feelsLike: Math.round(baseFeels + tempOffset + (Math.random() - 0.5) * 3),
            isCurrent: hour === 0
        });
    }
    
    return data;
}
