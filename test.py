import os
from dotenv import load_dotenv
import tushare as ts
import pandas as pd
from datetime import datetime

# -------------------
load_dotenv()
# -------------------
# Enter your Tushare token.
# -------------------
TOKEN = os.getenv("TUSHARE_TOKEN")

ts.set_token(TOKEN)
pro = ts.pro_api()

results = []

def record(test_name, success, fields=None, note=None):
    results.append({
        "Data_Item": test_name,
        "Available": success,
        "Returned_Fields": ",".join(fields) if fields else "",
        "Note": note if note else ""
    })


# 1. Individual-stock daily data, moving averages, and volume
try:
    df = pro.daily(
        ts_code='000001.SZ',
        start_date='20240101',
        end_date='20240331'
    )

    # Test whether moving averages can be calculated.
    for n in [10,20,50,120,200,240]:
        df[f"MA{n}"] = df["close"].rolling(n).mean()

    record(
        "Stock Daily + MA10/20/50/120/200/240 + Volume",
        True,
        fields=df.columns.tolist()
    )

except Exception as e:
    record(
        "Stock Daily + Moving Averages",
        False,
        note=str(e)
    )


# 2. Main-force trend (test using the money-flow API)
try:
    df = pro.moneyflow(
        ts_code='000001.SZ',
        start_date='20240101',
        end_date='20240131'
    )

    record(
        "Main Force Trend (Moneyflow proxy)",
        True,
        fields=df.columns.tolist()
    )

except Exception as e:
    record(
        "Main Force Trend (Moneyflow proxy)",
        False,
        note=str(e)
    )


# 3. Shenwan Level-1 sector index
try:
    df = pro.index_classify(
        level='L1',
        src='SW'
    )

    record(
        "Shenwan Level-1",
        True,
        fields=df.columns.tolist()
    )

except Exception as e:
    record(
        "Shenwan Level-1",
        False,
        note=str(e)
    )


# 4. Shenwan Level-2 sector index
try:
    df = pro.index_classify(
        level='L2',
        src='SW'
    )

    record(
        "Shenwan Level-2",
        True,
        fields=df.columns.tolist()
    )

except Exception as e:
    record(
        "Shenwan Level-2",
        False,
        note=str(e)
    )


# 5. Shanghai Stock Exchange Composite Index
try:
    df = pro.index_daily(
        ts_code='000001.SH',
        start_date='20240101',
        end_date='20240131'
    )

    record(
        "Shanghai Composite",
        True,
        fields=df.columns.tolist()
    )

except Exception as e:
    record(
        "Shanghai Composite",
        False,
        note=str(e)
    )


# 6. Shenzhen Stock Exchange Component Index
try:
    df = pro.index_daily(
        ts_code='399001.SZ',
        start_date='20240101',
        end_date='20240131'
    )

    record(
        "Shenzhen Component",
        True,
        fields=df.columns.tolist()
    )

except Exception as e:
    record(
        "Shenzhen Component",
        False,
        note=str(e)
    )


# Export CSV
out = pd.DataFrame(results)

filename = "tushare_permission_check.csv"
out.to_csv(filename, index=False, encoding="utf-8-sig")

print(f"Done. Results saved to {filename}")
print(out)
