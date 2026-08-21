import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

def plot_backtest_results(equity_df, benchmark_file=None, save_path=None):
    """
    Plot three standard strategy-backtest analyses:
    1. Cumulative returns compared with the benchmark.
    2. Dynamic strategy drawdown.
    3. Rolling annualized-volatility comparison.
    """
    print("🎨 Generating backtest performance plots...")
    
    # --------------------------
    # 1. Process strategy equity data.
    # --------------------------
    # Core fix: convert either a list or a DataFrame to a DataFrame.
    df = pd.DataFrame(equity_df)
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
    
    strat_capital = df['capital']
    strat_ret = strat_capital.pct_change().fillna(0)
    
    # Normalize net value to a 1.0 starting point.
    strat_cum = strat_capital / strat_capital.iloc[0]
    
    # Calculate dynamic drawdown.
    cum_max = strat_capital.cummax()
    drawdown = (strat_capital / cum_max) - 1.0

    # --------------------------
    # 2. Process CSI 300 benchmark data.
    # --------------------------
    bench_cum = None
    bench_ret = None
    if benchmark_file:
        b_path = Path(benchmark_file)
        if b_path.exists():
            hs300 = pd.read_parquet(b_path)
            hs300['trade_date'] = pd.to_datetime(hs300['trade_date'])
            hs300 = hs300.set_index('trade_date').sort_index()
            
            # Align dates and forward-fill missing values.
            hs300 = hs300.reindex(df.index).ffill()
            bench_ret = hs300['close'].pct_change().fillna(0)
            
            # Normalize benchmark value to 1.0 to align its starting point with the strategy.
            bench_cum = hs300['close'] / hs300['close'].iloc[0]

    # --------------------------
    # 3. Create a three-row, one-column plot.
    # Set the plotting style.
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(3, 1, figsize=(12, 14), gridspec_kw={'height_ratios': [2, 1, 1]})
    
    # Plot 1: cumulative returns and capital changes.
    ax1 = axes[0]
    ax1.plot(df.index, strat_cum, label='Strategy Capital', color="#36c412", linewidth=2)
    if bench_cum is not None:
        ax1.plot(df.index, bench_cum, label='000300.SH (Benchmark)', color='#2980b9', alpha=0.8, linewidth=1.5)
    
    ax1.set_title("Strategy vs Benchmark Cumulative Performance", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Cumulative Return (Base=1.0)", fontsize=11)
    ax1.legend(loc='upper left', fontsize=11)
    
    # Plot 2: maximum drawdown.
    ax2 = axes[1]
    ax2.fill_between(df.index, drawdown, 0, color='#e74c3c', alpha=0.3)
    ax2.plot(df.index, drawdown, color='#c0392b', linewidth=1)
    ax2.set_title("Strategy Drawdown", fontsize=14, fontweight='bold')
    ax2.set_ylabel("Drawdown (%)", fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    
    # Plot 3: rolling volatility.
    ax3 = axes[2]
    roll_window = 20 # 20 trading days (about one month)
    
    # Calculate rolling annualized volatility.
    strat_vol = strat_ret.rolling(window=roll_window).std() * np.sqrt(252)
    ax3.plot(df.index, strat_vol, label='Strategy 20d Volatility', color='#c0392b', alpha=0.8, linewidth=1.5)
    
    if bench_ret is not None:
        bench_vol = bench_ret.rolling(window=roll_window).std() * np.sqrt(252)
        ax3.plot(df.index, bench_vol, label='000300.SH 20d Volatility', color='#2980b9', alpha=0.8, linewidth=1.5)
        
    ax3.set_title("Rolling 20-Day Annualized Volatility", fontsize=14, fontweight='bold')
    ax3.set_ylabel("Volatility (%)", fontsize=11)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    ax3.legend(loc='upper left', fontsize=11)

    # --------------------------
    # 4. Format and save the chart.
    # Improve the X-axis date display.
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.grid(True, linestyle='--', alpha=0.6)
        
    plt.tight_layout()
    
    if save_path:
        save_p = Path(save_path)
        save_p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_p, dpi=300, bbox_inches='tight')
        print(f"✅ Plot successfully saved to {save_p}")
        
    plt.show()
