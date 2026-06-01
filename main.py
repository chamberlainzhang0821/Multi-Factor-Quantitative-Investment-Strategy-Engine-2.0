from datetime import datetime

from data_engine.fetch.run_fetch_pipeline import (run_fetch_pipeline)

from data_engine.clean.run_clean_pipeline import (run_clean_pipeline)
from factor_engine.run_factor_pipeline import (run_factor_pipeline)
from signal_engine.rank_signal import (run_alpha_combiner)
from backtest.run_backtest_pipeline import (run_backtest)   


def log(msg):

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print(f"[{now}] {msg}")


def run_pipeline():

    try:
        log("Pipeline started.")

    

        run_fetch_pipeline()

        log("Data clean pipeline started.")

        run_clean_pipeline()

        log("Factor pipeline started.")

        run_factor_pipeline()

        log("Alpha combination started.")

        run_alpha_combiner()

        log("Backtest pipeline started.")

        run_backtest()

        log("Pipeline complete.")


        
        



    except Exception as e:

        log(f"ERROR: {e}")

        raise


if __name__=="__main__":
    run_pipeline()