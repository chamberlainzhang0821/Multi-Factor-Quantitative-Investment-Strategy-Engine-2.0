def golden_cross_factor(df):
    print("Calculating golden cross score...")
    
    ma50 = df.groupby("ts_code")["close"].transform(lambda x: x.rolling(50).mean())
    ma200 = df.groupby("ts_code")["close"].transform(lambda x: x.rolling(200).mean())

    cross = (ma50.shift(1) <= ma200.shift(1)) & (ma50 > ma200)
    # 注意：shift 也必须 groupby，否则会把上一只股票的最后一天 shift 过来
    cross = (
        df.groupby("ts_code").apply(
            lambda x: (x['close'].rolling(50).mean().shift(1) <= x['close'].rolling(200).mean().shift(1)) &
                      (x['close'].rolling(50).mean() > x['close'].rolling(200).mean())
        ).reset_index(level=0, drop=True)
    ) # 更安全的做法
    
    df['trend_score'] = cross.astype(int) * 4
    return df