import numpy as np

def compute_ignition_score(df):
    """
    Categorizes the direction of a breakout combined with 
    ATR expansion/contraction.
    """
    x = df.copy()
    atr_col = 'atr'
    
    # 1. Define 3-day Price Breakout
    # Use shift(1) to avoid look-ahead bias
    x['hi_3'] = x.groupby('ts_code')['high'].transform(lambda s: s.shift(1).rolling(3).max())
    x['lo_3'] = x.groupby('ts_code')['low'].transform(lambda s: s.shift(1).rolling(3).min())
    
    # 2. Determine ATR Direction
    x['atr_diff'] = x.groupby('ts_code')[atr_col].diff()
    
    # 3. Ignition Logic Matrix
    price_up = x['close'] > x['hi_3']
    price_down = x['close'] < x['lo_3']
    atr_up = x['atr_diff'] > 0
    atr_down = x['atr_diff'] <= 0
    
    conditions = [
        (price_up & atr_up),
        (price_up & atr_down),
        (price_down & atr_down),
        (price_down & atr_up)
    ]
    choices = [4, 1, -2, -4]
    
    x['ignition_score'] = np.select(conditions, choices, default=0)
    
    # Ensure NaN for the first row of diff
    x.loc[x['atr_diff'].isna(), 'ignition_score'] = np.nan
    
    # --- FIXED: Return the full dataframe to keep columns for the next step ---
    return x 