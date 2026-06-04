import io
import os
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from urllib3 import request

from .client import ApiClient
from .utils import generate_date_range, pretty_print_json


def fetch_all_stations() -> dict:
    wisconet_client = ApiClient("https://wisconet.wisc.edu/api/v1")
    r = wisconet_client.get("stations/")
    r.raise_for_status()
    return r.json()


class Station(BaseModel):
    station_name: str
    latitude: float
    longitude: float


def fetch_station(client: ApiClient, station_id: str) -> Station:
    r = client.get(f"stations/{station_id}")
    return Station(**r.json())


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

    buffer = io.StringIO(r.text)
    return pd.read_csv(buffer)


def fetch_weekly_air_quality_data(station: Station) -> pd.DataFrame:
    start = date.today()
    date_range = generate_date_range(start, 7)
    dfs = [fetch_daily_air_quality_data(station, date) for date in date_range]
    return pd.concat(dfs, ignore_index=True)


def run():
    wisconet_client = ApiClient("https://wisconet.wisc.edu/api/v1")
    stations = ["OJNR", "DFRC", "ALTN"]

    station = fetch_station(wisconet_client, stations[0])
    df = fetch_weekly_air_quality_data(station)
    print(df)

    df.to_csv("aqi-data.csv")


if __name__ == "__main__":
    load_dotenv()

    run()
