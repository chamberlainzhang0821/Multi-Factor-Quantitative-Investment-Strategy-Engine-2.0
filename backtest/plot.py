import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

def plot_backtest_results(equity_df, benchmark_file=None, save_path=None):
    """
    绘制量化策略回测的经典三板块分析图：
    1. 累计净值与基准对比 (Cumulative Returns)
    2. 策略动态回撤图 (Drawdown)
    3. 滚动年化波动率对比 (Rolling Volatility)
    """
    print("🎨 Generating backtest performance plots...")
    
    # --------------------------
    # 1. 处理策略资金数据
    # --------------------------
    # 🚀 关键修复：不管传进来的是 list 还是 df，统一强转成 DataFrame
    df = pd.DataFrame(equity_df)
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
    
    strat_capital = df['capital']
    strat_ret = strat_capital.pct_change().fillna(0)
    
    # 净值归一化 (起点为 1.0)
    strat_cum = strat_capital / strat_capital.iloc[0]
    
    # 计算动态回撤
    cum_max = strat_capital.cummax()
    drawdown = (strat_capital / cum_max) - 1.0

    # --------------------------
    # 2. 处理沪深300基准数据
    # --------------------------
    bench_cum = None
    bench_ret = None
    if benchmark_file:
        b_path = Path(benchmark_file)
        if b_path.exists():
            hs300 = pd.read_parquet(b_path)
            hs300['trade_date'] = pd.to_datetime(hs300['trade_date'])
            hs300 = hs300.set_index('trade_date').sort_index()
            
            # 对齐日期，缺失值前向填充
            hs300 = hs300.reindex(df.index).ffill()
            bench_ret = hs300['close'].pct_change().fillna(0)
            
            # 基准净值归一化 (为了和策略起点对齐，起点也设为 1.0)
            bench_cum = hs300['close'] / hs300['close'].iloc[0]

    # --------------------------
    # 3. 开始绘图 (3行1列的画布)
    # --------------------------
    # 设置风格
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(3, 1, figsize=(12, 14), gridspec_kw={'height_ratios': [2, 1, 1]})
    
    # --- 图1: 累计收益与资本变化 (Capital & Returns) ---
    ax1 = axes[0]
    ax1.plot(df.index, strat_cum, label='Strategy Capital', color="#36c412", linewidth=2)
    if bench_cum is not None:
        ax1.plot(df.index, bench_cum, label='000300.SH (Benchmark)', color='#2980b9', alpha=0.8, linewidth=1.5)
    
    ax1.set_title("Strategy vs Benchmark Cumulative Performance", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Cumulative Return (Base=1.0)", fontsize=11)
    ax1.legend(loc='upper left', fontsize=11)
    
    # --- 图2: 最大回撤图 (Drawdown) ---
    ax2 = axes[1]
    ax2.fill_between(df.index, drawdown, 0, color='#e74c3c', alpha=0.3)
    ax2.plot(df.index, drawdown, color='#c0392b', linewidth=1)
    ax2.set_title("Strategy Drawdown", fontsize=14, fontweight='bold')
    ax2.set_ylabel("Drawdown (%)", fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    
    # --- 图3: 波动率变化图 (Rolling Volatility) ---
    ax3 = axes[2]
    roll_window = 20 # 20个交易日(约1个月)
    
    # 计算年化滚动波动率
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
    # 4. 图表美化与保存
    # --------------------------
    # 优化X轴的时间显示
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