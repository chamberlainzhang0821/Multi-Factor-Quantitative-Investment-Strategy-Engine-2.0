import pandas as pd
import numpy as np

class PortfolioEngine:
    def __init__(self, initial_capital, slippage=0.001):
        """
        Initializes the accounting system.
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.peak_capital = initial_capital
        self.slippage = slippage

    def _calculate_fees(self, transaction_value, is_sell=False):
        """
        Calculates A-share specific transaction costs.
        Includes 5 RMB minimum commission and one-way stamp tax.
        """
        commission = max(transaction_value * 0.0002354, 5.0)
        stamp_tax = transaction_value * 0.0005 if is_sell else 0.0
        return commission + stamp_tax

    def execute_sell(self, position, current_price, current_date, reason):
        """
        Processes a sell order, deducts fees, and updates cash.
        """
        # Apply slippage to the exit price (selling lower)
        actual_price = current_price * (1 - self.slippage)
        proceeds = actual_price * position['shares']
        fees = self._calculate_fees(proceeds, is_sell=True)
        
        net_proceeds = proceeds - fees
        pnl = net_proceeds - (position['entry_price'] * position['shares'])
        
        self.cash += net_proceeds
        
        self.trades.append({
            'code': position['code'],
            'entry_date': position['entry_date'],
            'exit_date': current_date,
            'entry_price': position['entry_price'],
            'exit_price': actual_price,
            'shares': position['shares'],
            'pnl': pnl,
            'reason': reason
        })

    def execute_buy(self, code, current_price, current_date, target_value):
        """
        Processes a buy order. Uses dynamic sizing.
        """
        # Apply slippage to the entry price (buying higher)
        actual_price = current_price * (1 + self.slippage)
        
        shares = int(target_value // actual_price)
        # Round down to nearest board lot (100 shares) for A-shares
        shares = (shares // 100) * 100 
        
        if shares == 0:
            return False
            
        cost = actual_price * shares
        fees = self._calculate_fees(cost, is_sell=False)
        total_cost = cost + fees
        
        if self.cash >= total_cost:
            self.cash -= total_cost
            self.positions.append({
                'code': code,
                'entry_price': actual_price,
                'shares': shares,
                'entry_date': current_date
            })
            return True
        return False

    def update_daily_equity(self, current_date, data_engine):
        """
        Marks the portfolio to market at the end of the day.
        """
        portfolio_value = 0
        for pos in self.positions:
            price = data_engine.get_price(current_date, pos['code'])
            if not pd.isna(price):
                portfolio_value += price * pos['shares']
                
        total_capital = self.cash + portfolio_value
        self.peak_capital = max(self.peak_capital, total_capital)
        
        self.equity_curve.append({
            'date': current_date,
            'capital': total_capital,
            'cash': self.cash
        })
        
        return total_capital