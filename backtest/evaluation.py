import pandas as pd
import numpy as np
from pathlib import Path

class EvaluationEngine:
    def __init__(self, equity_curve, trades, benchmark_file=None):
        """
        Initializes the performance evaluator and loads the benchmark.
        """
        self.equity = pd.DataFrame(equity_curve)
        self.trades = pd.DataFrame(trades)
        self.market_returns = None
        
        if not self.equity.empty:
            # Core fix: set date as the index so Alpha can align with the benchmark.
            self.equity['date'] = pd.to_datetime(self.equity['date'])
            self.equity = self.equity.set_index('date')
            self.equity['return'] = self.equity['capital'].pct_change().fillna(0)

        # Load and process the benchmark.
        if benchmark_file is not None:
            bench_path = Path(benchmark_file)
            if bench_path.exists():
                hs300 = pd.read_parquet(bench_path)
                hs300['trade_date'] = pd.to_datetime(hs300['trade_date'])
                hs300 = hs300.set_index('trade_date').sort_index()
                self.market_returns = hs300['close'].pct_change().fillna(0)
            else:
                print(f"⚠️ Benchmark file not found at {bench_path}. Alpha will be 0.")
                
    def calculate_metrics(self):
        if self.equity.empty:
            return {}

        total_return = (self.equity['capital'].iloc[-1] / self.equity['capital'].iloc[0]) - 1
        
        self.equity['cum_max'] = self.equity['capital'].cummax()
        self.equity['drawdown'] = (self.equity['capital'] / self.equity['cum_max']) - 1
        max_drawdown = self.equity['drawdown'].min()
        
        daily_ret = self.equity['return']
        sharpe = (daily_ret.mean() / daily_ret.std()) * np.sqrt(252) if daily_ret.std() != 0 else 0
        
        win_rate = 0
        pnl_ratio = 0
        avg_hold_days = 0
        annual_turnover = 0
        
        # Include all trade records, including end-of-backtest forced settlement.
        if not self.trades.empty:
            # Ensure the pnl column exists.
            if 'pnl' in self.trades.columns:
                profits = self.trades[self.trades['pnl'] > 0]['pnl']
                losses = self.trades[self.trades['pnl'] < 0]['pnl']
                
                win_rate = len(profits) / len(self.trades) if len(self.trades) > 0 else 0
                
                avg_profit = profits.mean() if not profits.empty else 0
                avg_loss = abs(losses.mean()) if not losses.empty else 0
                pnl_ratio = avg_profit / avg_loss if avg_loss != 0 else 0

            years = len(self.equity) / 252
            
            if 'entry_date' in self.trades.columns and 'exit_date' in self.trades.columns:
                hold_days = (pd.to_datetime(self.trades['exit_date']) - pd.to_datetime(self.trades['entry_date'])).dt.days
                avg_hold_days = hold_days.mean()

            if 'entry_price' in self.trades.columns and 'shares' in self.trades.columns and years > 0:
                self.trades['trade_value'] = self.trades['entry_price'] * self.trades['shares']
                total_traded_capital = self.trades['trade_value'].sum()
                avg_portfolio_value = self.equity['capital'].mean()
                annual_turnover = total_traded_capital / avg_portfolio_value / years

        # Keep the Alpha calculation logic unchanged.
        alpha = 0.0
        if self.market_returns is not None and daily_ret.std() != 0:
            aligned = pd.concat([daily_ret.rename('strat'), self.market_returns.rename('mkt')], axis=1).dropna()
            if not aligned.empty and aligned['mkt'].std() != 0:
                beta = np.cov(aligned['strat'], aligned['mkt'])[0][1] / np.var(aligned['mkt'])
                alpha = (aligned['strat'].mean() - beta * aligned['mkt'].mean()) * 252

        return {
            "Total Return": f"{total_return * 100:.2f}%",
            "Max Drawdown": f"{max_drawdown * 100:.2f}%",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Win Rate": f"{win_rate * 100:.2f}%",
            "PnL Ratio": f"{pnl_ratio:.2f}",
            "Annual Alpha": f"{alpha * 100:.2f}%",
            "Avg Hold Days": f"{avg_hold_days:.1f}" if avg_hold_days > 0 else "N/A",
            "Annual Turnover": f"{annual_turnover:.2f}x" if annual_turnover > 0 else "N/A"
        }
    
    def calculate_yearly_returns(self):
        """
        Group equity by year and calculate each year's return and maximum drawdown.
        Return a Pandas DataFrame for convenient printing.
        """
        if self.equity.empty:
            return pd.DataFrame()
            
        yearly_records = []
        
        # Group by calendar year.
        for year, group in self.equity.groupby(self.equity.index.year):
            if not group.empty:
                start_capital = group['capital'].iloc[0]
                end_capital = group['capital'].iloc[-1]
                yearly_ret = (end_capital / start_capital) - 1
                
                # Calculate the year's maximum drawdown.
                cum_max = group['capital'].cummax()
                drawdown = (group['capital'] / cum_max) - 1
                max_dd = drawdown.min()
                
                yearly_records.append({
                    "Year": year,
                    "Return": f"{yearly_ret * 100:.2f}%",
                    "Max Drawdown": f"{max_dd * 100:.2f}%"
                })
                
        yearly_df = pd.DataFrame(yearly_records).set_index("Year")
        return yearly_df
