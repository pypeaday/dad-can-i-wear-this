"""Safety guidelines and standard recommendations for weather conditions."""

from typing import List, Dict


def get_safety_recommendations(weather_data: Dict) -> List[str]:
    """Get safety recommendations based on weather conditions."""
    recommendations = []
    temp = weather_data["temp"]
    feels_like = weather_data["feels_like"]
    conditions = weather_data["conditions"]
    wind_speed = weather_data["wind_speed"]

    # Extreme temperature warnings - more flexible thresholds
    if feels_like < 20:
        recommendations.append("⚠️ Risk of hypothermia with prolonged exposure! Dress warmly.")
    elif feels_like < 5:
        recommendations.append("🚫 Dangerous cold! Limit time outdoors and dress in layers.")
    elif feels_like > 95:
        recommendations.append("⚠️ Heat exhaustion risk! Stay hydrated and seek shade.")
    elif feels_like > 105:
        recommendations.append("🚫 Dangerous heat! Limit outdoor activities to early morning or evening.")

    # Temperature difference warnings - more reasonable threshold
    if abs(temp - feels_like) > 10:
        recommendations.append(
            "⚠️ Temperature feels different than actual! Consider dressing in layers."
        )

    # Wind safety - adjusted thresholds
    if wind_speed > 20:
        recommendations.append("💨 Moderate winds! Consider a windbreaker.")
    elif wind_speed > 30:
        recommendations.append("🌪️ Strong winds! Be careful outdoors.")

    # Weather condition safety
    if conditions in ["thunderstorm"]:
        recommendations.append("⚡ Thunderstorm! Seek shelter if outdoors.")
    elif conditions in ["tornado"]:
        recommendations.append(
            "🌪️ Tornado warning! Seek appropriate shelter immediately."
        )
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

    recommendations = []

    # Base layer recommendations - more flexible
    if feels_like < 25:
        recommendations.append("🧊 Base layer: Thermal underwear or heat tech")
    elif feels_like < 50:
        recommendations.append("👕 Base layer: Long sleeve shirt")
    else:
        recommendations.append("👕 Base layer: T-shirt or short sleeves")

    # Pants/shorts recommendations - more flexible
    if feels_like < 65:
        if feels_like < 25:
            recommendations.append("👖 Bottoms: Heavy pants with thermal layer")
        else:
            recommendations.append("👖 Bottoms: Long pants")
    else:
        recommendations.append("🩳 Bottoms: Shorts or light pants")

    # Coat recommendations - more flexible
    if feels_like < 55:
        if feels_like < 25:
            recommendations.append("🧥 Outer layer: Heavy winter coat")
        elif feels_like < 40:
            recommendations.append("🧥 Outer layer: Winter coat")
        else:
            recommendations.append("🧥 Outer layer: Light jacket")

    # Accessories - more flexible recommendations
    if feels_like < 32:
        recommendations.extend(
            ["🧣 Consider a scarf", "🧤 Consider gloves", "🧢 Consider a warm hat"]
        )

    # Rain gear - clear, non-optional recommendations
    if conditions in ["rain", "drizzle", "thunderstorm"]:
        recommendations.append("🧥 Wear a rain jacket")

    # Footwear - clear, non-optional recommendations
    if conditions in ["rain", "drizzle", "thunderstorm", "snow", "sleet"]:
        recommendations.append("👢 Wear waterproof boots")
    else:
        recommendations.append("👟 Wear closed-toe shoes")

    return recommendations
