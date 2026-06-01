import pandas as pd
import numpy as np

def compute_squeeze_score(df):
    """
    Identifies volatility exhaustion by comparing current ATR 
    to its historical minimums.
    """
    x = df.copy()
    atr_col = 'atr'
    windows = [20, 60, 120]
    
    x['squeeze_score'] = 0
    
    for w in windows:
        rolling_min = (
            x.groupby('ts_code')[atr_col]
            .transform(lambda s: s.rolling(w, min_periods=w).min())
        )
        x['squeeze_score'] += (x[atr_col] <= rolling_min).astype(int)
        
    mask = x.groupby('ts_code')[atr_col].transform(lambda s: s.rolling(120).count()) < 120
    x.loc[mask, 'squeeze_score'] = np.nan
    
    # --- FIXED: Return the full dataframe ---
    return x