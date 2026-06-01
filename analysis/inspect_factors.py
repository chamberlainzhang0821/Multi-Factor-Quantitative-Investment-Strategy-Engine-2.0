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

# ==========================================
# 🚀 自动检测因子列 (核心修改在这里)
# ==========================================
print("\n" + "="*40)
print("🔍 Factor Column Detection")
print("="*40)

# 自动找出所有以 _score 或 _factor 结尾的列，并排除 alpha_score 本身
detected_factors = [
    col for col in df.columns 
    if ('_score' in col or '_factor' in col) and col != 'alpha_score'
]

print(f"Detected {len(detected_factors)} individual factor columns:")
for f in detected_factors:
    print(f"  - {f}")

if "alpha_score" in df.columns:
    print("\n✅ 'alpha_score' is PRESENT in the dataset.")
    # 把 alpha_score 加进我们要看分布的列表里
    detected_factors.append("alpha_score")
else:
    print("\n❌ WARNING: 'alpha_score' is MISSING! SignalEngine will fail.")

print("\n" + "="*40)
print("📊 Factor Distributions")
print("="*40)

# 打印所有探测到的因子的统计信息 (包括 alpha_score)
print(df[detected_factors].describe())

print("\nValue counts (excluding alpha_score and continuous variables):\n")
# 通常 alpha_score 是连续变量，打印 value_counts 没太大意义，所以我们排除它
# 也可以排除其他连续因子，只看离散得分（比如只有 0, 1, 2 的得分）
for c in [col for col in detected_factors if col != "alpha_score"]:
    # 简单判断一下，如果独特值少于20个，说明是离散打分，打印 value_counts 才好看
    if df[c].nunique() < 20:
        print(f"\n--- {c} ---")
        print(
            df[c]
            .value_counts(normalize=True)
            .sort_index()
        )
    else:
        print(f"\n--- {c} (Continuous / {df[c].nunique()} unique values) ---")