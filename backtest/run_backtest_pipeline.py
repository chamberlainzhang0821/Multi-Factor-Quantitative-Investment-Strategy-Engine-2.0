import pandas as pd
import numpy as np
from pathlib import Path
import time

# Import paths from your config
from config.paths import CLEAN_DATA_DIR, FACTOR_DATA_DIR
from config.paths import ROOT_DIR
ROOT_DIR = Path(__file__).resolve().parents[1]

# Import the 5 backtest engines
from backtest.data_engine import DataEngine
from backtest.signal_engine import SignalEngine
from backtest.risk_engine import RiskEngine
from backtest.portfolio import PortfolioEngine
from backtest.evaluation import EvaluationEngine


def run_backtest():
    print("=" * 50)
    print("🚀 Starting Backtest Pipeline (T+1 & Compounding Enabled)")
    print("=" * 50)
    
    # ---------------------------------------------------------
    # 1. Configuration parameters (central control section)
    # ---------------------------------------------------------
    # Capital and trading parameters
    INITIAL_CAPITAL = 100000
    HOLD_DAYS = 9999          # Use a very large value to follow the trend
    TOP_N = 5                 # Max stocks to buy per day
    SCORE_THRESHOLD = 10.0     # Minimum alpha_score to trigger a buy
    SLIPPAGE = 0.00           # Slippage setting
    
    # Risk-engine parameters
    DAILY_STOP_LOSS_PCT = 0.06        # Single-day plunge stop threshold (6%)
    MAX_PORTFOLIO_DD = 0.15           # Portfolio drawdown threshold that triggers a freeze (15%)
    FREEZE_DAYS = 7                   # Freeze cooldown days
    ENABLE_TIME_EXIT = False          # Switch 1: exit at expiry (disabled for trend following)
    ENABLE_STOP_LOSS = True           # Switch 2: single-stock daily plunge stop
    ENABLE_PORTFOLIO_FREEZE = False    # Switch 3: portfolio drawdown freeze
    ENABLE_DELIST_LIQUIDATION = True  # Switch 4: forced delisting/suspension liquidation
    # ---------------------------------------------------------
    
    factor_file = FACTOR_DATA_DIR / "factor_scores.parquet"
    panel_file = CLEAN_DATA_DIR / "aligned_panel.parquet"
    
    # ---------------------------------------------------------
    # 2. Initialize Engines
    # ---------------------------------------------------------
    t0 = time.perf_counter()
    
    data_engine = DataEngine(factor_path=factor_file, panel_path=panel_file)
    signal_engine = SignalEngine(top_n=TOP_N, score_threshold=SCORE_THRESHOLD)
    portfolio_engine = PortfolioEngine(initial_capital=INITIAL_CAPITAL, slippage=SLIPPAGE)
    
    # Initialize with the new parameters.
    risk_engine = RiskEngine(
        daily_stop_loss_pct=DAILY_STOP_LOSS_PCT, 
        max_portfolio_dd=MAX_PORTFOLIO_DD, 
        freeze_days=FREEZE_DAYS,
        enable_time_exit=ENABLE_TIME_EXIT,         
        enable_stop_loss=ENABLE_STOP_LOSS,          
        enable_portfolio_freeze=ENABLE_PORTFOLIO_FREEZE,
        enable_delist_liquidation=ENABLE_DELIST_LIQUIDATION
    ) 
    
    dates = data_engine.trading_days
    print(f"Total trading days to simulate: {len(dates)}")
    print("-" * 50)

    # ---------------------------------------------------------
    # 3. The Daily Trading Loop
    # ---------------------------------------------------------
    
    buy_signals = [] # Used for T+1 execution logic
    
    for current_date in dates:
        # A. Check state.
        is_frozen = risk_engine.is_trading_frozen(current_date)
        current_total_capital = portfolio_engine.equity_curve[-1]['capital'] if portfolio_engine.equity_curve else INITIAL_CAPITAL
        
        # B. Scan and process positions.
        current_positions = portfolio_engine.positions.copy()
        
        # Optimization: df_today is no longer fetched because ATR is not needed.
        
        for pos in current_positions:
            code = pos['code']
            current_price = data_engine.get_price(current_date, code)

            # Delegate all risk decisions to RiskEngine.
            # The atr_val argument has been removed.
            exit_flag, reason, execute_price = risk_engine.check_stock_exit(
                current_price=current_price,
                position=pos,
                current_date=current_date,
                hold_days=HOLD_DAYS
            )
            
            # Execute the sale at the price returned by the risk engine.
            if exit_flag:
                if reason == "forced_delist_liquidation":
                    print(f"💀 CRITICAL: {code} missing {risk_engine.delist_missing_days} days. Forced liquidation on {current_date.strftime('%Y-%m-%d')}")
                    
                portfolio_engine.execute_sell(pos, execute_price, current_date, reason)
                portfolio_engine.positions.remove(pos)

        # C. Standard purchase logic (do not enter while frozen).
        if not is_frozen and buy_signals:
            active_codes = [p['code'] for p in portfolio_engine.positions]
            target_value = current_total_capital * 0.20 # Compound at 20% of current total assets
            
            for code in buy_signals:
                if code in active_codes:
                    continue
                    
                current_price = data_engine.get_price(current_date, code)
                if pd.isna(current_price):
                    continue
                
                success = portfolio_engine.execute_buy(
                    code=code, 
                    current_price=current_price, 
                    current_date=current_date, 
                    target_value=target_value
                )
                if success:
                    active_codes.append(code)

        # ---------------------------------------------------------
        # D. Daily finalization and signal generation.
        # ---------------------------------------------------------
        # 1. Generate today's signals for tomorrow (T+1).
        buy_signals = signal_engine.generate_daily_buy_list(current_date, data_engine.factors)

        # 2. Record today's net value.
        total_capital = portfolio_engine.update_daily_equity(current_date, data_engine)
        
        # 3. Check whether today triggers a new freeze for tomorrow.
        # peak_capital is now managed internally by the engine.
        risk_engine.check_portfolio_risk(
            current_capital=total_capital, 
            current_date=current_date
        )

    # ---------------------------------------------------------
    # Settle open positions at the end of the backtest to correct win-rate statistics.
    # ---------------------------------------------------------
    final_date = dates[-1]
    for pos in portfolio_engine.positions.copy():
        current_price = data_engine.get_price(final_date, pos['code'])
        if not pd.isna(current_price):
            portfolio_engine.execute_sell(pos, current_price, final_date, "end_of_backtest_liquidation")

    # ---------------------------------------------------------
    # 4. Final Evaluation
    # ---------------------------------------------------------
    from config.paths import RAW_DATA_DIR
    benchmark_path = RAW_DATA_DIR / "indices" / "000300.SH.parquet"

    eval_engine = EvaluationEngine(
        equity_curve=portfolio_engine.equity_curve,
        trades=portfolio_engine.trades,
        benchmark_file=benchmark_path
    )
    
    metrics = eval_engine.calculate_metrics()
    
    print("-" * 50)
    print("📊 Core Backtest Results (Trend Following Mode):")
    for k, v in metrics.items():
        print(f"   {k}: {v}")
        
    print("-" * 50)
    print("📅 Yearly Performance:")
    yearly_df = eval_engine.calculate_yearly_returns()
    if not yearly_df.empty:
        print(yearly_df.to_string())
    
    # ---------------------------------------------------------
    # 5. Plotting
    # ---------------------------------------------------------
    from backtest.plot import plot_backtest_results  
    plot_save_path = ROOT_DIR / "backtest" / "results" / "backtest_performance.png"
    
    plot_backtest_results(
        equity_df=portfolio_engine.equity_curve, 
        benchmark_file=benchmark_path,
        save_path=plot_save_path
    )

if __name__ == "__main__":
    run_backtest()
