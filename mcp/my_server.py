from fastmcp import FastMCP

from datetime import datetime
from zoneinfo import ZoneInfo

import ast
import operator
import httpx


mcp = FastMCP("utility-server")


# =========================================
# WEATHER TOOL
# =========================================

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


@mcp.tool
async def get_weather(city: str) -> dict:
    """
    Get real current weather for a city.
    """

    try:
        async with httpx.AsyncClient(timeout=10) as client:

            # Step 1: Geocode city -> lat/lon
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1}
            )

            geo_data = geo_resp.json()

            if "results" not in geo_data:
                return {"error": f"City '{city}' not found"}

            location = geo_data["results"][0]

            lat = location["latitude"]
            lon = location["longitude"]

            # Step 2: Weather API
            weather_resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True
                }
            )

            weather_data = weather_resp.json()

            current = weather_data["current_weather"]

            return {
                "city": location["name"],
                "country": location.get("country"),
                "temperature_c": current["temperature"],
                "windspeed_kmh": current["windspeed"],
                "condition": WEATHER_CODES.get(
                    current["weathercode"],
                    "Unknown"
                ),
                "time": current["time"]
            }

    except Exception as e:
        return {"error": str(e)}


# =========================================
# TIME TOOL
# =========================================

@mcp.tool
def get_time(timezone: str = "UTC") -> dict:
    """
    Get current time in a timezone.

    Example:
    - UTC
    - Asia/Tokyo
    - Europe/London
    """

    try:
        now = datetime.now(ZoneInfo(timezone))

        return {
            "timezone": timezone,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "day": now.strftime("%A")
        }

    except Exception:
        return {
            "error": f"Invalid timezone: {timezone}"
        }


# =========================================
# SAFE CALCULATOR
# =========================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_eval(node):

    if isinstance(node, ast.Constant):
        return node.value

    elif isinstance(node, ast.BinOp):

        left = safe_eval(node.left)
        right = safe_eval(node.right)

        return OPERATORS[type(node.op)](left, right)

    elif isinstance(node, ast.UnaryOp):

        operand = safe_eval(node.operand)

        return OPERATORS[type(node.op)](operand)

    raise ValueError("Unsupported expression")


@mcp.tool
def calculate(expression: str) -> dict:
    """
    Safely evaluate a math expression.

    Examples:
    - 2 + 2
    - (5 * 10) / 2
    - 2 ** 8
    """

    try:

        parsed = ast.parse(expression, mode="eval")

        result = safe_eval(parsed.body)

        return {
            "expression": expression,
            "result": result
        }

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================
# SERVER
# =========================================

if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )