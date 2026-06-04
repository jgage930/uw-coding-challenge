import io
import os
from datetime import date

import pandas as pd
import requests
from loguru import logger
from pydantic import BaseModel

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
    elif parameter_name == "03":
        row["Concentration"] = convert_ozone(aqi, category_number)

    return row


def run_aqi_data_pipeline(station_id: str, days: int):
    logger.info(f"Fetching station info for: {station_id}...")
    station = fetch_station(station_id)

    logger.info(f"Fetching AQI data for the past {days} days...")
    aqi_df = fetch_past_air_quality_data(station, days)

    logger.info("Calculating concentrations...")
    concentration_df = aqi_df.apply(convert_row, axis=1)
    print(concentration_df.to_string())

    logger.info("Building reports for PM2.5 data...")
    pm_25_df = concentration_df[concentration_df["ParameterName"] == "PM2.5"]
    print(pm_25_df)

    logger.info("Buildinf reports for O3 data...")
    ozone_df = concentration_df[concentration_df["ParameterName"] == "O3"]
    print(ozone_df)
