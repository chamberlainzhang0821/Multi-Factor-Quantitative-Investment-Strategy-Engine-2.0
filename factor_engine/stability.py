# stability.py
import numpy as np
from scipy.stats import linregress

def trend_stability(df):
    print("Calculating trend stability score...")

    df = df.sort_values([
        "ts_code",
        "trade_date"
    ]).copy()

    w = 7

    # fixed regressor 0..w-1
    x = np.arange(w)
    x_mean = x.mean()
    var_x = ((x - x_mean)**2).mean()

    logp = np.log(
        df["close"].clip(lower=1e-8)
    )

    g = df.groupby("ts_code")

    y_mean = (
        g["close"]
        .transform(
            lambda s: np.log(
                s.clip(lower=1e-8)
            ).rolling(w).mean()
        )
    )

    xy_mean = (
        g["close"]
        .transform(
            lambda s:
            np.log(s.clip(lower=1e-8))
            .rolling(w)
            .apply(
                lambda y:
                (y * x).mean(),
                raw=True
            )
        )
    )

    cov_xy = xy_mean - x_mean * y_mean

    slope = cov_xy / var_x

    y_std = (
        g["close"]
        .transform(
            lambda s:
            np.log(s.clip(lower=1e-8))
            .rolling(w)
            .std()
        )
    )

    corr = cov_xy / (
        np.sqrt(var_x) * y_std
    )

    r2 = corr.pow(2).clip(
        lower=0,
        upper=1
    )

    df["stability_raw"] = slope * r2

    pct = (
        df.groupby("trade_date")["stability_raw"]
        .rank(pct=True)
    )

    df["stability_score"] = 0
    df.loc[pct > 0.50, "stability_score"] = 1
    df.loc[pct > 0.70, "stability_score"] = 2
    df.loc[pct > 0.90, "stability_score"] = 3

    return df