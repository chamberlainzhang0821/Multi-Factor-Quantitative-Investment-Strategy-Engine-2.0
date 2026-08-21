# clean_prices.py
import pandas as pd


def clean_prices(df):
    if df is None:
        raise ValueError("Input dataframe is None")
    df = df.copy()

    # Dates
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values(['ts_code','trade_date'])

    # Deduplicate
    df = df.drop_duplicates(
        subset=['ts_code','trade_date']
    )

    # Data types
    numeric_cols = [
        'open','high','low','close',
        'vol','amount'
    ]

    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # OHLC sanity check
    # Invalid only if:
    # high below open/close, low above open/close, or high below low
    bad = (
        (df['high'] < df[['open','close']].max(axis=1))
        |
        (df['low'] > df[['open','close']].min(axis=1))
        |
        (df['high'] < df['low'])
    )

    df = df.loc[~bad]

    return df
