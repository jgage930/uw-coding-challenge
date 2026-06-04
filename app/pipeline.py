import io
import os
from datetime import date, datetime
from typing import Literal

import pandas as pd
import requests
from loguru import logger
from pydantic import BaseModel, Field

from .utils import convert_ozone, convert_pm25, generate_date_range


class Station(BaseModel):
    station_name: str
    latitude: float
    longitude: float


def fetch_daily_air_quality_data(station: Station, date: date) -> pd.DataFrame:
    url = "https://airnowapi.org/aq/forecast/latLong"
    r = requests.get(
        url=url,
        params={
            "format": "text/csv",
            "latitude": station.latitude,
            "longitude": station.longitude,
            "date": date.strftime("%Y-%m-%d"),
            "API_KEY": os.environ["AIRNOW_API_KEY"],
        },
    )
    r.raise_for_status()

    buffer = io.StringIO(r.text)
    return pd.read_csv(buffer)


def fetch_past_air_quality_data(station: Station, days: int) -> pd.DataFrame:
    start = date.today()
    date_range = generate_date_range(start, 7)
    dfs = [fetch_daily_air_quality_data(station, date) for date in date_range]
    return pd.concat(dfs, ignore_index=True)


def fetch_station(station_id: str) -> Station:
    r = requests.get(url=f"https://wisconet.wisc.edu/api/v1/stations/{station_id}")
    r.raise_for_status()
    return Station(**r.json())


def convert_row(row: pd.Series) -> pd.Series:
    aqi = row["AQI"]
    category_number = row["CategoryNumber"]
    parameter_name = row["ParameterName"]

    if parameter_name == "PM2.5":
        row["Concentration"] = convert_pm25(aqi, category_number)

    if parameter_name == "O3":
        row["Concentration"] = convert_ozone(aqi, category_number)

    return row


class Report(BaseModel):
    station_id: str
    date_: date = Field(default_factory=date.today)
    days: int = Field(
        description="Number of days included in the range. Start with start and looks back."
    )
    pollutant_type: Literal["PM2.5", "O3"]
    units: str
    average: float
    min: float
    max: float


def run_aqi_data_pipeline(station_id: str, days: int):
    logger.info(f"Fetching station info for: {station_id}...")
    station = fetch_station(station_id)

    logger.info(f"Fetching AQI data for the past {days} days...")
    aqi_df = fetch_past_air_quality_data(station, days)

    logger.info("Calculating concentrations...")
    concentration_df = aqi_df.apply(convert_row, axis=1)

    logger.info("Building reports for PM2.5 data...")
    pm_25_df = concentration_df[concentration_df["ParameterName"] == "PM2.5"]
    pm_25_report = Report(
        station_id=station_id,
        days=days,
        pollutant_type="PM2.5",
        units="micrograms per cubic meter",
        average=pm_25_df["Concentration"].mean(),
        min=pm_25_df["Concentration"].min(),
        max=pm_25_df["Concentration"].max(),
    )

    logger.info("Building reports for O3 data...")
    ozone_df = concentration_df[concentration_df["ParameterName"] == "O3"]
    ozone_report = Report(
        station_id=station_id,
        days=days,
        pollutant_type="O3",
        units="parts per million",
        average=ozone_df["Concentration"].mean(),
        min=ozone_df["Concentration"].min(),
        max=ozone_df["Concentration"].max(),
    )

    print(pm_25_report)
    print(ozone_report)
