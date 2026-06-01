# volume_filter.py
def volume_confirmation(df):
    print("Calculating volume confirmation score...")
    avg20=(
      df.groupby("ts_code")["vol"]
      .transform(
        lambda x:x.rolling(20).mean()
      )
    )

    is_high_vol = (df.vol > 1.3 * avg20).astype(int)
    confirm = (
        is_high_vol.groupby(df["ts_code"])
        .transform(lambda x: x.rolling(3).sum()) == 3
    )

    df['volume_score']=confirm.astype(int)

    return df