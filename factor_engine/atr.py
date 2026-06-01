import pandas as pd
import numpy as np
from config.factors_config import (
    ATR_LOOKBACK,
    ATR_VOL_WINDOW,
    ATR_EXPAND_WINDOW,
    ATR_LOW_VOL_THRESHOLD,
    ATR_MED_VOL_THRESHOLD,
    ATR_EXPANSION_MULTIPLIER,
)


def atr_factor(df,n=ATR_LOOKBACK):

    print("Calculating ATR score...")

    prev_close=(
      df.groupby("ts_code")["close"]
      .shift(1)
    )

    tr1=df.high-df.low
    tr2=(df.high-prev_close).abs()
    tr3=(df.low-prev_close).abs()


    tr=(
      pd.concat(
         [tr1,tr2,tr3],
         axis=1
      ).max(axis=1)
    )


    df["atr"]=(
      tr.groupby(df["ts_code"])
      .transform(
         lambda x:
         x.rolling(n).mean()
      )
    )


    df["atr_pct"]=df["atr"]/df["close"]


    df["atr_score"]=0.0


    low_vol=(
      df.groupby("ts_code")["atr_pct"]
      .transform(
         lambda x:
         x.rolling(ATR_VOL_WINDOW).mean()<ATR_LOW_VOL_THRESHOLD
      )
    )

    expand=(
      df["atr_pct"] >
      ATR_EXPANSION_MULTIPLIER*
      df.groupby("ts_code")["atr_pct"]
      .transform(
         lambda x:
         x.rolling(ATR_EXPAND_WINDOW).mean()
      )
    )

    medium_vol=(
      (df.groupby("ts_code")["atr_pct"]
       .transform(
          lambda x:
          x.rolling(ATR_VOL_WINDOW).mean()
       ) >=ATR_LOW_VOL_THRESHOLD)
      &
      (df.groupby("ts_code")["atr_pct"]
       .transform(
          lambda x:
          x.rolling(ATR_VOL_WINDOW).mean()
       ) <ATR_MED_VOL_THRESHOLD)
    )

    high_vol=(
      df.groupby("ts_code")["atr_pct"]
      .transform(
         lambda x:
         x.rolling(ATR_VOL_WINDOW).mean()
      ) >=ATR_MED_VOL_THRESHOLD
    )

    df.loc[
      low_vol,
      "atr_score"
    ]=0

    df.loc[
      medium_vol,
      "atr_score"
    ]=1

    df.loc[
      high_vol,
      "atr_score"
    ]=-1

    df.loc[
      medium_vol & expand,
      "atr_score"
    ]=1.5


    return df