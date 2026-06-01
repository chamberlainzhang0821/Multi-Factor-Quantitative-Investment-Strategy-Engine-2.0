

    # data_engine/fetch/adj_factor_fetch.py

import time
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from config.paths import RAW_DATA_DIR
from config.strategy_config import DURATION_DAYS

pro = ts.pro_api()

def fetch_adj_factor():
    adj_dir = RAW_DATA_DIR / "adj_factor"
    adj_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.today()
    start_day = (today - timedelta(days=DURATION_DAYS)).strftime("%Y%m%d")
    end_day = today

    cal = pro.trade_cal(
        exchange='SSE',
        is_open='1',
        start_date=start_day,
        end_date=end_day.strftime("%Y%m%d")
    )
    trade_dates = cal.cal_date.tolist()

    for i, d in enumerate(trade_dates):
        fname = adj_dir / f"{d}.parquet"

        # Checkpoint
        if fname.exists():
            continue

        try:
            print(f"{i+1}/{len(trade_dates)} Fetching adj_factor for {d}")
            
            df = pro.adj_factor(trade_date=d)

            if df.empty:
                continue

            df.to_parquet(fname, index=False)

            # batching
            if i % 20 == 0:
                time.sleep(3)

        except Exception as e:
            print(f"{d} adj_factor failed: {e}")
            time.sleep(3)
            
    print("Adj_factor fetched.")

if __name__=="__main__":
    fetch_adj_factor()