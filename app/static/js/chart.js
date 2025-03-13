function initializeChart(forecastData) {
    const canvas = document.getElementById('forecastChart');
    if (!canvas) {
        console.error('Chart canvas not found');
        return null;
    }

    // Get current time for the vertical line
    const currentTime = new Date();
    
    // Convert forecast data timestamps to Date objects
    const data = forecastData.map(point => ({
        ...point,
        time: new Date(point.time)
    }));
    
    // Get time range for the chart
    const today = new Date();
    const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 7, 0, 0);
    const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 20, 0, 0);
    
    // Format data for Chart.js
    const chartData = {
        datasets: [
            {
                label: 'Temperature (°F)',
                data: data.map(point => ({
                    x: point.time,
                    y: point.temp
                })),
                borderColor: '#646cff',
                backgroundColor: 'rgba(100, 108, 255, 0.2)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Feels Like (°F)',
                data: data.map(point => ({
                    x: point.time,
                    y: point.feels_like
                })),
                borderColor: '#ff6b6b',
                backgroundColor: 'rgba(255, 107, 107, 0.2)',
                tension: 0.4,
                fill: true
            }
        ]
    };

    // Chart configuration
    const config = {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            hour: 'h:mm a'
                        }
                    },
                    min: startTime,
                    max: endTime,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        maxRotation: 0,
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Temperature (°F)',
                        color: 'rgba(255, 255, 255, 0.9)'
                    },
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
                            xMin: currentTime,
                            xMax: currentTime,
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
    };

    // Create and return the chart
    return new Chart(canvas, config);
}
