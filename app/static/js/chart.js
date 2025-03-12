function initializeChart(forecast) {
    // Clean up any existing chart
    const chartId = 'forecastChart';
    const existingChart = Chart.getChart(chartId);
    if (existingChart) {
        existingChart.destroy();
    }

    const ctx = document.getElementById(chartId);
    if (!ctx) return;

    // Process data for the chart
    const labels = forecast.map(f => {
        const date = new Date(f.time * 1000);
        return date.toLocaleTimeString([], { hour: 'numeric' });
    });
    
    const tempData = forecast.map(f => f.temp);
    const feelsLikeData = forecast.map(f => f.feels_like);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Temperature °F',
                data: tempData,
                borderColor: '#646cff',
                tension: 0.4,
                fill: false
            }, {
                label: 'Feels Like °F',
                data: feelsLikeData,
                borderColor: '#ff6b6b',
                tension: 0.4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        color: '#2d2d2d'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                x: {
                    grid: {
                        color: '#2d2d2d'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}
