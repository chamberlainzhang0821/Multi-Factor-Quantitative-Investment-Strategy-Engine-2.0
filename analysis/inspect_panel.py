import pandas as pd

df = pd.read_parquet(
   "data/clean/aligned_panel.parquet"
)

print(df.shape)

print(df.columns)

print(df.head())


print(
    df.groupby(
      'ts_code'
    ).size().describe()
)

print(
    df.duplicated(
      ['ts_code','trade_date']
    ).sum()
)

print(
    df.isna().mean().sort_values(
      ascending=False
    ).head(10)
)

print(df['amount'].describe())

print("\nMissing sector mapping stock count:")
print(
    df[df['sw_l1'].isna()]
    ['ts_code']
    .drop_duplicates()
    .shape
)

print("\nExample stocks missing sector mapping:")
print(
    df[df['sw_l1'].isna()]
    ['ts_code']
    .drop_duplicates()
    .head(20)
)

print("\nRows missing sector mapping:")
print(
    df['sw_l1'].isna().sum()
)

print("\nCheck whether missingness is mapping issue:")
print(
    df[
      ['sw_l1','sw_l1_close']
    ]
    .isna()
    .mean()
)

print("\nSector price missing conditional on having sector code:")
mask = df['sw_l1'].notna()
print(
    df.loc[
      mask,
      'sw_l1_close'
    ].isna().mean()
)

print("\nTop stocks by missing sector rows:")
print(
    df[df['sw_l1'].isna()]
    .groupby('ts_code')
    .size()
    .sort_values(ascending=False)
    .head(20)
)


print("\n" + "="*50)
print("--- Split-Adjustment (复权) Verification ---")
print("="*50)

# Ensure the data is sorted correctly.
df = df.sort_values(['ts_code', 'trade_date'])

# 1. Calculate theoretical daily returns (Close / prior-day Close - 1).
df['daily_ret'] = df.groupby('ts_code')['close'].pct_change()

# 2. Check for artificial cliff-like declines beyond A-share limits.
# Use -25% as the threshold; even a 20% STAR Market limit-down should not exceed it.
# Many -30% to -50% records indicate failed adjustment.
extreme_drops = df[df['daily_ret'] < -0.25]

print(f"\nNumber of extreme daily drops (< -25%): {len(extreme_drops)}")

if len(extreme_drops) > 50: # Allow a small number of outliers, such as delisting consolidation periods
    print("❌ WARNING: Too many extreme price drops! Data might NOT be fully adjusted.")
    print("Sample of extreme drops (Check if these are ex-dividend dates):")
    print(extreme_drops[['ts_code', 'trade_date', 'close', 'daily_ret']].head(10))
else:
    print("✅ SUCCESS: No massive price gaps found. Data appears properly adjusted.")


# 3. Check the historical scaling effect of forward adjustment.
# Forward adjustment scales older actual prices down; spot-check historical lows of long-standing dividend payers.
print("\n--- Check Historic Prices of Classic Stocks ---")

test_stocks = {
    '000001.SZ': 'Ping An Bank',
    '600519.SH': 'Kweichow Moutai'
}

for code, name in test_stocks.items():
    stock_data = df[df['ts_code'] == code]
    if not stock_data.empty:
        oldest_record = stock_data.iloc[0]
        latest_record = stock_data.iloc[-1]
        print(f"\n{name} ({code}):")
        print(f"  Oldest Date ({oldest_record['trade_date'].strftime('%Y-%m-%d')}): Close = {oldest_record['close']:.2f}")
        print(f"  Latest Date ({latest_record['trade_date'].strftime('%Y-%m-%d')}): Close = {latest_record['close']:.2f}")
        print("  (💡 If the oldest close is significantly lower than the actual historical unadjusted price, forward-adjustment worked!)")


# 4. Check OHLC consistency: adjusted highs must not be below adjusted lows.
print("\n--- Adjusted OHLC Consistency ---")
invalid_ohlc = df[
    (df['high'] < df['low']) | 
    (df['high'] < df['close']) | 
    (df['low'] > df['open'])
]
print(f"Invalid OHLC rows after adjustment: {len(invalid_ohlc)}")
if len(invalid_ohlc) > 0:
    print(invalid_ohlc[['ts_code', 'trade_date', 'open', 'high', 'low', 'close']].head())

# 5. Remove columns used for testing.
df = df.drop(columns=['daily_ret'])
