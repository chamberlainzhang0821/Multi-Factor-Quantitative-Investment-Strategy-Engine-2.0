import pandas as pd


def handle_missing(df):
    """Handle missing values in the corrected full-panel dataset.

    Important: this function uses time-series filling (ffill / bfill).
    Run it only on the global panel after all stock, sector, and external data are merged.
    Do not call it in a single-day cross-sectional loop, where a fill length of one would make it ineffective.
    """
    if df is None or df.empty:
        return df

    df = df.copy()

    # ----------------------------------------------------
    # Core fix 1: enforce strict global sorting.
    # Each ts_code must be tightly ordered by time for ffill/bfill to work correctly.
    # ----------------------------------------------------
    df = df.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)

    # ----------------------------------------------------
    # 1. Time-series filling for individual-stock closing prices.
    # ----------------------------------------------------
    # Fill at most three consecutive days to avoid noise from long-suspended stocks.
    if "close" in df.columns:
        df["close"] = df.groupby("ts_code")["close"].ffill(limit=3)

    # ----------------------------------------------------
    # 2. Drop invalid trading days with missing volume.
    # ----------------------------------------------------
    # An A-share row without volume is not useful for multi-factor calculations and is removed.
    if "vol" in df.columns:
        df = df.dropna(subset=["vol"])

    # ----------------------------------------------------
    # 3. Set missing money-flow values to zero.
    # ----------------------------------------------------
    # Missing main-force, large-order, and extra-large-order data indicates zero volume at that tier.
    mf_cols = [
        c
        for c in df.columns
        if "buy_" in c or "sell_" in c or "net_mf" in c
    ]
    if mf_cols:
        df[mf_cols] = df[mf_cols].fillna(0)

    # ----------------------------------------------------
    # 4. Time-series filling for Shenwan sector labels.
    # ----------------------------------------------------
    # Handle missing assignments and historical gaps caused by dynamic Shenwan sector changes.
    if "sw_l1" in df.columns:
        df["sw_l1"] = df.groupby("ts_code")["sw_l1"].ffill().bfill()

    if "sw_l2" in df.columns:
        df["sw_l2"] = df.groupby("ts_code")["sw_l2"].ffill().bfill()

    # ----------------------------------------------------
    # 5. Time-series filling for sector-index prices.
    # Core fix 2: never use groupby('sw_l1') here.
    # In a flat global panel, it could forward-fill the final row of one stock into another stock's first row.
    # Instead, group by ts_code and follow each stock's own history when filling sector-index prices.
    # ----------------------------------------------------
    if "sw_l1_close" in df.columns:
        df["sw_l1_close"] = (
            df.groupby("ts_code")["sw_l1_close"].ffill().bfill()
        )

    if "sw_l2_close" in df.columns:
        df["sw_l2_close"] = (
            df.groupby("ts_code")["sw_l2_close"].ffill().bfill()
        )

    return df
