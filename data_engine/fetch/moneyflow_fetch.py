import time
import tushare as ts
import pandas as pd

from datetime import datetime,timedelta

from config.paths import RAW_DATA_DIR
from config.strategy_config import DURATION_DAYS


pro=ts.pro_api()


def fetch_moneyflow():

    flow_dir=RAW_DATA_DIR/"moneyflow"

    flow_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # ------------------------
    # rolling 2-year window
    # ------------------------

    end_day=datetime.today()

    start_day=(
        end_day-timedelta(days=DURATION_DAYS)
    ).strftime("%Y%m%d")


    cal=pro.trade_cal(
        exchange='SSE',
        is_open='1',
        start_date=start_day,
        end_date=end_day.strftime("%Y%m%d")
    )

    trade_dates=cal.cal_date.tolist()


    for i,d in enumerate(trade_dates):

        fname=flow_dir/f"{d}.parquet"


        # ------------------
        # checkpoint
        # ------------------

        if fname.exists():
            continue


        try:

            print(
                f"{i+1}/{len(trade_dates)} {d}"
            )


            # full-market moneyflow
            df=pro.moneyflow(
                trade_date=d
            )


            if df.empty:
                continue


            df.to_parquet(
                fname,
                index=False
            )


            # audit csv preview
            if i<3:
                df.head(100).to_csv(
                    flow_dir/f"{d}_sample.csv",
                    index=False
                )


            # batching
            if i%20==0:
                time.sleep(2)


        except Exception as e:

            print(
                f"{d} failed: {e}"
            )

            time.sleep(2)


    print("Moneyflow fetched.")