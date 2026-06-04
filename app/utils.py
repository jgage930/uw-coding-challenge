import json
from ast import Break
from datetime import date, timedelta

from pydantic import BaseModel


def pretty_print_json(input: dict):
    pretty = json.dumps(input, indent=4)
    print(pretty)


def generate_date_range(start: date, lookback: int) -> list[date]:
    """
    Generate a range of dates starting at start going back a number of days equal to
    lookback.

    Example:
        >> generate_date_range(date(year=2026, month=6, day=2), 4)
        [
           date(year=2026, month=6, day=2),
           date(year=2026, month=6, day=1),
           date(year=2026, month=5, day=31),
           date(year=2026, month=5, day=30),
        ]

    Args:
        - start: The date to start from.
        - lookback: The number of days to lookback to.

    Returns:
        A list of dates starting at start.
    """
    dates = []
    for i in range(lookback):
        dates.append(start - timedelta(days=i))
    return dates


class AqiRange(BaseModel):
    min: int
    max: int


def aqi_category_range(category_number: int) -> AqiRange:
    """
    Get the range of the aqi values for a certain Air Now aqi category.

        1: Good
        2: Moderate
        3: Unhealthy for Sensitive Groups
        4: Unhealthy
        5: Very Unhealthy
        6: Hazardous

    Args:
        - category_number: The number that defines the category. See table above.

    Returns:
        The Min and Max values for the aqirange.

    Raises:
        Value error with the category_number is invalid.  (Should always use with a valid number category)
    """
    range_map = {
        1: AqiRange(min=0, max=50),
        2: AqiRange(min=51, max=100),
        3: AqiRange(min=101, max=150),
        4: AqiRange(min=151, max=200),
        5: AqiRange(min=201, max=300),
        6: AqiRange(min=301, max=500),
    }
    return range_map[category_number]


class BreakPoint(BaseModel):
    min: float
    max: float


def ozone_breakpoints(category_number: int) -> BreakPoint:
    """
    Get the min and max breakpoint values for an AirNow aqi range.
    Only supports the first up to Very Unhealthy. Beyond that the 1 hour
    values are needed.  Not going to support that since it was not asked for.

    Returns

    Args:
        - category_number: The number that defines the category.

    Returns:
        The min and max breakpoints value in units of parts per million (ppm).

    Raises:
        Value error with the category_number is invalid.  (Should always use with a valid number category)
    """
    break_point_map = {
        1: BreakPoint(min=0.0, max=0.054),
        2: BreakPoint(min=0.055, max=0.070),
        3: BreakPoint(min=0.071, max=0.085),
        4: BreakPoint(min=0.086, max=0.105),
        5: BreakPoint(min=0.106, max=0.2),
    }
    return break_point_map[category_number]


def pm25_breakpoints(category_number: int) -> BreakPoint:
    break_point_map = {
        1: BreakPoint(min=0.0, max=12.0),
        2: BreakPoint(min=12.1, max=35.4),
        3: BreakPoint(min=35.5, max=55.4),
        4: BreakPoint(min=55.5, max=150.4),
        5: BreakPoint(min=150.5, max=250.4),
        6: BreakPoint(min=250.5, max=500.4),
    }
    return break_point_map[category_number]


def convert_to_concentration(
    aqi: int, aqi_range: AqiRange, breakpoint: BreakPoint
) -> float:
    """
    Convert from AQI to concentration.
    """
    c_p = (aqi - aqi_range.min) * ((breakpoint.max - breakpoint.min) / (aqi_range.max - aqi_range.min)) + breakpoint.min  # fmt: skip
    return c_p


def convert_ozone(aqi: int, category_number: int) -> float:
    aqi_range = aqi_category_range(category_number)
    breakpoint = ozone_breakpoints(category_number)
    return convert_to_concentration(aqi, aqi_range, breakpoint)


def convert_pm25(aqi: int, category_number: int) -> float:
    aqi_range = aqi_category_range(category_number)
    breakpoint = pm25_breakpoints(category_number)
    return convert_to_concentration(aqi, aqi_range, breakpoint)
