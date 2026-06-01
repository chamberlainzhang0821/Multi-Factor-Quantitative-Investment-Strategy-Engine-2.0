import pandas as pd
from pathlib import Path
from config.paths import RAW_DATA_DIR, CLEAN_DATA_DIR

# 导入基础清洗步骤
from data_engine.clean.clean_prices import clean_prices
from data_engine.clean.missing_handler import handle_missing
from data_engine.clean.universe_filter import filter_universe
# 🚨 确保这里的 filter_short_history 已经是你刚刚替换过的“时光冻结版”函数
from data_engine.clean.validate_data import validate, filter_short_history
from data_engine.clean.align_panel import align_panel

# 导入全量面板复权函数
from data_engine.clean.forward_adj import get_adj_factor_panel, apply_price_adjustment_panel


def run_clean_pipeline():
    raw_price_dir = RAW_DATA_DIR / "daily_cross_section"
    raw_adj_dir = RAW_DATA_DIR / "adj_factor"
    clean_dir = CLEAN_DATA_DIR / "daily_cross_section"
    clean_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # 阶段 1: 仅执行单日基础清洗（不含缺失值时序填充）
    # ==========================================
    # 单日横截面只有 1 行数据，无法进行前向/后向时序填充。此处只做去噪与截面过滤。
    CLEAN_STEPS = [clean_prices, filter_universe]
    files = sorted(raw_price_dir.glob("*.parquet"))

    for f in files:
        out = clean_dir / f.name
        if out.exists():
            # 已经有清洗过的日线，就跳过
            continue

        print(f"Basic daily cleaning for {f.name}...")
        df = pd.read_parquet(f)
        
        # --- 仅执行单日去噪与股票池硬过滤 ---
        for step in CLEAN_STEPS:
            df = step(df)

        df.to_parquet(out, index=False)

    # ==========================================
    # 阶段 2: 将日线拼接成全局初始面板
    # ==========================================
    print("Building initial price panel for cross-sectional adjustment...")
    def load_panel(folder):
        if not folder.exists():
            return pd.DataFrame()
        panel_files = sorted(folder.glob("*.parquet"))
        if not panel_files:
            return pd.DataFrame()
        return pd.concat([pd.read_parquet(pf) for pf in panel_files], ignore_index=True)

    price_panel = load_panel(clean_dir)

    # ==========================================
    # 阶段 3: 执行防弹级“面板复权”
    # ==========================================
    print("Loading global adjustment factors...")
    # 获取全时间序列的因子大全表
    df_all_adj, latest_factors_series = get_adj_factor_panel(raw_adj_dir)
    
    print("Applying strict panel-level split adjustment (ffill enabled)...")
    # 对着整张大面板进行高精度前向填充复权
    price_panel = apply_price_adjustment_panel(price_panel, df_all_adj, latest_factors_series)

    # ==========================================
    # 阶段 4: 多源外部数据对齐 & 全量面板级终极清洗
    # ==========================================
    print("Aligning external data sources...")
    moneyflow_panel = load_panel(RAW_DATA_DIR / "moneyflow")
    members_panel = pd.read_parquet(RAW_DATA_DIR / "sw_members.parquet")
    sector_prices_panel = pd.read_parquet(RAW_DATA_DIR / "sw_index_prices.parquet")
    index_prices_panel = load_panel(RAW_DATA_DIR / "indices")

    # 执行大面板对齐合并
    panel = align_panel(
        price_panel, 
        moneyflow_panel, 
        members_panel, 
        sector_prices_panel,
        index_prices_panel
    )
    
    # 多源数据合流后，统一进行面板级【缺失值时序填充】
    print("Executing panel-level missing values time-series imputation...")
    panel = handle_missing(panel)
    
    # 🚨 核心联动修正：调用全新“时光冻结版”历史天数过滤
    # 该函数内部会自动以 2025-05-26 为分水岭：
    # 1. 2025-05-26 之前：维持老逻辑的总天数统计（保住历史高收益核心）
    # 2. 2025-05-26 之后：采用严格的滚动递增累计计数，绝不篡改历史
    print("Executing Anchored Time-Freeze history filter (Threshold: 2025-05-26)...")
    panel = filter_short_history(panel, min_required_days=228)
    
    # 最终数据唯一性完整性校验
    # 🚨 注意：如果之前提到的单天个股分身 Bug（如 600360.SH 出现两次）发生在 align 阶段，
    # 这里的 validate(panel) 断言将会直接报错挂掉，提前帮你拦截潜在灾难！
    print("Running final dataset health validation...")
    validate(panel)
    
    # 输出对历史高度免疫、兼顾旧收益表现的金标回测面板
    final_output = CLEAN_DATA_DIR / "aligned_panel.parquet"
    panel.to_parquet(final_output, index=False)
    print(f"🚀 SUCCESS: Aligned panel fully adjusted and saved to {final_output}!")


if __name__ == "__main__":
    run_clean_pipeline()