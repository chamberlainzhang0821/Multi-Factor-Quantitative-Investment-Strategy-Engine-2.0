# monotonicity_check.py
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]

# Use a unified path to read the original full factor file.
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
    x = df.copy()

    cutoff = x.groupby("trade_date")["amount"].transform(
        lambda s: s.quantile(min_amount_quantile)
    )

    x = x[x["amount"] > cutoff]

    if exclude_gem:
        x = x[~x["ts_code"].str.startswith(("300","301"))]

    if exclude_star:
        x = x[~x["ts_code"].str.startswith(("688","689"))]

    # main force confirmation filter
    if "main_force_score" in x.columns:
        x = x[x["main_force_score"] > 0]

    return x


def monotonicity_check():

    print("Loading factor panel...")
    df = pd.read_parquet(FACTOR_FILE)

    # ---------------------------------------------------------
    # Step 1: strictly sort by code and date to prevent shift misalignment.
    # ---------------------------------------------------------
    print("Sorting data by ts_code and trade_date...")
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)

    # ---------------------------------------------------------
    # Step 2: calculate complete forward returns before filtering.
    # ---------------------------------------------------------
    print("Calculating forward returns...")
    for horizon in [10, 15, 60, 120]:
        df[f"future_ret_{horizon}"] = (
          df.groupby("ts_code")["close"]
          .shift(-horizon)
          .div(df["close"]) - 1
        )

    # ---------------------------------------------------------
    # Step 3: calculate cross-sectional Z-scores on the full set.
    # ---------------------------------------------------------
    print("Calculating Z-scores...")
    factor_cols = [
        #"main_force_score",
        "momentum_score",
        "trend_score",
        #"breakout_score",
        "sector_score",
        "atr_score",
        "squeeze_score",
        "ignition_score",
        "stability_score",
        "volume_score"
    ]

    df["total_score"] = 0.0

    for f in factor_cols:
        if f not in df.columns:
            continue
            
        cs_mean = df.groupby("trade_date")[f].transform("mean")
        cs_std = df.groupby("trade_date")[f].transform("std").replace(0, np.nan)
        z = ((df[f] - cs_mean) / cs_std).fillna(0.0)
        df["total_score"] += z

    # ---------------------------------------------------------
    # Step 4: filter safely after forward returns and Z-scores are aligned.
    # ---------------------------------------------------------
    print("Filtering signals...")
    df = filter_signals(df)

    # Remove NaN rows used in calculation, including missing forward returns or composite scores.
    df = df.dropna(
       subset=[
         "future_ret_10",
         "future_ret_15",
         "future_ret_60",
         "future_ret_120",
         "total_score"
       ]
    )

    # --------------------------
    # Daily quintiles (groups 1-5)
    # --------------------------
    print("Assigning quintiles...")
    def make_deciles(x):
        try:
            return pd.qcut(
               x.rank(method="first"),
               5,
               labels=False
            ) + 1
        except:
            return np.nan

    df["decile"] = (
      df.groupby("trade_date")["total_score"]
      .transform(make_deciles)
    )

    df = df.dropna(subset=["decile"])

    # --------------------------
    # average future returns
    # --------------------------
    print("Evaluating monotonicity...")
    for horizon in [10, 15, 60, 120]:

        col = f"future_ret_{horizon}"

        daily_decile_ret = (
          df.groupby(["trade_date", "decile"])[col]
          .mean()
          .reset_index()
        )

        monotone = (
          daily_decile_ret
          .groupby("decile")[col]
          .mean()
        )

        print(f"\n{horizon}-Day Future Return by Quintile:\n")
        print(monotone)

        spread = monotone.loc[5] - monotone.loc[1]
        print(f"Top-Bottom Spread ({horizon}d): {spread:.4%}")

    # --------------------------
    # extreme tail check inside top quintile
    # --------------------------
    q5 = df[df["decile"] == 5].copy()

    # Calculate the Top 10% threshold daily for greater accuracy than a global threshold.
    threshold = q5.groupby("trade_date")["total_score"].transform(lambda x: x.quantile(0.90))
    q5["extreme"] = (q5["total_score"] >= threshold)

    extreme_test = q5.groupby("extreme")["future_ret_120"].mean()

    print("\n120-Day Return Inside Top Quintile (Extreme Tail Check):\n")
    print(extreme_test)

    # --------------------------
    # quintile comparison plots
    # --------------------------
    print("\nGenerating plots...")
    fig, axes = plt.subplots(4, 1, figsize=(8, 16))

    for ax, horizon in zip(axes, [10, 15, 60, 120]):
        col = f"future_ret_{horizon}"
        
        daily_decile_ret = df.groupby(["trade_date", "decile"])[col].mean().reset_index()
        monotone = daily_decile_ret.groupby("decile")[col].mean()

        # Set colors: green or red for the highest score and gray for the lowest.
        colors = ['#d3d3d3', '#a9a9a9', '#808080', '#69b3a2', '#40e0d0']
        
        ax.bar(monotone.index, monotone.values, color=colors[:len(monotone)])
        ax.set_title(f"{horizon}-Day Forward Return by Quintile")
        ax.set_xlabel("Quintile (1 = Worst, 5 = Best)")
        ax.set_ylabel("Average Return")
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    
    # Ensure the directory exists.
    output_dir = BASE_DIR / "research" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    save_path = output_dir / "monotonicity_quintiles.png"
    plt.savefig(save_path)
    print(f"Plot saved to {save_path}")

    plt.show()

if __name__ == "__main__":
    monotonicity_check()
