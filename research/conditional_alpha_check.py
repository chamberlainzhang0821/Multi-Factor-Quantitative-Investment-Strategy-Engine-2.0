import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

BASE_DIR=Path(__file__).resolve().parents[1]

FACTOR_FILE=(
    BASE_DIR/
    "data"/
    "factors"/
    "factor_scores.parquet"
)


def filter_signals(
    df,
    min_amount_quantile=0.30,
    exclude_gem=True,
    exclude_star=True,
):

    x=df.copy()

    cutoff=x["amount"].quantile(
        min_amount_quantile
    )

    x=x[
      x["amount"]>cutoff
    ]

    if exclude_gem:
        x=x[
          ~x.ts_code.str.startswith(
             ("300","301")
          )
        ]

    if exclude_star:
        x=x[
          ~x.ts_code.str.startswith(
             ("688","689")
          )
        ]

    return x


def build_zscore(df):

    factor_cols=[
        "main_force_score",
        "momentum_score",
        "trend_score",
        "breakout_score",
        "rs_score",
        "stability_score",
        "sector_score",
        "atr_score",
        "volume_score"
    ]

    df["total_score"]=0.0

    for f in factor_cols:

        mu=(
          df.groupby("trade_date")[f]
            .transform("mean")
        )

        sigma=(
          df.groupby("trade_date")[f]
            .transform("std")
            .replace(0,np.nan)
        )

        z=((df[f]-mu)/sigma).fillna(0)

        df["total_score"] += z

    return df


def positive_score_filter(df):

    return df[
      df.total_score > 0
    ].copy()


def add_forward_returns(df):

    for h in [5,10,20]:

        col=f"future_ret_{h}"

        df[col]=(
           df.groupby("ts_code")["close"]
             .shift(-h)
             .div(df["close"])-1
        )

        lo=(
          df.groupby("trade_date")[col]
            .transform(
              lambda x:x.quantile(0.01)
            )
        )

        hi=(
          df.groupby("trade_date")[col]
            .transform(
              lambda x:x.quantile(0.99)
            )
        )

        df[f"{col}_win"]=(
           df[col].clip(
              lower=lo,
              upper=hi
           )
        )

    return df


def monotonicity_check(df):

    print("\nSCORE>0 CONDITIONAL MONOTONICITY\n")

    # quintiles within top50 subset
    df["decile"]=(
      df.groupby("trade_date")["total_score"]
        .transform(
           lambda x: pd.qcut(
               x,
               5,
               labels=False,
               duplicates="drop"
           )+1
        )
    )

    print("\nDecile average total_score sanity check:\n")
    print(
      df.groupby("decile")["total_score"]
        .mean()
    )

    print("\nConditional total_score distribution:\n")
    print(
      df["total_score"].describe()
    )

    fig,axes=plt.subplots(
      3,1,
      figsize=(8,12)
    )

    for ax,h in zip(
        axes,
        [5,10,20]
    ):

        col=f"future_ret_{h}_win"

        daily=(
          df.groupby(
             ["trade_date","decile"]
          )[col]
          .mean()
          .reset_index()
        )

        mono=(
          daily.groupby("decile")[col]
            .mean()
        )

        print(
         f"{h}-Day Return by Quintile\n"
        )
        print(mono)

        spread=(
           mono.loc[5]-mono.loc[1]
        )

        print(
         f"Spread: {spread:.4%}\n"
        )

        ax.bar(
          mono.index,
          mono.values
        )

        ax.set_title(
         f"Score>0 Conditional {h}d Quintiles"
        )

    plt.tight_layout()

    plt.savefig(
      BASE_DIR/
      "research"/
      "results"/
      "conditional_positive_score_monotonicity.png"
    )

    plt.show()


def ic_check(df):

    print("\nSCORE>0 CONDITIONAL IC\n")

    for h in [5,10,20]:

        col=f"future_ret_{h}_win"

        daily_ic=[]

        for d,g in df.groupby(
            "trade_date"
        ):

            x=g["total_score"]
            y=g[col]

            valid=(
              x.notna()&y.notna()
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
         f"Rank IC ({h}d)"
        )

        print(
         f"Mean IC: {daily_ic.mean():.4f}"
        )

        print(
         f"ICIR: {(daily_ic.mean()/daily_ic.std()):.4f}"
        )

        print(
         f"Positive Ratio: {(daily_ic>0).mean():.2%}\n"
        )

    # -------------------------
    # conditional single-factor IC
    # -------------------------

    print("\nConditional Single-Factor Rank IC (20d)\n")

    factor_cols=[
        "main_force_score",
        "momentum_score",
        "trend_score",
        "breakout_score",
        "rs_score",
        "stability_score",
        "sector_score",
        "atr_score",
        "volume_score"
    ]

    for f in factor_cols:

        daily_ic=[]

        for d,g in df.groupby(
            "trade_date"
        ):

            x=g[f]
            y=g["future_ret_20_win"]

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

        if len(daily_ic)==0:
            continue

        daily_ic=np.array(
            daily_ic
        )

        print(
          f"{f}: {daily_ic.mean():.4f}"
        )


def main():

    print(
      "Loading factor panel..."
    )

    df=pd.read_parquet(
      FACTOR_FILE
    )

    df=filter_signals(df)

    df=build_zscore(df)

    # ---------
    # NEW robustness restriction
    # ---------

    df=positive_score_filter(df)

    print("\nPost-filter total_score sanity:\n")
    print(
      df["total_score"].describe()
    )

    print(
      f"Rows after score>0 filter: {len(df):,}"
    )

    df=add_forward_returns(df)

    monotonicity_check(df)

    ic_check(df)


if __name__=="__main__":
    main()