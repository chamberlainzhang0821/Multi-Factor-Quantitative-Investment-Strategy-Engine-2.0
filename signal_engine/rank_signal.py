import pandas as pd
from config.paths import FACTOR_DATA_DIR, ROOT_DIR
from datetime import datetime

def run_alpha_combiner():
    print("=" * 40)
    print("🧪 Starting Alpha Combination (Z-Scored)")
    print("=" * 40)
    
    # 1. 加载全量因子库
    input_file = FACTOR_DATA_DIR / "all_factors.parquet"
    if not input_file.exists():
        raise FileNotFoundError(f"All factors database not found at {input_file}. Run factor pipeline first.")
        
    print("Loading factor database...")
    df = pd.read_parquet(input_file)

    # ---------------------------------------------------------
    # 2. 核心配方权重表 (FACTOR WEIGHTS)
    # ---------------------------------------------------------
    FACTOR_WEIGHTS = {
        "momentum_score": 1.0,
        "trend_score": 1.0,
        "volume_score": 1.0,
        "stability_score": 1.0,
        "sector_score": 1.0,
        "atr_score": 1.0,       
        "main_force_score": 1.0,
        "squeeze_score": 1.0,
        "ignition_score": 1.0
    }

    print("Applying cross-sectional Z-score normalization...")
    df['alpha_score'] = 0.0
    
    # 3. 截面 Z-score 处理并合成 alpha_score
    active_factors = []
    for factor, weight in FACTOR_WEIGHTS.items():
        if weight != 0:
            if factor in df.columns:
                z_col_name = f"{factor}_z"
                df[z_col_name] = df.groupby('trade_date')[factor].transform(
                    lambda x: (x - x.mean()) / x.std() if x.std() != 0 else 0
                ).fillna(0)
                
                df['alpha_score'] += df[z_col_name] * weight
                active_factors.append(z_col_name)
                print(f"  - {factor} (Z-scored): {weight}")
            else:
                print(f"  ⚠️ Warning: {factor} is missing from the database!")

    # ---------------------------------------------------------
    # 4. 保存全量分数 (用于回测)
    # ---------------------------------------------------------
    output_file = FACTOR_DATA_DIR / "factor_scores.parquet"
    df.to_parquet(output_file, index=False)
    
    # ---------------------------------------------------------
    # 5. 🚀 新增功能：提取最新的“今日买入清单” CSV
    # ---------------------------------------------------------
    print("-" * 40)
    print("📅 Generating Today's Buy List...")
    
    # 获取数据中的最后交易日
    latest_date = df['trade_date'].max()
    
    # 提取最后一日的所有股票，并按 alpha_score 降序排列
    recommendations = df[df['trade_date'] == latest_date].copy()
    recommendations = recommendations.sort_values(by='alpha_score', ascending=False)
    
    # 筛选核心列：只保留代码、总分以及各个子项的 Z-score，方便观察为什么选它
    cols_to_export = ['ts_code', 'alpha_score'] + active_factors
    # 如果你的原始 df 里有名称（name）或行业（industry），也可以加进来
    if 'name' in recommendations.columns:
        cols_to_export.insert(1, 'name')

    # 定义保存路径
    csv_filename = f"buy_list_{latest_date.strftime('%Y%m%d')}.csv"
    csv_output_path = FACTOR_DATA_DIR / csv_filename
    
    # 导出前 20 名（或者全部，你可以根据需要调整）
    recommendations[cols_to_export].head(20).to_csv(csv_output_path, index=False, encoding='utf_8_sig')

    print("-" * 40)
    print(f"✅ Composite Z-scored alpha_score generated!")
    print(f"🚀 TODAY'S TOP PICKS ({latest_date.strftime('%Y-%m-%d')}):")
    print(recommendations[['ts_code', 'alpha_score']].head(5).to_string(index=False))
    print("-" * 40)
    print(f"📂 Full buy list saved to: {csv_output_path}")

if __name__ == "__main__":
    run_alpha_combiner()