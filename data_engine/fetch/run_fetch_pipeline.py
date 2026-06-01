from datetime import datetime

from data_engine.fetch.adj_factor import fetch_adj_factor
from data_engine.fetch.universe_fetch import fetch_universe
from data_engine.fetch.price_fetch import fetch_price
from data_engine.fetch.sector_fetch import fetch_sector
from data_engine.fetch.moneyflow_fetch import fetch_moneyflow
# 新增：导入我们刚写的指数抓取函数
from data_engine.fetch.index_fetch import fetch_index_data


def log(msg):
    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    print(f"[{now}] {msg}")


# 新增：写一个包装函数，把带参数的函数包装成无参函数，适配底下的 func() 循环
def fetch_index_wrapper():
    # ⚠️ 请确保这里的日期与你抓取个股 price 的全局配置日期一致
    # 如果你有一个 config 模块，建议改成类似 start_date=config.START_DATE
    fetch_index_data(start_date="20210101", end_date="20260502")


def run_fetch_pipeline():
    try:
        log("Data fetch pipeline started.")

        FETCH_STEPS = [
            ("Universe", fetch_universe),
            ("Prices", fetch_price),
            ("Adj_Factor", fetch_adj_factor),
            ("Sector", fetch_sector),
            ("Moneyflow", fetch_moneyflow),
            ("Indices", fetch_index_wrapper),  # 新增：把基准指数作为最后一步抓取
        ]

        for name, func in FETCH_STEPS:
            log(f"Fetching {name}...")
            func()

        log("Data fetch complete.")

    except Exception as e:
        log(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    run_fetch_pipeline()