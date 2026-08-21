import time
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from config.paths import RAW_DATA_DIR
from config.strategy_config import DURATION_DAYS

pro = ts.pro_api()

def fetch_sector():
    level1_file = RAW_DATA_DIR / "sw_level1.parquet"
    level2_file = RAW_DATA_DIR / "sw_level2.parquet"
    member_file = RAW_DATA_DIR / "sw_members.parquet"
    price_file = RAW_DATA_DIR / "sw_index_prices.parquet"

    # ------------------------
    # 1. Sector Classification
    # ------------------------
    if level1_file.exists() and level2_file.exists():
        print("Sector classifications exist, loading from disk...")
        l1 = pd.read_parquet(level1_file)
        l2 = pd.read_parquet(level2_file)
    else:
        print("Fetching sector classifications from Tushare...")
        l1 = pro.index_classify(level="L1", src="SW2021")
        l2 = pro.index_classify(level="L2", src="SW2021")
        l1.to_parquet(level1_file)
        l2.to_parquet(level2_file)

    # Ensure all_codes is defined in every execution path
    all_codes = l1["index_code"].tolist() + l2["index_code"].tolist()

    # ------------------------
    # 2. Stock-Sector Mapping
    # ------------------------
    if member_file.exists():
        print("Sector members exist, skipping.")
    else:
        print("Fetching sector members...")
        member_frames = []
        for code in all_codes:
            try:
                df = pro.index_member(index_code=code)
                if not df.empty:
                    member_frames.append(df)
                    print(f"{code} members fetched.")
                time.sleep(0.2)
            except Exception as e:
                print(f"{code} member failed: {e}")

        if member_frames:
            members = pd.concat(member_frames, ignore_index=True)
            members.to_parquet(member_file)

    # ------------------------
    # 3. Sector index prices (complete 730 days of data)
    # ------------------------
    if price_file.exists():
        # Delete the existing file if it contains less than two years of data,
        # or change this logic to overwrite it unconditionally.
        print("Sector prices exist, skipping.")
    else:
        print("Fetching sector index prices for the last 730 days...")
        
        today = datetime.today()
        start_day = (today - timedelta(days=DURATION_DAYS)).strftime("%Y%m%d")
        end_day = today.strftime("%Y%m%d")

        price_frames = []
        for code in all_codes:
            try:
                df = pro.sw_daily(
                    ts_code=code,
                    start_date=start_day,
                    end_date=end_day
                )
                if df is not None and not df.empty:
                    price_frames.append(df)
                    print(f"{code} prices fetched.")
                time.sleep(0.12) # Slightly faster while remaining safe
            except Exception as e:
                print(f"{code} price failed: {e}")
                # Keep permission and rate-limit error handling unchanged.

        if not price_frames:
            raise RuntimeError("No sector index data fetched.")

        sector_prices = pd.concat(price_frames, ignore_index=True)
        sector_prices.to_parquet(price_file)

    print("Sector fetched successfully.")
