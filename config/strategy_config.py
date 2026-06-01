# ==========================================
# Trend Following Strategy Config
# ==========================================

# for all the score: we remaint the option to use ML to optimize the weights,
#  but for now we set them based on intuition and backtesting results
# config/
#  strategy_config.py
#  factor_weights.py
#  data_fetch_config.py
#  backtest_config.py
#  paths.py
# ----------------------
# Universe
# ----------------------
UNIVERSE = "A_SHARE"

MIN_LISTING_DAYS = 240
EXCLUDE_ST = True

DURATION_DAYS = 1825  # 5 years of data for factor calculation and backtesting


# ----------------------
# Moving Averages
# ----------------------
MA_WINDOWS = {
    "short": 20,
    "medium": 50,
    "trend": 120,
    "golden_cross": 200,
    "long_term": 240
}


# ----------------------
# Factor Scores
# ----------------------

MOMENTUM_SCORE = {

    ("MA20","MA50","MA120"): 6,

    ("MA20","MA120","MA50"): 2, # reamin the option for ML

    ("MA50","MA20","MA120"): 3, # reamin the option for ML

    ("MA50","MA120","MA20"): 0,

    ("MA120","MA20","MA50"): 0,

    ("MA120","MA50","MA20"): -6
}


# ----------------------
# Golden Cross
# ----------------------
GOLDEN_CROSS = {

    "enable": True,

    "pairs": [
        (20,50),
        (50,120),
        (50,200)
    ],

    "score": 4
}


# ----------------------
# Breakout Factors
# ----------------------
BREAKOUT = {

    "20_day_high_score":1,

    "55_day_high_score":2
}


# ----------------------
# Relative Strength
# ----------------------
RELATIVE_STRENGTH = {

    "benchmark":[
        "000001.SH",
        "399001.SZ"
    ],

    "thresholds":[
        (0.03,1),
        (0.05,2),
        (0.08,3)
    ]
}


# ----------------------
# Volume Confirmation
# ----------------------
VOLUME_FILTER = {

    "lookback_days":3,

    "volume_multiplier":1.30,

    "volume_ma":20,

    "score":1
}


# ----------------------
# ATR
# ----------------------
ATR_CONFIG = {

    "period":14,

    "low_vol_threshold":0.5,

    "high_vol_threshold":3,

    "atr_expansion_score":1,

    "atr_golden_cross_bonus":1.5
}


# ----------------------
# Trend Stability
# ----------------------
LINEAR_REGRESSION = {

    "lookback":60,

    "use_slope":True,

    "use_r2":True,

    "weight_slope":0.5,

    "weight_r2":0.5
}


# ----------------------
# Sector Trend Filter
# ----------------------
SECTOR_FILTER = {

    "use_sw_level1":True,

    "use_sw_level2":True,

    "sector_ma_break_scores":{

        "ma5_above_ma10":1,

        "ma5_above_ma20":0.75,

        "ma5_above_ma30":0.5
    }
}


# ----------------------
# Main Force Trend
# ----------------------
MAIN_FORCE_CONFIRMATION = {

    "required":False
}


# ----------------------
# Risk Management
# ----------------------
RISK = {

    "trailing_stop":0.10,

    "market_stop_index":"000001.SH",

    "market_drop_filter":-0.01
}


# ----------------------
# Portfolio
# ----------------------
PORTFOLIO = {

    "top_n":20,

    "rebalance":"weekly"
}