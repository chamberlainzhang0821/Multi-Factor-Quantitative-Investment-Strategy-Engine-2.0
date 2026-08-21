import pandas as pd
from pathlib import Path
from config.paths import RAW_DATA_DIR, CLEAN_DATA_DIR

# Import basic cleaning steps.
from data_engine.clean.clean_prices import clean_prices
from data_engine.clean.missing_handler import handle_missing
from data_engine.clean.universe_filter import filter_universe
# Ensure filter_short_history is the time-freeze version.
from data_engine.clean.validate_data import validate, filter_short_history
from data_engine.clean.align_panel import align_panel

# Import panel-wide price-adjustment functions.
from data_engine.clean.forward_adj import get_adj_factor_panel, apply_price_adjustment_panel


def run_clean_pipeline():
    raw_price_dir = RAW_DATA_DIR / "daily_cross_section"
    raw_adj_dir = RAW_DATA_DIR / "adj_factor"
    clean_dir = CLEAN_DATA_DIR / "daily_cross_section"
    clean_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: perform daily basic cleaning without time-series missing-value filling.
    # A single-day cross-section cannot support forward/backward time-series filling.
    CLEAN_STEPS = [clean_prices, filter_universe]
    files = sorted(raw_price_dir.glob("*.parquet"))

    for f in files:
        out = clean_dir / f.name
        if out.exists():
            # Skip daily data that has already been cleaned.
            continue

        print(f"Basic daily cleaning for {f.name}...")
        df = pd.read_parquet(f)
        
        # Apply daily denoising and strict universe filters only.
        for step in CLEAN_STEPS:
            df = step(df)

        df.to_parquet(out, index=False)

    # Phase 2: concatenate daily data into the initial global panel.
    print("Building initial price panel for cross-sectional adjustment...")
    def load_panel(folder):
        if not folder.exists():
            return pd.DataFrame()
        panel_files = sorted(folder.glob("*.parquet"))
        if not panel_files:
            return pd.DataFrame()
        return pd.concat([pd.read_parquet(pf) for pf in panel_files], ignore_index=True)

    price_panel = load_panel(clean_dir)

    # Phase 3: apply robust panel-level price adjustment.
    print("Loading global adjustment factors...")
    # Load the complete adjustment-factor time series.
    df_all_adj, latest_factors_series = get_adj_factor_panel(raw_adj_dir)
    
    print("Applying strict panel-level split adjustment (ffill enabled)...")
    # Apply high-precision forward-filled adjustment to the full panel.
    price_panel = apply_price_adjustment_panel(price_panel, df_all_adj, latest_factors_series)

    # Phase 4: align external sources and perform final panel-level cleaning.
    print("Aligning external data sources...")
    moneyflow_panel = load_panel(RAW_DATA_DIR / "moneyflow")
    members_panel = pd.read_parquet(RAW_DATA_DIR / "sw_members.parquet")
    sector_prices_panel = pd.read_parquet(RAW_DATA_DIR / "sw_index_prices.parquet")
    index_prices_panel = load_panel(RAW_DATA_DIR / "indices")

    # Align and merge the global panel.
    panel = align_panel(
        price_panel, 
        moneyflow_panel, 
        members_panel, 
        sector_prices_panel,
        index_prices_panel
    )
    
    # After merging all sources, apply panel-level time-series missing-value filling.
    print("Executing panel-level missing values time-series imputation...")
    panel = handle_missing(panel)
    
    # Apply the time-freeze history filter, using 2025-05-26 as the boundary.
    # Before the boundary it preserves legacy total-day counting; after it uses strict cumulative counts.
    print("Executing Anchored Time-Freeze history filter (Threshold: 2025-05-26)...")
    panel = filter_short_history(panel, min_required_days=228)
    
    # Perform final uniqueness and integrity validation.
    # The validation assertion catches duplicate stock-day rows introduced during alignment.
    print("Running final dataset health validation...")
    validate(panel)
    
    # Write the historical-safe, backtest-ready panel.
    final_output = CLEAN_DATA_DIR / "aligned_panel.parquet"
    panel.to_parquet(final_output, index=False)
    print(f"🚀 SUCCESS: Aligned panel fully adjusted and saved to {final_output}!")


if __name__ == "__main__":
    run_clean_pipeline()
