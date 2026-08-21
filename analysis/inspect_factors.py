import pandas as pd

df = pd.read_parquet(
    "data/factors/factor_scores.parquet"
)

print("\nPanel shape:")
print(df.shape)

print("\nUnique trade dates:")
print(df["trade_date"].nunique())

print("\nUnique stocks:")
print(df["ts_code"].nunique())

print("\nDate range:")
print(
    df["trade_date"].min(),
    "to",
    df["trade_date"].max()
)

print("\nRows per trade date (sample):")
print(
    df.groupby("trade_date")
      .size()
      .describe()
)

# Automatically detect factor columns.
print("\n" + "="*40)
print("🔍 Factor Column Detection")
print("="*40)

# Find columns ending in _score or _factor, excluding alpha_score itself.
detected_factors = [
    col for col in df.columns 
    if ('_score' in col or '_factor' in col) and col != 'alpha_score'
]

print(f"Detected {len(detected_factors)} individual factor columns:")
for f in detected_factors:
    print(f"  - {f}")

if "alpha_score" in df.columns:
    print("\n✅ 'alpha_score' is PRESENT in the dataset.")
    # Add alpha_score to the list whose distributions are inspected.
    detected_factors.append("alpha_score")
else:
    print("\n❌ WARNING: 'alpha_score' is MISSING! SignalEngine will fail.")

print("\n" + "="*40)
print("📊 Factor Distributions")
print("="*40)

# Print statistics for all detected factors, including alpha_score.
print(df[detected_factors].describe())

print("\nValue counts (excluding alpha_score and continuous variables):\n")
# alpha_score is usually continuous, so value_counts is not useful; exclude it here.
# Other continuous factors can likewise be excluded to inspect only discrete scores.
for c in [col for col in detected_factors if col != "alpha_score"]:
    # Treat fewer than 20 unique values as a discrete score suitable for value_counts.
    if df[c].nunique() < 20:
        print(f"\n--- {c} ---")
        print(
            df[c]
            .value_counts(normalize=True)
            .sort_index()
        )
    else:
        print(f"\n--- {c} (Continuous / {df[c].nunique()} unique values) ---")
