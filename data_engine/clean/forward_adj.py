import tushare as ts
import pandas as pd
import numpy as np

def get_adj_factor_panel(raw_adj_dir):
    """
    安全防污染版：屏蔽掉因网络崩溃产生的无效/零值/空值最新因子
    """
    adj_files = sorted(raw_adj_dir.glob("*.parquet"))
    if not adj_files:
        return pd.DataFrame(), pd.Series(dtype='float64')
    
    print(f"Loading {len(adj_files)} adjustment factor files to build global cache...")
    all_adj_frames = [pd.read_parquet(f)[['ts_code', 'trade_date', 'adj_factor']] for f in adj_files]
    df_all_adj = pd.concat(all_adj_frames)
    
    # 1. 强行排序
    df_all_adj = df_all_adj.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    
    # 2. 🚨【核心防御】：在计算全局最新因子前，必须把 NaN 和 异常的 0 或 1.0 过滤掉！
    # 只在有明确有效因子的数据集里找最后一天，防止被最近3天的网络垃圾数据污染历史
    valid_adj = df_all_adj[
        df_all_adj["adj_factor"].notna() & 
        (df_all_adj["adj_factor"] > 0)
    ]
    
    # 提取真正有效的最新因子基准
    latest_factors_series = valid_adj.groupby("ts_code")["adj_factor"].last()
    
    return df_all_adj, latest_factors_series


def apply_price_adjustment_panel(df_price_panel, df_all_adj, latest_factors_series):
    """
    全量面板复权逻辑：彻底解决单日数据缺失导致的 -90% 暴跌问题。
    """
    print("Applying panel-level price adjustment...")
    
    if df_all_adj.empty or df_price_panel.empty:
        return df_price_panel

    # 🚨【核心修复】：强制统一时间列的数据类型，消灭 ValueError
    df_price_panel['trade_date'] = pd.to_datetime(df_price_panel['trade_date'])
    df_all_adj['trade_date'] = pd.to_datetime(df_all_adj['trade_date'])

    # 1. 将全量复权因子左连接到价格面板上
    df = pd.merge(
        df_price_panel, 
        df_all_adj[['ts_code', 'trade_date', 'adj_factor']], 
        on=['ts_code', 'trade_date'], 
        how='left'
    )
    
    # 2. 排序后，按股票分组，向下填充缺失的复权因子
    df = df.sort_values(["ts_code", "trade_date"])
    df['adj_factor'] = df.groupby('ts_code')['adj_factor'].ffill()
    
    # 3. 极限排雷：如果连第一天都缺失，则向上填充
    df['adj_factor'] = df.groupby('ts_code')['adj_factor'].bfill()
    
    # 4. 映射全局最新因子
    df['latest_factor'] = df['ts_code'].map(latest_factors_series)
    
    # 5. 计算复权比例
    df['adj_ratio'] = df['adj_factor'] / df['latest_factor']
    df['adj_ratio'] = df['adj_ratio'].fillna(1.0)
    
    # 6. 价格类复权 (乘积)
    price_cols = ["open", "high", "low", "close", "pre_close"]
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col] * df['adj_ratio']
            
    # 7. 成交量复权 (除法，保证 Amount 不变)
    if 'vol' in df.columns:
        df['vol'] = df['vol'] / df['adj_ratio']
        
    # 清理并返回
    drop_cols = ['adj_factor', 'latest_factor', 'adj_ratio']
    return df.drop(columns=[c for c in drop_cols if c in df.columns])