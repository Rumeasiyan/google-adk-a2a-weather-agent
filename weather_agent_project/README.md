# Weather Agent Project

This project mirrors the structure of the existing Google ADK A2A sample, but changes the domain from travel booking to weather assistance.

## Project layout

```text
weather_agent_project/
├── .env
├── .env.example
├── README.md
├── requirements.txt
└── weather_a2a/
    ├── __init__.py
    ├── weather_agent/
    │   ├── __init__.py
    │   ├── agent.py
    │   └── remote/
    │       ├── __init__.py
    │       └── agent.py
    ├── weather_agent_card/
    │   ├── __init__.py
    │   ├── agent.py
    │   └── remote/
    │       └── weather/
    │           ├── __init__.py
    │           ├── agent.py
    │           └── agent.json
    └── weather_agent_card_sub/
        ├── __init__.py
        ├── agent.py
        └── remote/
            └── weather/
                ├── __init__.py
                ├── agent.py
                └── agent.json
```

## What each package does

- `weather_agent`: a direct `RemoteA2aAgent` wrapper that reads the standard agent card endpoint.
- `weather_agent/remote`: the runnable weather A2A service with current weather and forecast tools.
- `weather_agent_card`: a `RemoteA2aAgent` wrapper that points to a route-specific agent card.
- `weather_agent_card_sub`: an orchestrator that combines the remote weather agent with a local advisory tool.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Update `.env` with your Google API key.
4. Optionally add a real `WEATHER_API_KEY`.

If `WEATHER_API_KEY` is left as `demo`, the service falls back to built-in mock weather data so the project still runs end-to-end.

## Running the remote weather service

From the `weather_agent_project` directory:

```bash
python -m weather_a2a.weather_agent.remote.agent
```

This starts the A2A weather service on the port configured in `.env` (default `8091`).

## Using the agent packages

The main package entrypoints follow the same pattern as the original project:

- `weather_a2a.weather_agent.agent`
- `weather_a2a.weather_agent_card.agent`
- `weather_a2a.weather_agent_card_sub.agent`

Each module exposes a `root_agent` object compatible with Google ADK.

## Notes

- The remote weather service supports live API calls when `WEATHER_API_KEY` is configured.
- The `agent.json` files describe the remote weather service for card-based discovery.
- Ports, model names, hostnames, and the default city are all environment-driven.
