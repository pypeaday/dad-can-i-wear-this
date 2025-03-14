/**
 * Temperature Forecast Chart
 * Shows today's temperatures between 7 AM and 8 PM using OpenWeatherMap's 3-hour forecast API
 */

// Initialize the chart when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get forecast data from the window object (populated by the server)
    const forecastData = window.forecastData || [];
    
    console.log('Initializing chart with data:', forecastData);
    initializeChart(forecastData);
});

function initializeChart(forecastData) {
    const canvas = document.getElementById('forecastChart');
    if (!canvas) {
        console.error('Chart canvas not found');
        return null;
    }
    
    // Validate forecast data
    if (!forecastData || !Array.isArray(forecastData) || forecastData.length === 0) {
        console.error('Invalid or empty forecast data');
        // Create a placeholder message
        const ctx = canvas.getContext('2d');
        ctx.font = '16px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.fillText('No forecast data available', canvas.width / 2, canvas.height / 2);
        return null;
    }

    // Get current time
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    // Set time boundaries for today (7 AM to 8 PM)
    const startTime = new Date(today);
    startTime.setHours(7, 0, 0, 0);
    
    const endTime = new Date(today);
    endTime.setHours(20, 0, 0, 0);
    
    // Convert forecast data timestamps to Date objects
    const points = forecastData.map(point => ({
        ...point,
        time: new Date(point.time)
    }));
    
    // Sort points by time
    points.sort((a, b) => a.time - b.time);
    
    // Log the data points
    console.log('Chart data points:', points.length, 'points');
    points.forEach(p => {
        console.log(`- ${p.time.toLocaleTimeString()}: ${p.temp}°F (feels like ${p.feels_like}°F)`);
    });
    
    // Calculate y-axis range with some padding
    const allTemps = points.flatMap(p => [p.temp, p.feels_like]);
    // Always start the y-axis at 0 degrees
    const minTemp = 0;
    const maxTemp = Math.max(Math.ceil(Math.max(...allTemps) + 5), 100);
    
    // Create the chart
    try {
        return new Chart(canvas, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Temperature (°F)',
                        data: points.map(point => ({
                            x: point.time,
                            y: point.temp
                        })),
                        borderColor: '#4361ee',
                        backgroundColor: 'rgba(67, 97, 238, 0.3)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 5,
                        pointBackgroundColor: '#4361ee'
                    },
                    {
                        label: 'Feels Like (°F)',
                        data: points.map(point => ({
                            x: point.time,
                            y: point.feels_like
                        })),
                        borderColor: '#f72585',
                        backgroundColor: 'rgba(247, 37, 133, 0.3)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 5,
                        pointBackgroundColor: '#f72585'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour',
                            displayFormats: {
                                hour: 'h a'
                            },
                            tooltipFormat: 'h:mm a'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            maxRotation: 0
                        }
                    },
                    y: {
                        min: minTemp,
                        max: maxTemp,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                plugins: {
                    annotation: {
                        annotations: {
                            currentTime: {
                                type: 'line',
                                xMin: now,
                                xMax: now,
                                borderColor: '#51cf66',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {
                                    display: true,
                                    content: 'Current Time',
                                    position: 'start',
                                    backgroundColor: '#51cf66',
                                    color: '#000000',
                                    padding: 4
                                }
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y || 0;
                                return `${label}: ${value.toFixed(1)}°F`;
                            }
                        }
                    },
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.9)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating chart:', error);
        return null;
    }
}
