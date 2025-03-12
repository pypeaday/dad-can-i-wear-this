/**
 * Initialize or update the forecast chart
 * @param {Array<{time: number, temp: number, feels_like: number}>} forecast - Forecast data
 * @returns {void}
 */
function initializeChart(forecast) {
    // Validate input
    if (!Array.isArray(forecast) || forecast.length === 0) {
        console.warn('Invalid forecast data provided');
        return;
    }

    // Wait for Chart.js to be available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }

    // Get the canvas element
    const chartId = 'forecastChart';
    const canvas = document.getElementById(chartId);
    if (!canvas) {
        console.warn('Chart canvas not found');
        return;
    }

    // Clean up any existing chart
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }

    try {
        // Process data for the chart
        const labels = forecast.map(f => {
            const date = new Date(f.time * 1000);
            return date.toLocaleTimeString([], { hour: 'numeric' });
        });
        
        const tempData = forecast.map(f => parseFloat(f.temp));
        const feelsLikeData = forecast.map(f => parseFloat(f.feels_like));
        
        // Find min and max temperatures for better scaling
        const allTemps = [...tempData, ...feelsLikeData].filter(t => !isNaN(t));
        if (allTemps.length === 0) {
            console.warn('No valid temperature data');
            return;
        }

        const minTemp = Math.floor(Math.min(...allTemps));
        const maxTemp = Math.ceil(Math.max(...allTemps));
        const padding = 5; // Add 5 degrees padding

        // Create gradient fills
        const ctx = canvas.getContext('2d');
        const tempGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        tempGradient.addColorStop(0, 'rgba(100, 108, 255, 0.2)');
        tempGradient.addColorStop(1, 'rgba(100, 108, 255, 0)');

        const feelsLikeGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        feelsLikeGradient.addColorStop(0, 'rgba(255, 107, 107, 0.2)');
        feelsLikeGradient.addColorStop(1, 'rgba(255, 107, 107, 0)');

        // Create the chart
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Temperature °F',
                    data: tempData,
                    borderColor: '#646cff',
                    backgroundColor: tempGradient,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Feels Like °F',
                    data: feelsLikeData,
                    borderColor: '#ff6b6b',
                    backgroundColor: feelsLikeGradient,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                devicePixelRatio: 2,
                animation: {
                    duration: 750,
                    easing: 'easeOutQuart'
                },
                layout: {
                    padding: {
                        top: 20,
                        right: 20,
                        bottom: 20,
                        left: 20
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'center',
                        labels: {
                            color: '#ffffff',
                            font: {
                                size: 14,
                                weight: 'bold',
                                family: 'system-ui, -apple-system, sans-serif'
                            },
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold',
                            family: 'system-ui, -apple-system, sans-serif'
                        },
                        bodyFont: {
                            size: 14,
                            family: 'system-ui, -apple-system, sans-serif'
                        },
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}°F`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: minTemp - padding,
                        max: maxTemp + padding,
                        grid: {
                            color: 'rgba(45, 45, 45, 0.5)',
                            drawBorder: false,
                            drawTicks: false
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: {
                                size: 12,
                                family: 'system-ui, -apple-system, sans-serif'
                            },
                            padding: 8,
                            callback: function(value) {
                                return `${value}°F`;
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(45, 45, 45, 0.5)',
                            drawBorder: false,
                            drawTicks: false
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: {
                                size: 12,
                                family: 'system-ui, -apple-system, sans-serif'
                            },
                            padding: 8
                        }
                    }
                }
            }
        });

        return chart;
    } catch (error) {
        console.error('Error initializing chart:', error);
        return null;
    }
}
