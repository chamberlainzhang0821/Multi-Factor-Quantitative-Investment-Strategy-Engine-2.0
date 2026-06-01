# main_trend.py
from config.factors_config import MAIN_FORCE_FLOW_THRESHOLD

def trend_confirmation(df):
    print("Calculating main force accumulation score...")

    mf_ratio = (
        df['net_mf_amount'] /
        df['amount'].replace(0, float('nan'))
    )

    pos_flow = (
        (mf_ratio > MAIN_FORCE_FLOW_THRESHOLD)
        .astype(int)
    )

    flow_days = (
        pos_flow
        .groupby(df['ts_code'])
        .transform(
            lambda x: x.rolling(3).sum()
        )
    )

    df['main_force_confirm'] = (
        flow_days > 0
    ).astype(int)

    df['main_force_score'] = -1.0

    df.loc[
        flow_days.isin([1,2]),
        'main_force_score'
    ] = 1.0

    df.loc[
        flow_days == 3,
        'main_force_score'
    ] = 3.0

    return df
