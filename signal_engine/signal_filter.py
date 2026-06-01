# signal_filter.py
import pandas as pd


def filter_signals(
    df,
    min_amount_quantile=0.30,
    exclude_gem=True,
    exclude_star=True,
):
    """
    Basic production filters for daily stock signal ranking.

    Parameters
    ----------
    df : DataFrame
    min_amount_quantile : float
        Remove illiquid names below this turnover quantile.
    exclude_gem : bool
        Exclude ChiNext 300/301.
    exclude_star : bool
        Exclude STAR 688/689.
    """

    x = df.copy()

    # -------------------------
    # 1 Liquidity filter
    # -------------------------

    cutoff = x["amount"].quantile(
        min_amount_quantile
    )

    x = x[
        x["amount"] > cutoff
    ]


    # -------------------------
    # 2 Optional board filters
    # -------------------------

    if exclude_gem:
        x = x[
            ~x["ts_code"].str.startswith(
                ("300","301")
            )
        ]

    if exclude_star:
        x = x[
            ~x["ts_code"].str.startswith(
                ("688","689")
            )
        ]


    # -------------------------
    # 3 Optional sanity filter
    # (can tighten later)
    # -------------------------

    x = x[
        x["main_force_score"] > 0
    ]

    return x