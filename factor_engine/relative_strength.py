# relative_strength.py


import numpy as np

def relative_strength(df):
    print("Calculating relative strength score...")

    df = df.sort_values(["ts_code", "trade_date"]).copy()

    # --------------------------
    # 1 stock 20-day return
    # --------------------------
    stock_ret = (
        df.groupby("ts_code")["close"]
        .pct_change(20)
    )

    # --------------------------
    # 2 map stocks to benchmark
    # --------------------------
    print("Mapping stocks to benchmarks...")
    code3 = df["ts_code"].str[:3]

    df["benchmark_code"] = np.select(
        [
            code3.isin(["300", "301"]),
            code3.isin(["688", "689"]),
            code3.isin(["000", "001", "002"]),
            code3.isin(["600", "601", "603"])
        ],
        [
            #"399006.SZ",
            #"000688.SH",
            "399001.SZ",
            "000001.SH"
        ],
        default="000001.SH"
    )

    # --------------------------
    # 3 build benchmark proxy ONCE
    # avoid four separate dataframe scans
    # --------------------------
    print("Calculating benchmark returns...")
    bench_close = (
        df.groupby([
            "benchmark_code",
            "trade_date"
        ])["close"]
        .mean()
        .sort_index()
    )

    bench_ret = (
        bench_close
        .groupby(level=0)
        .pct_change(20)
    )

    # --------------------------
    # 4 map returns back (no merge)
    # --------------------------
    print("Mapping benchmark returns back to stocks...")
    df["benchmark_ret"] = [
        bench_ret.get((b, d), np.nan)
        for b, d in zip(
            df["benchmark_code"],
            df["trade_date"]
        )
    ]

    rs = stock_ret - df["benchmark_ret"]

    # --------------------------
    # 5 scoring
    # --------------------------
    df["rs_score"] = 0
    df.loc[rs > 0.03, "rs_score"] = 1
    df.loc[rs > 0.05, "rs_score"] = 2
    df.loc[rs > 0.08, "rs_score"] = 3

    return df