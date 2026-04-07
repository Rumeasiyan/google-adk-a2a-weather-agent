import os

from dotenv import load_dotenv
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

load_dotenv()

WEATHER_A2A_HOST = os.getenv("WEATHER_A2A_HOST", "localhost")
WEATHER_A2A_PORT = os.getenv("WEATHER_A2A_PORT", "8091")
WEATHER_A2A_ROUTE = os.getenv("WEATHER_A2A_ROUTE", "/a2a/weather")

root_agent = RemoteA2aAgent(
    name="WeatherLookupAgent",
    description="An agent that can look up current weather and forecasts using a remote weather service.",
    agent_card=f"http://{WEATHER_A2A_HOST}:{WEATHER_A2A_PORT}{WEATHER_A2A_ROUTE}{AGENT_CARD_WELL_KNOWN_PATH}",
)
