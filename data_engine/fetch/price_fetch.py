import time
import tushare as ts
import pandas as pd

from datetime import datetime,timedelta
from pathlib import Path

from config.paths import RAW_DATA_DIR
from config.strategy_config import DURATION_DAYS

pro=ts.pro_api()


def fetch_price():

    price_dir=RAW_DATA_DIR/"daily_cross_section"

    price_dir.mkdir(
      parents=True,
      exist_ok=True
    )

    today=datetime.today()
    start_day=(
        today - timedelta(days=DURATION_DAYS)
    ).strftime("%Y%m%d")

    end_day = datetime.today()

    cal=pro.trade_cal(
      exchange='SSE',
      is_open='1',
      start_date=start_day,
      end_date=end_day.strftime("%Y%m%d")
    )


    trade_dates=cal.cal_date.tolist()


    for i,d in enumerate(trade_dates):

        fname=price_dir/f"{d}.parquet"

        # checkpoint
        if fname.exists():
            print(f"{d} exists, skipping.")
            fetched=0
            skipped=0
            continue
        

        try:

            print(
             f"{i+1}/{len(trade_dates)} {d}"
            )

            df=pro.daily(
               trade_date=d
            )

            if df.empty:
                continue

            df.to_parquet(
                fname,
                index=False
            )

            # audit csv sample
            if i<3:
                df.head(100).to_csv(
                   price_dir/f"{d}_sample.csv",
                   index=False
                )


            # batching
            if i%20==0:
                time.sleep(3)

            print(f"Fetched:{fetched}, Skipped:{skipped}")        

        except Exception as e:

            print(d,e)

            time.sleep(5)
   