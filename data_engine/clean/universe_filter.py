import tushare as ts
import pandas as pd

pro = ts.pro_api()

def filter_universe(df):
    """
    Filter the full panel universe by removing BJ, STAR, ChiNext, ST, penny stocks, and stocks without sector mappings.
    """
    print(f"Original universe size: {len(df)}")

    # 1. Exclude Beijing Stock Exchange listings (.BJ).
    df = df[~df["ts_code"].str.endswith(".BJ")]

    # 2. Exclude ChiNext (300, 301) and STAR Market (688, 689) listings.
    # The medium- to long-term strategy targets the main board's lower-volatility price limits.
    df = df[~df["ts_code"].str.startswith(("300", "301", "688", "689"))]

    # 3. Exclude penny stocks and securities close to delisting.
    # A-share face-value delisting applies after 20 days below CNY 1; such stocks are unreliable for trend analysis.
    # Use 1.0 or 0.5 as the threshold; this implementation excludes stocks below CNY 1.
    if "close" in df.columns:
        df = df[df["close"] >= 1.0]

    # 4. Exclude stocks without Shenwan sector mappings, such as unindexed new listings.
    # Drop securities that have not been assigned to a sector.
    if "sw_l1" in df.columns:
        df = df.dropna(subset=["sw_l1"])

    # 5. Filter ST stocks with defensive error handling.
    # This uses only the ST list for the final backtest date.
    # A long backtest can miss stocks that were previously ST but later had the designation removed.
    # Consider storing historical ST status as panel data, similar to adj_factor.
    try:
        max_date = pd.to_datetime(df["trade_date"]).max()
        st = pro.stock_st(trade_date=max_date.strftime("%Y%m%d"))
        
        if not st.empty:
            st_codes = set(st["ts_code"])
            df = df[~df["ts_code"].isin(st_codes)]
    except Exception as e:
        print(f"Warning: Failed to fetch ST list. Error: {e}")

    print(f"Filtered universe size: {len(df)}")
    
    return df
