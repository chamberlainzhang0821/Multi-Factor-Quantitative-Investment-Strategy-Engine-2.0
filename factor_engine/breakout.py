def breakout_factor(df):
    print("Calculating breakout score...")

    # Safety check: ensure rows are strictly chronological.
    df = df.sort_values(["ts_code", "date"]).reset_index(drop=True)

    high20 = df.groupby("ts_code")["close"].transform(
        lambda x: x.rolling(20).max().shift(1)
    )
    high55 = df.groupby("ts_code")["close"].transform(
        lambda x: x.rolling(55).max().shift(1)
    )

    df["breakout_score"] = 0

    # Apply vectorized score additions.
    df.loc[df["close"] > high20, "breakout_score"] += 1
    df.loc[df["close"] > high55, "breakout_score"] += 2

    return df
