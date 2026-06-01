import pandas as pd
import time
from pathlib import Path

from config.paths import CLEAN_DATA_DIR, FACTOR_DATA_DIR
from factor_engine.momentum import momentum_score
from factor_engine.trend import golden_cross_factor
#from factor_engine.relative_strength import relative_strength
from factor_engine.volume_filter import volume_confirmation
from factor_engine.stability import trend_stability
from factor_engine.sector_factor import sector_factor
from factor_engine.atr import atr_factor
from factor_engine.main_trend import trend_confirmation
from factor_engine.squeeze import compute_squeeze_score
from factor_engine.ignition import compute_ignition_score

def run_factor_pipeline():
    """
    量化因子生成总管道 (带内鬼实时动态审计与自愈系统)
    """
    panel_file = CLEAN_DATA_DIR / "aligned_panel.parquet"

    if not panel_file.exists():
        raise FileNotFoundError(f"{panel_file} not found. Please ensure the cleaning pipeline has finished successfully.")

    print("Loading aligned panel data...")
    df = pd.read_parquet(panel_file)

    # ---------------------------------------------------------
    # Factor Steps Definition
    # ---------------------------------------------------------
    factor_steps = [
        ("Momentum", momentum_score),
        ("GoldenCross", golden_cross_factor),
        #("RelativeStrength", relative_strength),
        ("Volume", volume_confirmation),
        ("Stability", trend_stability),
        ("Sector", sector_factor),
        ("ATR", atr_factor),
        ("MainTrend", trend_confirmation),
        ("Squeeze", compute_squeeze_score),
        ("Ignition", compute_ignition_score),
    ]

    total_start = time.perf_counter()

    for name, func in factor_steps:
        # 🛡️ 记录进入该因子前的行数和状态
        initial_rows = len(df)
        
        t0 = time.perf_counter()
        print(f"Running {name}...")
        
        # 链式流式加工 df
        df = func(df)
        
        elapsed = time.perf_counter() - t0
        
        # 🚨 【审计红外线】检查该因子函数出来后是否发生了细胞分裂
        current_rows = len(df)
        dup_mask = df.duplicated(["ts_code", "trade_date"])
        
        if current_rows > initial_rows or dup_mask.any():
            print(f"====================================================")
            print(f"🚨 抓到内鬼！因子【{name}】内部逻辑导致了数据膨胀或时序重复！")
            print(f"   - 运行前行数 : {initial_rows}")
            print(f"   - 运行后行数 : {current_rows} (暴增了 {current_rows - initial_rows} 行)")
            print(f"   - 发现重复行 : {dup_mask.sum()} 行")
            print(f"👉 正在为您执行管道内自愈去重，强行维持大面板纯净...")
            
            # 强行自愈去重，保留加工后的第一条记录，防范污染传递给后续因子
            df = df.drop_duplicates(subset=["ts_code", "trade_date"], keep="first")
            print(f"✅ 因子【{name}】带来的膨胀已被定点清除！")
            print(f"====================================================")
        else:
            print(f"✅ {name} finished cleanly in {elapsed:.2f} sec (Rows: {current_rows})")

    print("-" * 30)
    print(f"Total factor calculation time: {time.perf_counter()-total_start:.2f} sec")

    # ---------------------------------------------------------
    # 终极总关卡防御：确保输出的 parquet 绝对不能有重复
    # ---------------------------------------------------------
    final_dup = df.duplicated(["ts_code", "trade_date"]).any()
    if final_dup:
        df = df.drop_duplicates(subset=["ts_code", "trade_date"], keep="first")

    FACTOR_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = FACTOR_DATA_DIR / "all_factors.parquet"
    df.to_parquet(output_path, index=False)
    
    print(f"🚀 SUCCESS: Factor pipeline complete. Raw factors safely sanitized and saved to {output_path}")
    return df

if __name__ == "__main__":
    run_factor_pipeline()