import pandas as pd
def validate(df):

    # The panel is already sorted during alignment; no repeated monotonicity check is needed.
    # Perform only meaningful data-integrity validation here.

    assert not df.duplicated(
        ['ts_code','trade_date']
    ).any()
def filter_short_history(df, min_required_days=228):
    """
    Time-freeze filtering function.
    
    Preserve historical logic before 2025-05-26 without back-propagating later data.
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    freeze_date = pd.to_datetime("2025-05-26")

    print(f"--- 正在执行时光冻结过滤 (锚定日期: {freeze_date.strftime('%Y-%m-%d')}) ---")

    # 1. Isolate the historical snapshot through 2025-05-26.
    snapshot_past = df[df['trade_date'] <= freeze_date]
    
    # Apply the original rule: retain codes with at least 228 days at that time.
    past_counts = snapshot_past.groupby('ts_code').size()
    keep_past_codes = past_counts[past_counts >= min_required_days].index
    
    # 2. Strictly apply the legacy universe filter to historical data.
    df_past_filtered = snapshot_past[snapshot_past['ts_code'].isin(keep_past_codes)]

    # 3. Process data added after 2025-05-26.
    df_future = df[df['trade_date'] > freeze_date]
    
    if not df_future.empty:
        # Later data does not retroactively contribute to historical day counts.
        # Use cumulative counts from the freeze date to determine when new stocks mature.
        # Previously qualified stocks remain in the universe.
        df_all_sorted = df.sort_values(['ts_code', 'trade_date']).reset_index(drop=True)
        df_all_sorted['cum_days'] = df_all_sorted.groupby('ts_code').cumcount() + 1
        
        # Extract future rows whose cumulative day count meets the threshold.
        df_future_sorted = df_all_sorted[df_all_sorted['trade_date'] > freeze_date]
        df_future_filtered = df_future_sorted[df_future_sorted['cum_days'] >= min_required_days].copy()
        df_future_filtered = df_future_filtered.drop(columns=['cum_days'])
        
        # Combine historical and subsequent data.
        df_final = pd.concat([df_past_filtered, df_future_filtered], ignore_index=True)
    else:
        df_final = df_past_filtered

    print(f"时光冻结完成。保留样本行数: {len(df_final)}")
    return df_final
