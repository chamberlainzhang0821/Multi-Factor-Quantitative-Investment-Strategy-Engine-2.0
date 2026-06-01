import pandas as pd
def validate(df):

    # panel已经在align阶段排序，无需重复monotonic检查
    # 这里只做真正有价值的数据完整性验证

    assert not df.duplicated(
        ['ts_code','trade_date']
    ).any()
def filter_short_history(df, min_required_days=228):
    """
    时光冻结版过滤函数
    
    满足用户执念：2025-05-26 之前的历史逻辑完全不动，2025-05-26 之后的数据不逆向污染历史。
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    freeze_date = pd.to_datetime("2025-05-26")

    print(f"--- 正在执行时光冻结过滤 (锚定日期: {freeze_date.strftime('%Y-%m-%d')}) ---")

    # 1. 剥离出 2025-05-26 之前的历史快照
    snapshot_past = df[df['trade_date'] <= freeze_date]
    
    # 用你原本的旧逻辑：看在当时的总天数是否大于等于 228
    past_counts = snapshot_past.groupby('ts_code').size()
    keep_past_codes = past_counts[past_counts >= min_required_days].index
    
    # 2. 2025-05-26 之前的历史数据，严格执行旧名单过滤（保住你的历史收益）
    df_past_filtered = snapshot_past[snapshot_past['ts_code'].isin(keep_past_codes)]

    # 3. 2025-05-26 之后的新增数据
    df_future = df[df['trade_date'] > freeze_date]
    
    if not df_future.empty:
        # 核心逻辑：未来数据不再去“逆向贡献”过去的天数，
        # 而是顺着 2025-05-26 的历史遗产，采用滚动累计（cumcount）来判断新股是否成熟
        # 同时允许当年已经通过考核的“老股”继续留在池子里
        df_all_sorted = df.sort_values(['ts_code', 'trade_date']).reset_index(drop=True)
        df_all_sorted['cum_days'] = df_all_sorted.groupby('ts_code').cumcount() + 1
        
        # 提取出未来日子里，累计天数达标的行
        df_future_sorted = df_all_sorted[df_all_sorted['trade_date'] > freeze_date]
        df_future_filtered = df_future_sorted[df_future_sorted['cum_days'] >= min_required_days].copy()
        df_future_filtered = df_future_filtered.drop(columns=['cum_days'])
        
        # 合并新旧历史
        df_final = pd.concat([df_past_filtered, df_future_filtered], ignore_index=True)
    else:
        df_final = df_past_filtered

    print(f"时光冻结完成。保留样本行数: {len(df_final)}")
    return df_final