from dotenv import load_dotenv

from .pipeline import run_aqi_data_pipeline


def run():
    stations = ["OJNR", "DFRC", "ALTN"]

    run_aqi_data_pipeline(stations[0], 7)


if __name__ == "__main__":
    load_dotenv()
    run()
