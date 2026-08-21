import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr


BASE_DIR = Path(__file__).resolve().parents[1]

# Read the original full factor file.
FACTOR_FILE = (
    BASE_DIR /
    "data" /
    "factors" /
    "all_factors.parquet"
)


def filter_signals(
    df,
    min_amount_quantile=0.30,
    exclude_gem=True,
    exclude_star=True,
):

    x=df.copy()

    cutoff = x["amount"].quantile(
        min_amount_quantile
    )

    x=x[
      x["amount"]>cutoff
    ]

    if exclude_gem:
        x=x[
          ~x["ts_code"].str.startswith(
            ("300","301")
          )
        ]

    if exclude_star:
        x=x[
          ~x["ts_code"].str.startswith(
            ("688","689")
          )
        ]

    # main force confirmation filter
    if "main_force_score" in x.columns:
        x = x[x["main_force_score"] > 0]

    return x


def ic_analysis():

    print(
      "Loading factor panel..."
    )

    df=pd.read_parquet(
      FACTOR_FILE
    )

    # ---------------------------------------------------------
    # Step 1: strictly sort by code and date to prevent shift misalignment.
    # ---------------------------------------------------------
    print("Sorting data by ts_code and trade_date...")
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)

    # ---------------------------------------------------------
    # Step 2: calculate complete forward returns before filtering.
    # ---------------------------------------------------------
    print("Calculating forward returns...")
    for h in [10,15,60,120]:

        df[f"future_{h}"]=(
           df.groupby("ts_code")["close"]
           .shift(-h)
           .div(df["close"])-1
        )

    # winsorized forward returns (1% / 99%)
    for h in [10,15,60,120]:

        col = f"future_{h}"
        wcol = f"future_{h}_win"

        lo = (
            df.groupby("trade_date")[col]
            .transform(
                lambda x: x.quantile(0.01)
            )
        )

        hi = (
            df.groupby("trade_date")[col]
            .transform(
                lambda x: x.quantile(0.99)
            )
        )

        df[wcol] = df[col].clip(
            lower=lo,
            upper=hi
        )

    # ---------------------------------------------------------
    # Step 3: calculate cross-sectional Z-scores on the full set for statistical validity.
    # ---------------------------------------------------------
    print("Calculating Z-scores...")
    factor_cols = [
        #"main_force_score",
        "momentum_score",
        "trend_score",
        #"breakout_score",
        "sector_score",
        "squeeze_score",
        "ignition_score",
        "atr_score",
        #"rs_score",
        "stability_score",
        "volume_score"
    ]

    df["total_score"]=0.0

    for f in factor_cols:
        
        # Skip gracefully when a factor is unavailable.
        if f not in df.columns:
            continue

        mu=(
          df.groupby("trade_date")[f]
          .transform("mean")
        )

        sigma=(
          df.groupby("trade_date")[f]
          .transform("std")
          .replace(0,np.nan)
        )

        z=(
         (df[f]-mu)/sigma
        ).fillna(0)

        df["total_score"] += z

    # ---------------------------------------------------------
    # Step 4: filter safely after forward returns and Z-scores are aligned.
    # ---------------------------------------------------------
    print("Filtering signals...")
    df=filter_signals(df)


    # -------------------
    # Rank IC (composite score)
    # -------------------
    for h in [10,15,60,120]:

        col=f"future_{h}_win"

        daily_ic=[]

        for d,g in df.groupby(
            "trade_date"
        ):

            x=g["total_score"]
            y=g[col]

            valid=(
               x.notna()
               &
               y.notna()
            )

            if valid.sum()<30:
                continue

            ic,_=spearmanr(
               x[valid],
               y[valid]
            )

            if np.isfinite(ic):
                daily_ic.append(ic)


        daily_ic=np.array(
            daily_ic
        )

        print(
          f"\nRank IC ({h}d)"
        )

        print(
         f"Mean IC: {daily_ic.mean():.4f}"
        )

        print(
         f"IC Std : {daily_ic.std():.4f}"
        )

        print(
         f"ICIR   : {daily_ic.mean()/daily_ic.std():.4f}"
        )

        print(
         f"Positive IC Ratio: {(daily_ic>0).mean():.2%}"
        )

    # -------------------
    # single factor IC decomposition
    # -------------------

    print("\nSingle-Factor Rank IC (120d)\n")

    for f in factor_cols:
        
        if f not in df.columns:
            continue

        daily_ic=[]

        for d,g in df.groupby("trade_date"):

            x=g[f]
            y=g["future_120_win"]

            valid=(
                x.notna()
                &
                y.notna()
            )

            if valid.sum()<30:
                continue

            ic,_=spearmanr(
                x[valid],
                y[valid]
            )

            if np.isfinite(ic):
                daily_ic.append(ic)

        daily_ic=np.array(daily_ic)

        if len(daily_ic)==0:
            continue

        print(
            f"{f}: {daily_ic.mean():.4f}"
        )

    # -------------------
    # leave-one-out test
    # -------------------

    for horizon in [10,15,60,120]:

        print(
            f"\nLeave-One-Out IC ({horizon}d)\n"
        )

        ret_col=f"future_{horizon}_win"

        baseline_ic=None

        for drop_factor in [None] + factor_cols:
            
            if drop_factor and drop_factor not in df.columns:
                continue

            use_factors=[
                f for f in factor_cols
                if f != drop_factor and f in df.columns
            ]

            score=pd.Series(
                0.0,
                index=df.index
            )

            for f in use_factors:

                mu=(
                 df.groupby("trade_date")[f]
                 .transform("mean")
                )

                sigma=(
                 df.groupby("trade_date")[f]
                 .transform("std")
                 .replace(0,np.nan)
                )

                z=(
                 (df[f]-mu)/sigma
                ).fillna(0)

                score += z

            daily_ic=[]

            for d,g in df.groupby(
                "trade_date"
            ):

                x=score.loc[g.index]
                y=g[ret_col]

                valid=(
                   x.notna()
                   &
                   y.notna()
                )

                if valid.sum()<30:
                    continue

                ic,_=spearmanr(
                    x[valid],
                    y[valid]
                )

                if np.isfinite(ic):
                    daily_ic.append(ic)

            mean_ic=np.mean(
                daily_ic
            )

            if drop_factor is None:

                baseline_ic=mean_ic

                print(
                 f"Baseline: {mean_ic:.4f}"
                )

            else:

                delta=(
                 mean_ic-baseline_ic
                )

                print(
                 f"Drop {drop_factor}: "
                 f"{mean_ic:.4f} "
                 f"(Δ {delta:+.4f})"
                )


if __name__=="__main__":
    ic_analysis()
