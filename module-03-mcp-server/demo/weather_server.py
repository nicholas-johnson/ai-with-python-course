"""
Module 3 Demo — Weather MCP Server
A local stdio MCP server that looks up current weather.

Run directly:  python weather_server.py   (starts an MCP stdio server)
Used by:       test_weather_server.py and demo.py (part 5) connect to this server.

Place names are resolved with Open-Meteo geocoding. Forecasts come from
the Norwegian Meteorological Institute (api.met.no). Neither needs an API key.
"""

import json
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from mcp.server.mcpserver import MCPServer

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

server = MCPServer("Weather")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
TIMEOUT = 10.0
USER_AGENT = "pathfinder-weather-mcp/1.0 (ai-python-course demo)"

# symbol_code values from api.met.no, without the _day / _night suffix.
CONDITIONS = {
    "clearsky": "clear",
    "fair": "mainly clear",
    "partlycloudy": "partly cloudy",
    "cloudy": "overcast",
    "fog": "fog",
    "lightrain": "light rain",
    "rain": "rain",
    "heavyrain": "heavy rain",
    "lightrainshowers": "light showers",
    "rainshowers": "showers",
    "heavyrainshowers": "heavy showers",
    "lightsleet": "light sleet",
    "sleet": "sleet",
    "heavysleet": "heavy sleet",
    "lightsnow": "light snow",
    "snow": "snow",
    "heavysnow": "heavy snow",
    "lightsnowshowers": "light snow showers",
    "snowshowers": "snow showers",
    "heavysnowshowers": "heavy snow showers",
    "lightrainandthunder": "thunderstorm",
    "rainandthunder": "thunderstorm",
    "heavyrainandthunder": "heavy thunderstorm",
    "lightrainshowersandthunder": "thunderstorm",
    "rainshowersandthunder": "thunderstorm",
    "heavyrainshowersandthunder": "heavy thunderstorm",
    "sleetandthunder": "sleet and thunder",
    "lightsnowandthunder": "snow and thunder",
    "snowandthunder": "snow and thunder",
    "heavysnowandthunder": "heavy snow and thunder",
}


def _error(message: str) -> str:
    return json.dumps({"error": message})


def _condition(symbol_code: str | None) -> str:
    if not symbol_code:
        return "unknown"
    base = symbol_code.split("_", 1)[0]
    return CONDITIONS.get(base, base)


def _local(iso_time: str, tz_name: str | None) -> datetime:
    moment = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    if not tz_name:
        return moment
    try:
        return moment.astimezone(ZoneInfo(tz_name))
    except (KeyError, ValueError):
        return moment


def _temperature(celsius: float, units: str) -> float:
    if units == "fahrenheit":
        return round(celsius * 9 / 5 + 32, 1)
    return round(celsius, 1)


def _wind(meters_per_second: float, units: str) -> float:
    if units == "fahrenheit":
        return round(meters_per_second * 2.23694, 1)
    return round(meters_per_second * 3.6, 1)


def _symbol(entry: dict) -> str | None:
    data = entry.get("data") or {}
    for window in ("next_1_hours", "next_6_hours", "next_12_hours"):
        code = ((data.get(window) or {}).get("summary") or {}).get("symbol_code")
        if code:
            return code
    return None


def _details(entry: dict) -> dict:
    return ((entry.get("data") or {}).get("instant") or {}).get("details") or {}


def _geocode(client: httpx.Client, location: str) -> dict | None:
    response = client.get(
        GEOCODE_URL,
        params={"name": location, "count": 1, "language": "en", "format": "json"},
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    return results[0] if results else None


def _forecast(client: httpx.Client, place: dict) -> list[dict]:
    response = client.get(
        FORECAST_URL,
        params={
            "lat": round(place["latitude"], 4),
            "lon": round(place["longitude"], 4),
        },
    )
    response.raise_for_status()
    return response.json()["properties"]["timeseries"]


def _outlook(timeseries: list[dict], tz_name: str | None, units: str) -> list[dict]:
    by_day: dict[str, list[dict]] = {}
    for entry in timeseries:
        day = _local(entry["time"], tz_name).date().isoformat()
        by_day.setdefault(day, []).append(entry)

    outlook = []
    for day, entries in list(by_day.items())[:3]:
        temps = [
            _details(entry)["air_temperature"]
            for entry in entries
            if _details(entry).get("air_temperature") is not None
        ]
        noon = min(entries, key=lambda entry: abs(_local(entry["time"], tz_name).hour - 12))
        outlook.append({
            "date": day,
            "condition": _condition(_symbol(noon)),
            "high": _temperature(max(temps), units) if temps else None,
            "low": _temperature(min(temps), units) if temps else None,
        })
    return outlook


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool()
def get_weather(location: str, units: str = "celsius") -> str:
    """Get the current weather and a 3-day outlook for a city or place.

    location: city or place name, such as "London" or "Austin, Texas".
    units: "celsius" or "fahrenheit". Defaults to celsius.
    """
    location = location.strip()
    if not location:
        return _error("location is required")

    units = units.lower().strip()
    if units not in ("celsius", "fahrenheit"):
        return _error("units must be 'celsius' or 'fahrenheit'")

    wind_label = "km/h" if units == "celsius" else "mph"

    try:
        headers = {"User-Agent": USER_AGENT}
        with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
            place = _geocode(client, location)
            if not place:
                return _error(f"Could not find a place named {location!r}")
            timeseries = _forecast(client, place)
    except httpx.HTTPStatusError as exc:
        return _error(f"Weather lookup failed ({exc.response.status_code})")
    except httpx.HTTPError:
        return _error("Weather lookup failed: could not reach the weather service")

    if not timeseries:
        return _error(f"No forecast available for {location!r}")

    tz_name = place.get("timezone")
    now = timeseries[0]
    current = _details(now)
    observed = _local(now["time"], tz_name)

    name_parts = [place.get("name") or location]
    if place.get("admin1"):
        name_parts.append(place["admin1"])
    if place.get("country"):
        name_parts.append(place["country"])

    return json.dumps({
        "location": ", ".join(name_parts),
        "latitude": place.get("latitude"),
        "longitude": place.get("longitude"),
        "time": observed.isoformat(timespec="minutes"),
        "condition": _condition(_symbol(now)),
        "temperature": _temperature(current["air_temperature"], units),
        "units": units,
        "humidity": round(current["relative_humidity"]),
        "wind_speed": _wind(current["wind_speed"], units),
        "wind_units": wind_label,
        "outlook": _outlook(timeseries, tz_name, units),
    })


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Weather MCP server starting…", file=sys.stderr)
    server.run()
