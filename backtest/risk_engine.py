import pandas as pd

class RiskEngine:
    
    def __init__(
        self, 
        max_portfolio_dd=0.15, 
        freeze_days=7, 
        daily_stop_loss_pct=0.06,        # Daily-loss stop threshold (6%)
        enable_time_exit=False,          # Switch 1: time-based exit
        enable_stop_loss=True,           # Switch 2: single-day plunge stop
        enable_portfolio_freeze=True,    # Switch 3: portfolio drawdown freeze
        enable_delist_liquidation=True,  # Switch 4: forced delisting/suspension liquidation
        delist_missing_days=3,           # Tolerated number of missing days
        delist_penalty=0.8               # Forced-liquidation price discount (20%)
    ):
        self.max_portfolio_dd = max_portfolio_dd
        self.freeze_days = freeze_days
        self.pause_until = None
        self.internal_peak = None        # Maintain the capital peak internally to avoid deadlock
        self.daily_stop_loss_pct = daily_stop_loss_pct
        
        # Store switch states.
        self.enable_time_exit = enable_time_exit
        self.enable_stop_loss = enable_stop_loss
        self.enable_portfolio_freeze = enable_portfolio_freeze
        self.enable_delist_liquidation = enable_delist_liquidation
        self.delist_missing_days = delist_missing_days
        self.delist_penalty = delist_penalty

    def check_stock_exit(self, current_price, position, current_date, hold_days):
        """
        Determine whether to exit and return (exit_flag, reason, exit_price).
        External callers no longer need to pass atr_val.
        """
        # 0. Handle missing data, suspension, and delisting when current_price is NaN.
        if pd.isna(current_price):
            position['missing_days'] = position.get('missing_days', 0) + 1
            
            if self.enable_delist_liquidation and position['missing_days'] >= self.delist_missing_days:
                # Trigger discounted forced liquidation and calculate the penalty price.
                penalty_price = position['entry_price'] * self.delist_penalty
                return True, "forced_delist_liquidation", penalty_price
                
            return False, None, current_price

        # Reset the missing-day counter when the price is available.
        position['missing_days'] = 0

        # Store the prior closing price to calculate the single-day drop.
        if 'last_price' not in position:
            position['last_price'] = position['entry_price']
            
        # Calculate today's actual decline relative to yesterday or the entry price.
        daily_drop = 1 - (current_price / position['last_price'])
        
        # Store today's price for tomorrow's calculation regardless of whether it is sold.
        position['last_price'] = current_price

        # 1. Time-based exit (forced sale at expiry)
        if self.enable_time_exit:
            if (current_date - position['entry_date']).days >= hold_days:
                return True, "time_exit", current_price
            
        # 2. Single-day plunge stop (6% daily decline)
        if self.enable_stop_loss:
            # Stop out when today's price is down 6% (0.06) or more from yesterday.
            if daily_drop >= self.daily_stop_loss_pct:
                return True, "daily_stop_loss", current_price
            
        # All risk checks passed; do not sell.
        return False, None, current_price

    def check_portfolio_risk(self, current_capital, current_date, peak_capital=None):
        """
        Check whether the equity curve has suffered a severe drawdown.
        peak_capital is ignored if supplied; the engine uses the safer internal_peak instead.
        """
        if not self.enable_portfolio_freeze:
            return False
            
        # Update the internal peak net value.
        if self.internal_peak is None or current_capital > self.internal_peak:
            self.internal_peak = current_capital
            
        if self.internal_peak <= 0:
            return False
            
        # Calculate drawdown from the most recent valid peak.
        dd = 1 - (current_capital / self.internal_peak)
        
        if dd > self.max_portfolio_dd:
            self.pause_until = current_date + pd.Timedelta(days=self.freeze_days)
            
            # Reset the peak baseline to current capital after a freeze to avoid deadlock.
            # Trading can resume unless capital declines another 15% from this reset baseline.
            self.internal_peak = current_capital 
            
            return True # Trigger the portfolio freeze
            
        return False

    def is_trading_frozen(self, current_date):
        """
        Returns True if the system is currently under a risk freeze.
        """
        if not self.enable_portfolio_freeze:
            return False
            
        if self.pause_until and current_date < self.pause_until:
            return True
            
        return False
