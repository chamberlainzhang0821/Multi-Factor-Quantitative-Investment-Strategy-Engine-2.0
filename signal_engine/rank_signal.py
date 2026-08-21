import pandas as pd
from config.paths import FACTOR_DATA_DIR, ROOT_DIR
from datetime import datetime

def run_alpha_combiner():
    print("=" * 40)
    print("🧪 Starting Alpha Combination (Z-Scored)")
    print("=" * 40)
    
    # 1. Load the full factor database
    input_file = FACTOR_DATA_DIR / "all_factors.parquet"
    if not input_file.exists():
        raise FileNotFoundError(f"All factors database not found at {input_file}. Run factor pipeline first.")
        
    print("Loading factor database...")
    df = pd.read_parquet(input_file)

    # ---------------------------------------------------------
    # 2. Core factor weights
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
    
    # 3. Apply cross-sectional Z-scores and combine them into alpha_score
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
    # 4. Save full scores for backtesting
    # ---------------------------------------------------------
    output_file = FACTOR_DATA_DIR / "factor_scores.parquet"
    df.to_parquet(output_file, index=False)
    
    # ---------------------------------------------------------
    # 5. Export the latest daily buy list to CSV
    # ---------------------------------------------------------
    print("-" * 40)
    print("📅 Generating Today's Buy List...")
    
    # Get the final trading day in the data
    latest_date = df['trade_date'].max()
    
    # Extract all stocks on the final day and sort by alpha_score descending
    recommendations = df[df['trade_date'] == latest_date].copy()
    recommendations = recommendations.sort_values(by='alpha_score', ascending=False)
    
    # Keep the code, total score, and component Z-scores for review
    cols_to_export = ['ts_code', 'alpha_score'] + active_factors
    # Include the name when it is available in the source data
    if 'name' in recommendations.columns:
        cols_to_export.insert(1, 'name')

    # Define the output path
    csv_filename = f"buy_list_{latest_date.strftime('%Y%m%d')}.csv"
    csv_output_path = FACTOR_DATA_DIR / csv_filename
    
    # Export the top 20, or adjust this limit as needed
    recommendations[cols_to_export].head(20).to_csv(csv_output_path, index=False, encoding='utf_8_sig')

    print("-" * 40)
    print(f"✅ Composite Z-scored alpha_score generated!")
    print(f"🚀 TODAY'S TOP PICKS ({latest_date.strftime('%Y-%m-%d')}):")
    print(recommendations[['ts_code', 'alpha_score']].head(5).to_string(index=False))
    print("-" * 40)
    print(f"📂 Full buy list saved to: {csv_output_path}")

if __name__ == "__main__":
    run_alpha_combiner()
