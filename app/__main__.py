import io
import os
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

from .client import ApiClient
from .utils import pretty_print_json


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


def fetch_air_quality_data(station: Station, date: date) -> pd.DataFrame:
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


def run():
    wisconet_client = ApiClient("https://wisconet.wisc.edu/api/v1")

    stations = ["OJNR", "DFRC", "ALTN"]

    station = fetch_station(wisconet_client, stations[0])
    air_quality_data = fetch_air_quality_data(station, date(month=6, day=1, year=2026))
    print(air_quality_data)


if __name__ == "__main__":
    load_dotenv()

    run()
