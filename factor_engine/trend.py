def golden_cross_factor(df):
    print("Calculating golden cross score...")
    
    ma50 = df.groupby("ts_code")["close"].transform(lambda x: x.rolling(50).mean())
    ma200 = df.groupby("ts_code")["close"].transform(lambda x: x.rolling(200).mean())

    cross = (ma50.shift(1) <= ma200.shift(1)) & (ma50 > ma200)
    # shift must also be grouped; otherwise it carries the previous stock's final day forward.
    cross = (
        df.groupby("ts_code").apply(
            lambda x: (x['close'].rolling(50).mean().shift(1) <= x['close'].rolling(200).mean().shift(1)) &
                      (x['close'].rolling(50).mean() > x['close'].rolling(200).mean())
        ).reset_index(level=0, drop=True)
    ) # Safer approach
    
    df['trend_score'] = cross.astype(int) * 4
    return df
