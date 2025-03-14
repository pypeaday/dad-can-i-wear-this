"""Safety guidelines and standard recommendations for weather conditions."""

from typing import List, Dict

def get_safety_recommendations(weather_data: Dict) -> List[str]:
    """Get safety recommendations based on weather conditions."""
    recommendations = []
    temp = weather_data["temp"]
    feels_like = weather_data["feels_like"]
    conditions = weather_data["conditions"]
    wind_speed = weather_data["wind_speed"]

    # Extreme temperature warnings
    if feels_like < 32:
        recommendations.append("⚠️ Risk of hypothermia! Limit time outdoors.")
    elif feels_like < 20:
        recommendations.append("🚫 Dangerous cold! Stay indoors if possible.")
    elif feels_like > 90:
        recommendations.append("⚠️ Heat exhaustion risk! Stay hydrated.")
    elif feels_like > 100:
        recommendations.append("🚫 Dangerous heat! Limit outdoor activities.")

    # Temperature difference warnings
    if abs(temp - feels_like) > 15:
        recommendations.append("⚠️ Temperature feels much different than actual! Dress in layers.")

    # Wind safety
    if wind_speed > 25:
        recommendations.append("💨 High winds! Be careful with loose items.")
    elif wind_speed > 35:
        recommendations.append("🌪️ Dangerous winds! Stay indoors if possible.")

    # Weather condition safety
    if conditions in ["thunderstorm"]:
        recommendations.append("⚡ Thunderstorm! Seek shelter if outdoors.")
    elif conditions in ["tornado"]:
        recommendations.append("🌪️ Tornado warning! Seek appropriate shelter immediately.")
    elif conditions in ["snow", "sleet"]:
        recommendations.append("❄️ Slippery conditions! Watch your step.")
    elif conditions in ["rain", "drizzle"]:
        recommendations.append("☔ Slick surfaces! Walk carefully.")
    elif conditions in ["fog"]:
        recommendations.append("🌫️ Limited visibility! Be extra cautious.")

    # UV and sun protection
    if conditions in ["clear", "clouds"] and temp > 75:
        recommendations.append("☀️ Don't forget sunscreen and sunglasses!")

    return recommendations

def get_standard_recommendations(weather_data: Dict) -> List[str]:
    """Get standard clothing recommendations based on temperature ranges."""
    feels_like = weather_data["feels_like"]
    conditions = weather_data["conditions"]
    wind_speed = weather_data["wind_speed"]
    
    recommendations = []
    
    # Base layer recommendations
    if feels_like < 30:
        recommendations.append("🧊 Base layer: Thermal underwear or heat tech")
    elif feels_like < 45:
        recommendations.append("👕 Base layer: Long sleeve shirt")
    else:
        recommendations.append("👕 Base layer: T-shirt or short sleeves")
        
    # Pants/shorts recommendations
    if feels_like < 32:
        recommendations.append("👖 Bottoms: Heavy pants with thermal underwear")
    elif feels_like < 50:
        recommendations.append("👖 Bottoms: Long pants, possibly thermal for lower temperatures")
    elif feels_like < 65:
        recommendations.append("👖 Bottoms: Long pants or jeans")
    elif feels_like < 75:
        recommendations.append("👖 Bottoms: Light pants or shorts depending on preference")
    elif feels_like < 85:
        recommendations.append("🩳 Bottoms: Shorts or very light pants")
    else:
        recommendations.append("🩳 Bottoms: Shorts")
    
    # Mid layer recommendations
    if feels_like < 40:
        recommendations.append("🧥 Mid layer: Fleece or wool sweater")
    elif feels_like < 55 or (wind_speed > 15 and feels_like < 65):
        recommendations.append("🧥 Mid layer: Light sweater or long sleeves")
    
    # Outer layer recommendations
    if feels_like < 32:
        recommendations.append("🧥 Outer layer: Heavy winter coat")
    elif feels_like < 45:
        recommendations.append("🧥 Outer layer: Winter coat")
    elif feels_like < 60:
        recommendations.append("🧥 Outer layer: Light jacket")
    elif wind_speed > 15:
        recommendations.append("🧥 Consider a windbreaker")
    
    # Accessories
    if feels_like < 40:
        recommendations.extend([
            "🧣 Wear a scarf",
            "🧤 Don't forget gloves",
            "🧢 Wear a warm hat"
        ])
    elif feels_like > 75:
        recommendations.append("🧢 Consider a hat for sun protection")
    
    # Rain gear
    if conditions in ["rain", "drizzle", "thunderstorm"]:
        if wind_speed > 15:
            recommendations.append("🧥 Wear a rain jacket (too windy for umbrella)")
        else:
            recommendations.append("☔ Bring an umbrella")
    
    # Footwear
    if conditions in ["rain", "drizzle", "thunderstorm"]:
        recommendations.append("👢 Wear waterproof shoes")
    elif conditions in ["snow", "sleet"]:
        recommendations.append("👢 Wear insulated, waterproof boots")
    else:
        recommendations.append("👟 Regular shoes are fine")
    
    return recommendations
