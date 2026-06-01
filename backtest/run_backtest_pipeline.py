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
    # 1. Configuration Parameters (💡 核心中央控制台)
    # ---------------------------------------------------------
    # --- 资金与交易参数 ---
    INITIAL_CAPITAL = 100000
    HOLD_DAYS = 9999          # 既然你要“跟随趋势”，我们将 HOLD_DAYS 设为一个极大值
    TOP_N = 5                 # Max stocks to buy per day
    SCORE_THRESHOLD = 10.0     # Minimum alpha_score to trigger a buy
    SLIPPAGE = 0.00           # 滑点设置
    
    # --- 风控系统参数 (Risk Engine 专属) ---
    DAILY_STOP_LOSS_PCT = 0.06        # 🚀 新增：单日暴跌止损阈值 (6%)
    MAX_PORTFOLIO_DD = 0.15           # 账户整体最大回撤阈值 (15% 触发熔断)
    FREEZE_DAYS = 7                   # 熔断冷却天数
    ENABLE_TIME_EXIT = False          # 开关1：到期平仓 (关掉，专注趋势)
    ENABLE_STOP_LOSS = True           # 开关2：单票单日暴跌止损
    ENABLE_PORTFOLIO_FREEZE = False    # 开关3：大盘回撤账户熔断
    ENABLE_DELIST_LIQUIDATION = True  # 开关4：退市/停牌强平
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
    
    # 🚀 实例化时替换为新的参数
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
    
    buy_signals = [] # 用于 T+1 逻辑
    
    for current_date in dates:
        # A. 状态检查
        is_frozen = risk_engine.is_trading_frozen(current_date)
        current_total_capital = portfolio_engine.equity_curve[-1]['capital'] if portfolio_engine.equity_curve else INITIAL_CAPITAL
        
        # B. 仓位扫描与处理
        current_positions = portfolio_engine.positions.copy()
        
        # 💡 优化：删除了 df_today 的获取，因为不需要 ATR 了，回测速度会显著提升
        
        for pos in current_positions:
            code = pos['code']
            current_price = data_engine.get_price(current_date, code)

            # --- 💡 全部风控裁决交给 RiskEngine ---
            # 移除了 atr_val 传参
            exit_flag, reason, execute_price = risk_engine.check_stock_exit(
                current_price=current_price,
                position=pos,
                current_date=current_date,
                hold_days=HOLD_DAYS
            )
            
            # 只要风控引擎说要卖，就按它给的 execute_price 坚决执行
            if exit_flag:
                if reason == "forced_delist_liquidation":
                    print(f"💀 CRITICAL: {code} missing {risk_engine.delist_missing_days} days. Forced liquidation on {current_date.strftime('%Y-%m-%d')}")
                    
                portfolio_engine.execute_sell(pos, execute_price, current_date, reason)
                portfolio_engine.positions.remove(pos)

        # C. 【常规买入逻辑】(受熔断限制：is_frozen 时不进场)
        if not is_frozen and buy_signals:
            active_codes = [p['code'] for p in portfolio_engine.positions]
            target_value = current_total_capital * 0.20 # 复利：当前总资产的 20%
            
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
        # D. 每日必跑：收尾与信号生成
        # ---------------------------------------------------------
        # 1. 产生今日信号给明天用 (T+1)
        buy_signals = signal_engine.generate_daily_buy_list(current_date, data_engine.factors)

        # 2. 算账：记录今天的净值
        total_capital = portfolio_engine.update_daily_equity(current_date, data_engine)
        
        # 3. 检查今天是否触发新的熔断 (供明天参考)
        # 💡 修改：移除了外部传入的 peak_capital，引擎内部会自动管理
        risk_engine.check_portfolio_risk(
            current_capital=total_capital, 
            current_date=current_date
        )

    # ---------------------------------------------------------
    # 🚀 补丁：回测结束“虚拟平仓”，修复 Win Rate 统计
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