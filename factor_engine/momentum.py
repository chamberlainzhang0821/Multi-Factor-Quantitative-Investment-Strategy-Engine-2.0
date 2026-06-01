import numpy as np


def momentum_score(df):
  print("Calculating momentum score...")
  df["ma20"] = (
      df.groupby("ts_code")["close"]
        .transform(lambda x: x.rolling(20).mean())
  )
  df["ma50"] = (
      df.groupby("ts_code")["close"]
        .transform(lambda x: x.rolling(50).mean())
  )
  df["ma120"] = (
      df.groupby("ts_code")["close"]
        .transform(lambda x: x.rolling(120).mean())
  )

  conditions=[
    (df.ma20>df.ma50)&(df.ma50>df.ma120),
    (df.ma20>df.ma120)&(df.ma120>df.ma50),
    (df.ma50>df.ma20)&(df.ma20>df.ma120),
    (df.ma50>df.ma120)&(df.ma120>df.ma20),
    (df.ma120>df.ma20)&(df.ma20>df.ma50),
    (df.ma120>df.ma50)&(df.ma50>df.ma20)
  ]

    

  df['momentum_score']=np.select(
      conditions,
      [6,2,3,0,0,-6],
      default=0
  )

  return df
    
