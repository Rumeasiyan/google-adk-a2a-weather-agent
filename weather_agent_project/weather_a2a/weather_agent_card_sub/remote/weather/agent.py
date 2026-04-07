import json
import os
from collections import defaultdict
from datetime import datetime
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import uvicorn
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "demo")
WEATHER_DEFAULT_CITY = os.getenv("WEATHER_DEFAULT_CITY", "Colombo")
WEATHER_AGENT_MODEL = os.getenv("WEATHER_AGENT_MODEL", "gemini-2.0-flash")
WEATHER_A2A_PORT = int(os.getenv("WEATHER_A2A_PORT", "8091"))

MOCK_WEATHER_DATA = {
    "colombo": {
        "current": {
            "city": "Colombo",
            "temperature_c": 30,
            "feels_like_c": 34,
            "condition": "Humid and partly cloudy",
            "humidity": 78,
            "wind_kph": 18,
        },
        "forecast": [
            {"date": "2026-04-08", "condition": "Scattered showers", "high_c": 31, "low_c": 26},
            {"date": "2026-04-09", "condition": "Partly cloudy", "high_c": 32, "low_c": 26},
            {"date": "2026-04-10", "condition": "Thunderstorms late", "high_c": 30, "low_c": 25},
        ],
    },
    "london": {
        "current": {
            "city": "London",
            "temperature_c": 12,
            "feels_like_c": 10,
            "condition": "Cool with light rain",
            "humidity": 71,
            "wind_kph": 16,
        },
        "forecast": [
            {"date": "2026-04-08", "condition": "Cloudy", "high_c": 13, "low_c": 7},
            {"date": "2026-04-09", "condition": "Light rain", "high_c": 11, "low_c": 6},
            {"date": "2026-04-10", "condition": "Sunny intervals", "high_c": 14, "low_c": 8},
        ],
    },
    "new york": {
        "current": {
            "city": "New York",
            "temperature_c": 17,
            "feels_like_c": 16,
            "condition": "Clear skies",
            "humidity": 55,
            "wind_kph": 12,
        },
        "forecast": [
            {"date": "2026-04-08", "condition": "Sunny", "high_c": 18, "low_c": 10},
            {"date": "2026-04-09", "condition": "Partly cloudy", "high_c": 19, "low_c": 11},
            {"date": "2026-04-10", "condition": "Showers", "high_c": 16, "low_c": 9},
        ],
    },
    "tokyo": {
        "current": {
            "city": "Tokyo",
            "temperature_c": 20,
            "feels_like_c": 21,
            "condition": "Mild and sunny",
            "humidity": 60,
            "wind_kph": 10,
        },
        "forecast": [
            {"date": "2026-04-08", "condition": "Sunny", "high_c": 21, "low_c": 14},
            {"date": "2026-04-09", "condition": "Cloudy", "high_c": 19, "low_c": 13},
            {"date": "2026-04-10", "condition": "Light rain", "high_c": 18, "low_c": 12},
        ],
    },
}


def _use_live_weather() -> bool:
    return WEATHER_API_KEY not in {"", "demo", "your_weather_api_key_here"}


def _city_key(city: str) -> str:
    return city.strip().lower()


def _mock_current_weather(city: str) -> dict:
    weather = MOCK_WEATHER_DATA.get(_city_key(city), MOCK_WEATHER_DATA[_city_key(WEATHER_DEFAULT_CITY)])
    return {
        "source": "mock",
        **weather["current"],
    }


def _mock_forecast(city: str, days: int) -> dict:
    weather = MOCK_WEATHER_DATA.get(_city_key(city), MOCK_WEATHER_DATA[_city_key(WEATHER_DEFAULT_CITY)])
    return {
        "source": "mock",
        "city": weather["current"]["city"],
        "forecast": weather["forecast"][:days],
    }


def _fetch_openweather_json(path: str, params: dict) -> dict:
    query = urlencode(params)
    url = f"https://api.openweathermap.org/data/2.5/{path}?{query}"
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _live_current_weather(city: str) -> dict:
    payload = _fetch_openweather_json(
        "weather",
        {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric",
        },
    )
    return {
        "source": "live",
        "city": payload["name"],
        "temperature_c": round(payload["main"]["temp"]),
        "feels_like_c": round(payload["main"]["feels_like"]),
        "condition": payload["weather"][0]["description"].title(),
        "humidity": payload["main"]["humidity"],
        "wind_kph": round(payload["wind"]["speed"] * 3.6, 1),
    }


def _live_forecast(city: str, days: int) -> dict:
    payload = _fetch_openweather_json(
        "forecast",
        {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric",
        },
    )

    grouped = defaultdict(lambda: {"temps": [], "descriptions": []})
    for item in payload["list"]:
        forecast_date = datetime.utcfromtimestamp(item["dt"]).strftime("%Y-%m-%d")
        grouped[forecast_date]["temps"].append(item["main"]["temp"])
        grouped[forecast_date]["descriptions"].append(item["weather"][0]["description"].title())

    forecast = []
    for forecast_date, values in grouped.items():
        descriptions = values["descriptions"]
        forecast.append(
            {
                "date": forecast_date,
                "condition": max(set(descriptions), key=descriptions.count),
                "high_c": round(max(values["temps"])),
                "low_c": round(min(values["temps"])),
            }
        )

    return {
        "source": "live",
        "city": payload["city"]["name"],
        "forecast": forecast[:days],
    }


def get_current_weather(city: str = WEATHER_DEFAULT_CITY) -> dict:
    """Return the current weather for a city using a live API or fallback mock data."""
    try:
        if _use_live_weather():
            return _live_current_weather(city)
    except (HTTPError, URLError, KeyError, ValueError):
        pass
    return _mock_current_weather(city)


def get_weather_forecast(city: str = WEATHER_DEFAULT_CITY, days: int = 3) -> dict:
    """Return a short weather forecast for a city using a live API or fallback mock data."""
    safe_days = max(1, min(days, 5))
    try:
        if _use_live_weather():
            return _live_forecast(city, safe_days)
    except (HTTPError, URLError, KeyError, ValueError):
        pass
    return _mock_forecast(city, safe_days)


root_agent = LlmAgent(
    name="weather_agent",
    description="This is my weather agent",
    instruction="""
    You are a helpful weather assistant.
    Use the get_current_weather function when the user asks about current conditions.
    Use the get_weather_forecast function when the user asks about upcoming weather.
    """,
    model=WEATHER_AGENT_MODEL,
    tools=[get_current_weather, get_weather_forecast],
)

a2a_app = to_a2a(root_agent, port=WEATHER_A2A_PORT)


if __name__ == "__main__":
    uvicorn.run(a2a_app, host="0.0.0.0", port=WEATHER_A2A_PORT)
