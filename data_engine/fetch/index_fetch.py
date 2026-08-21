import pandas as pd
import time
from pathlib import Path
from config.paths import RAW_DATA_DIR

# This example uses Tushare; replace these API calls for another data source.
import tushare as ts

def fetch_index_data(start_date: str, end_date: str, token: str = None):
    """
    Fetches daily data for major market indices to serve as benchmarks.
    """
    print("=" * 40)
    print("📊 Fetching Market Benchmark Indices")
    print("=" * 40)
    
    # Initialize Tushare Pro; a shared pro instance could also be passed in.
    if token:
        ts.set_token(token)
    pro = ts.pro_api()

    # Major benchmarks: SSE Composite, SZSE Component, CSI 300, and CSI 500.
    target_indices = {
        "000001.SH": "SSE_Composite",  # Shanghai Stock Exchange Composite
        "399001.SZ": "SZSE_Component", # Shenzhen Stock Exchange Component
        "000300.SH": "CSI_300",        # CSI 300
        "000905.SH": "CSI_500"         # CSI 500
    }

    # Use a dedicated index directory to avoid mixing data with individual stocks.
    index_dir = RAW_DATA_DIR / "indices"
    index_dir.mkdir(parents=True, exist_ok=True)

    for ts_code, name in target_indices.items():
        print(f"Fetching {name} ({ts_code})...")
        try:
            # Tushare provides index data through index_daily.
            df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                print(f"⚠️ No data returned for {ts_code}")
                continue
                
            # Standardize the date format to match the stock-price panel.
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.normalize()
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # Save as Parquet.
            out_file = index_dir / f"{ts_code}.parquet"
            df.to_parquet(out_file, index=False)
            print(f"✅ Saved {ts_code} -> {out_file.name} ({len(df)} days)")
            
            # Protect against API rate limits.
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"❌ Failed to fetch {ts_code}: {e}")

    print("Index fetching complete.")
