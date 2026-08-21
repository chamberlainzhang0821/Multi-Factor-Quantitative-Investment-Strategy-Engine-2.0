import tushare as ts
import pandas as pd
import numpy as np

def get_adj_factor_panel(raw_adj_dir):
    """
    Safely exclude invalid, zero, or null latest factors caused by failed network requests.
    """
    adj_files = sorted(raw_adj_dir.glob("*.parquet"))
    if not adj_files:
        return pd.DataFrame(), pd.Series(dtype='float64')
    
    print(f"Loading {len(adj_files)} adjustment factor files to build global cache...")
    all_adj_frames = [pd.read_parquet(f)[['ts_code', 'trade_date', 'adj_factor']] for f in adj_files]
    df_all_adj = pd.concat(all_adj_frames)
    
    # 1. Enforce sorting.
    df_all_adj = df_all_adj.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    
    # 2. Core defense: exclude NaN and abnormal zero or 1.0 values before finding the global latest factor.
    # Find the final day only in data with valid factors to avoid corrupting history with failed recent fetches.
    valid_adj = df_all_adj[
        df_all_adj["adj_factor"].notna() & 
        (df_all_adj["adj_factor"] > 0)
    ]
    
    # Extract the latest valid factor baseline.
    latest_factors_series = valid_adj.groupby("ts_code")["adj_factor"].last()
    
    return df_all_adj, latest_factors_series


def apply_price_adjustment_panel(df_price_panel, df_all_adj, latest_factors_series):
    """
    Apply panel-wide price adjustment to prevent artificial -90% drops from missing daily data.
    """
    print("Applying panel-level price adjustment...")
    
    if df_all_adj.empty or df_price_panel.empty:
        return df_price_panel

    # Core fix: standardize date-column types to prevent ValueError.
    df_price_panel['trade_date'] = pd.to_datetime(df_price_panel['trade_date'])
    df_all_adj['trade_date'] = pd.to_datetime(df_all_adj['trade_date'])

    # 1. Left-join all adjustment factors onto the price panel.
    df = pd.merge(
        df_price_panel, 
        df_all_adj[['ts_code', 'trade_date', 'adj_factor']], 
        on=['ts_code', 'trade_date'], 
        how='left'
    )
    
    # 2. Sort and forward-fill missing adjustment factors within each stock.
    df = df.sort_values(["ts_code", "trade_date"])
    df['adj_factor'] = df.groupby('ts_code')['adj_factor'].ffill()
    
    # 3. As a final safeguard, backfill when even the first day is missing.
    df['adj_factor'] = df.groupby('ts_code')['adj_factor'].bfill()
    
    # 4. Map the latest global factors.
    df['latest_factor'] = df['ts_code'].map(latest_factors_series)
    
    # 5. Calculate the adjustment ratio.
    df['adj_ratio'] = df['adj_factor'] / df['latest_factor']
    df['adj_ratio'] = df['adj_ratio'].fillna(1.0)
    
    # 6. Adjust price columns by multiplication.
    price_cols = ["open", "high", "low", "close", "pre_close"]
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col] * df['adj_ratio']
            
    # 7. Adjust volume by division to preserve amount.
    if 'vol' in df.columns:
        df['vol'] = df['vol'] / df['adj_ratio']
        
    # Clean up and return.
    drop_cols = ['adj_factor', 'latest_factor', 'adj_ratio']
    return df.drop(columns=[c for c in drop_cols if c in df.columns])
