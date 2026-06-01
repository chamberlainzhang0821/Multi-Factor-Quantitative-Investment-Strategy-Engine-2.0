import pandas as pd
import time
from pathlib import Path
from config.paths import RAW_DATA_DIR

# 假设你使用的是 tushare，如果你用的是其他数据源，只需替换这里的 API 调用
import tushare as ts

def fetch_index_data(start_date: str, end_date: str, token: str = None):
    """
    Fetches daily data for major market indices to serve as benchmarks.
    """
    print("=" * 40)
    print("📊 Fetching Market Benchmark Indices")
    print("=" * 40)
    
    # 初始化 Tushare Pro (如果你有全局的 pro 实例，可以直接传进来)
    if token:
        ts.set_token(token)
    pro = ts.pro_api()

    # 我们最常用的三大裁判：上证指数、深证成指、沪深300。还可以加上中证500(000905.SH)
    target_indices = {
        "000001.SH": "SSE_Composite",  # 上证
        "399001.SZ": "SZSE_Component", # 深证
        "000300.SH": "CSI_300",        # 沪深300
        "000905.SH": "CSI_500"         # 中证500
    }

    # 创建独立的指数存储目录，避免和个股混淆
    index_dir = RAW_DATA_DIR / "indices"
    index_dir.mkdir(parents=True, exist_ok=True)

    for ts_code, name in target_indices.items():
        print(f"Fetching {name} ({ts_code})...")
        try:
            # Tushare 抓取指数的接口是 index_daily
            df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                print(f"⚠️ No data returned for {ts_code}")
                continue
                
            # 标准化列名和日期格式，和你的股价 panel 保持一致
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.normalize()
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 存为 Parquet
            out_file = index_dir / f"{ts_code}.parquet"
            df.to_parquet(out_file, index=False)
            print(f"✅ Saved {ts_code} -> {out_file.name} ({len(df)} days)")
            
            # API 限流保护
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"❌ Failed to fetch {ts_code}: {e}")

    print("Index fetching complete.")