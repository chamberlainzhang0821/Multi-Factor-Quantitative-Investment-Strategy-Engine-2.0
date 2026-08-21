from datetime import datetime

from data_engine.fetch.adj_factor import fetch_adj_factor
from data_engine.fetch.universe_fetch import fetch_universe
from data_engine.fetch.price_fetch import fetch_price
from data_engine.fetch.sector_fetch import fetch_sector
from data_engine.fetch.moneyflow_fetch import fetch_moneyflow
# Import the index-fetching function.
from data_engine.fetch.index_fetch import fetch_index_data


def log(msg):
    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    print(f"[{now}] {msg}")


# Wrap the parameterized function so it fits the no-argument function loop below.
def fetch_index_wrapper():
    # Keep these dates consistent with the global price-fetch configuration.
    # If available, use values such as start_date=config.START_DATE instead.
    fetch_index_data(start_date="20210101", end_date="20260502")


def run_fetch_pipeline():
    try:
        log("Data fetch pipeline started.")

        FETCH_STEPS = [
            ("Universe", fetch_universe),
            ("Prices", fetch_price),
            ("Adj_Factor", fetch_adj_factor),
            ("Sector", fetch_sector),
            ("Moneyflow", fetch_moneyflow),
            ("Indices", fetch_index_wrapper),  # Fetch benchmark indices as the final step
        ]

        for name, func in FETCH_STEPS:
            log(f"Fetching {name}...")
            func()

        log("Data fetch complete.")

    except Exception as e:
        log(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    run_fetch_pipeline()
