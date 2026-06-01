import tushare as ts
import pandas as pd

from config.paths import RAW_DATA_DIR
from config.paths import DATA_DIR

from config.strategy_config import EXCLUDE_ST


pro = ts.pro_api()


def fetch_universe():

    df = pro.stock_basic(
        exchange='',
        list_status='L',
        fields='ts_code,name,industry,list_date'
    )

    if EXCLUDE_ST:
        df = df[~df['name'].str.contains('ST')]

    # full raw save
    df.to_parquet(
        RAW_DATA_DIR/"stock_universe.parquet",
        index=False
    )
    df = pro.stock_basic(
        
        list_status='L',   
    )
    df = df[~df['name'].str.contains('ST')]
    # audit sample
    df.head(100).to_csv(
        DATA_DIR/"audit_csv_universe.csv",
        index=False
    )
    today=pd.Timestamp.today()

    df['list_days']=(
     today-pd.to_datetime(df.list_date)
    ).dt.days

    print("Universe fetched.")


if __name__=="__main__":
    fetch_universe()