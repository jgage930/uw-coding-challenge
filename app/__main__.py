from dotenv import load_dotenv
from loguru import logger

from .pipeline import run_aqi_data_pipeline

ONE_WEEK = 7


def run():
    stations = ["OJNR", "DFRC", "ALTN"]

    for station in stations:
        run_aqi_data_pipeline(station, ONE_WEEK)
        # try:
        #     run_aqi_data_pipeline(station, ONE_WEEK)
        # except Exception as e:
        #     logger.error(f"Failed to run aqi pipeline for {station}. Due to: {e}")


if __name__ == "__main__":
    load_dotenv()
    run()
