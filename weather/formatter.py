# OpenWeather condition code 의 앞자리로 분류한다. 800(맑음)만 801~804(구름)와 갈라진다.
WEATHER_EMOJI = {
    2: ":thunder_cloud_and_rain:",
    3: ":barely_sunny:",
    5: ":rain_cloud:",
    6: ":snowflake:",
    7: ":fog:",
    8: ":partly_sunny:",
}


def get_weather_emoji(weather_id: int) -> str:
    if weather_id == 800:
        return ":sunny:"
    return WEATHER_EMOJI.get(weather_id // 100, ":white_sun_cloud:")


def format_weather_fields(weather: dict) -> list[dict]:
    emoji = get_weather_emoji(weather["weather_id"])
    return [
        {"type": "mrkdwn", "text": f"*날씨*\n{emoji} {weather['description']}"},
        {"type": "mrkdwn", "text": f"*기온*\n{weather['temp']}°C (체감 {weather['feels_like']}°C)"},
        {"type": "mrkdwn", "text": f"*강수 확률*\n{weather['rain_prob']}%"},
        {"type": "mrkdwn", "text": f"*습도*\n{weather['humidity']}%"},
    ]
