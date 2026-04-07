import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

load_dotenv()

WEATHER_A2A_HOST = os.getenv("WEATHER_A2A_HOST", "localhost")
WEATHER_A2A_PORT = os.getenv("WEATHER_A2A_PORT", "8091")
WEATHER_A2A_ROUTE = os.getenv("WEATHER_A2A_ROUTE", "/a2a/weather")
WEATHER_ORCHESTRATOR_MODEL = os.getenv("WEATHER_ORCHESTRATOR_MODEL", "gemini-2.5-flash")


def get_weather_advisory(city: str, plan: str) -> str:
    """
    Generate a lightweight local advisory for an outdoor or travel plan in a city.
    """
    normalized_plan = plan.strip().lower()
    if any(keyword in normalized_plan for keyword in ["run", "walk", "hike", "outdoor"]):
        return (
            f"For {city}, suggest breathable clothing, water, and a quick rain check before the {plan}. "
            "If showers are expected, shift the activity earlier in the day."
        )

    if any(keyword in normalized_plan for keyword in ["commute", "drive", "ride"]):
        return (
            f"For {city}, keep a compact umbrella and allow extra travel time for the {plan}. "
            "Weather changes can affect traffic and visibility."
        )

    return (
        f"For {city}, check the latest forecast before the {plan} and prepare layers, hydration, "
        "and rain protection depending on the expected conditions."
    )


advisory_agent = LlmAgent(
    name="WeatherAdvisoryAgent",
    description="An agent that provides practical weather advice for plans and daily activities.",
    model=WEATHER_ORCHESTRATOR_MODEL,
    tools=[get_weather_advisory],
)

weather_service_agent = RemoteA2aAgent(
    name="WeatherLookupAgent",
    description="An agent that can look up current weather and forecasts using a remote weather service.",
    agent_card=f"http://{WEATHER_A2A_HOST}:{WEATHER_A2A_PORT}{WEATHER_A2A_ROUTE}{AGENT_CARD_WELL_KNOWN_PATH}",
)

root_agent = LlmAgent(
    name="WeatherOrchestratorAgent",
    description="This agent combines weather lookup with practical local advice for the user.",
    model=WEATHER_ORCHESTRATOR_MODEL,
    instruction="""
    You are a helpful weather assistant.
    Use the remote weather agent for facts about current conditions and forecasts.
    Use the advisory agent when the user asks what to wear, carry, or plan around the weather.
    """,
    sub_agents=[weather_service_agent, advisory_agent],
)
