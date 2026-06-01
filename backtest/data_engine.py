import pandas as pd
import numpy as np
from pathlib import Path

class DataEngine:
    def __init__(self, factor_path: Path, panel_path: Path):
        """
        Initializes the data engine by loading pre-cleaned, split-adjusted 
        data and factor scores directly from parquet files.
        """
        print("Loading factor scores and price panel...")
        self.factors = pd.read_parquet(factor_path)
        panel = pd.read_parquet(panel_path)
        
        # Standardize date columns to avoid time-matching issues
        self.factors['date'] = pd.to_datetime(self.factors['trade_date']).dt.normalize()
        panel['trade_date'] = pd.to_datetime(panel['trade_date']).dt.normalize()
        
        # ---------------------------------------------------------
        # Critical Optimization: Price Matrix Pivot
        # ---------------------------------------------------------
        # We pivot the long-format panel into a wide matrix 
        # (Index = Dates, Columns = Codes, Values = Close Prices).
        # This makes daily price lookups O(1) instead of filtering rows,
        # speeding up the backtest loop significantly.
        print("Building wide price matrix for fast O(1) lookups...")
        self.prices = panel.pivot(index='trade_date', columns='ts_code', values='close')
        
        # We can also pre-calculate the market return once to save time
        print("Pre-calculating daily market returns...")
        self.market_returns = self.prices.pct_change(fill_method=None).mean(axis=1)
        
        # Get a sorted list of all valid trading days in the dataset
        self.trading_days = sorted(self.prices.index.tolist())

    def get_price(self, date, code):
        """
        Retrieves the split-adjusted closing price for a specific date and stock.
        """
        try:
            price = self.prices.loc[date, code]
            return price if pd.notna(price) else np.nan
        except KeyError:
            return np.nan
            
    def get_market_return(self, date):
        """
        Retrieves the pre-calculated market return for a specific date.
        """
        try:
            return self.market_returns.loc[date]
        except KeyError:
            return 0.0
            
    def get_daily_factors(self, date):
        """
        Returns the cross-section of factor scores for a specific date.
        """
        return self.factors[self.factors['date'] == date]