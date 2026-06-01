import tushare as ts
import pandas as pd

pro = ts.pro_api()

def filter_universe(df):
    """
    全量面板股票池过滤：剔除北交所、科创、创业、ST、仙股及缺失行业映射的标的
    """
    print(f"Original universe size: {len(df)}")

    # 1. 剔除北交所 (.BJ)
    df = df[~df["ts_code"].str.endswith(".BJ")]

    # 2. 剔除创业板 (300, 301) 和 科创板 (688, 689)
    # 你的中长线策略更适合主板的 10% 涨跌幅，过滤掉 20% 的高波动噪音
    df = df[~df["ts_code"].str.startswith(("300", "301", "688", "689"))]

    # 3. 剔除“仙股”和濒临退市的垃圾股（价格补丁）
    # A股有“面值退市”规则（连续20天低于1元退市），低于 1 元的标的不仅毫无趋势可言，还极易出现数据错乱。
    # 这里用 1.0 或 0.5 都可以，为了安全起见，剔除 1 块钱以下的。
    if "close" in df.columns:
        df = df[df["close"] >= 1.0]

    # 4. 剔除申万行业 mapping 缺失的孤儿股（比如还没纳入指数的新股）
    # 直接丢弃那些连行业都没分进去的票
    if "sw_l1" in df.columns:
        df = df.dropna(subset=["sw_l1"])

    # 5. ST 股票过滤 (你的原有逻辑，但我加了安全保护)
    # ⚠️ 提示：你这种取 df['trade_date'].max() 的写法，只能取到【回测最后一天】的 ST 名单。
    # 对于 5 年回测，这会漏掉那些“曾经在 2022 年是 ST，但后来摘帽了”的股票。
    # 暂且保留你的逻辑，但你可以考虑后续把 ST 状态像 adj_factor 一样做成面板数据。
    try:
        max_date = pd.to_datetime(df["trade_date"]).max()
        st = pro.stock_st(trade_date=max_date.strftime("%Y%m%d"))
        
        if not st.empty:
            st_codes = set(st["ts_code"])
            df = df[~df["ts_code"].isin(st_codes)]
    except Exception as e:
        print(f"Warning: Failed to fetch ST list. Error: {e}")

    print(f"Filtered universe size: {len(df)}")
    
    return df