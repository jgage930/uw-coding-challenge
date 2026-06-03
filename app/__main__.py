import os

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


def get_station(client: ApiClient, station_id: str) -> Station:
    r = client.get(f"stations/{station_id}")
    return Station(**r.json())


def run():
    wisconet_client = ApiClient("https://wisconet.wisc.edu/api/v1")
    stations = ["OJNR", "DFRC", "ALTN"]
    station = get_station(wisconet_client, stations[0])
    print(station)


if __name__ == "__main__":
    load_dotenv()

    run()
