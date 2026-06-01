import pandas as pd

def align_panel(
    price,
    moneyflow,
    members,
    sector_prices,
    index_prices  # 🚀 新增参数
):

    price = price.copy()
    moneyflow = moneyflow.copy()
    members = members.copy()
    sector_prices = sector_prices.copy()
    index_prices = index_prices.copy()  # 🚀 新增：复制指数数据
    # 如果抓取到了指数数据才处理
    if not index_prices.empty:
        index_prices = index_prices.copy()

    # -----------------
    # dates
    # -----------------
    dfs_to_convert = [price, moneyflow, sector_prices]
    if not index_prices.empty:
        dfs_to_convert.append(index_prices)

    for df in dfs_to_convert:
        df["trade_date"] = pd.to_datetime(df["trade_date"])

    # -----------------
    # merge moneyflow
    # -----------------
    panel = price.merge(
        moneyflow,
        on=["ts_code", "trade_date"],
        how="left"
    )

    # -----------------
    # sector member mapping
    # -----------------
    l1_members = (
        members[
            members["index_code"].isin(
                members["index_code"].dropna().unique()
            )
        ]
        .merge(
            pd.DataFrame({
                "index_code": members["index_code"].dropna().unique()
            }),
            on="index_code"
        )
    )

    l1_members = (
        l1_members[
            l1_members["index_code"].isin(
                l1_members["index_code"].drop_duplicates()
            )
        ]
        .drop_duplicates(["con_code"])
        [["con_code", "index_code"]]
        .rename(
            columns={
                "con_code": "ts_code",
                "index_code": "sw_l1"
            }
        )
    )

    panel = panel.merge(
        l1_members,
        on="ts_code",
        how="left"
    )

    l2_members = (
        members
        .drop_duplicates(["con_code", "index_code"])
        .groupby("con_code")
        .tail(1)
        [["con_code", "index_code"]]
        .rename(
            columns={
                "con_code": "ts_code",
                "index_code": "sw_l2"
            }
        )
    )

    panel = panel.merge(
        l2_members,
        on="ts_code",
        how="left"
    )

    # -----------------
    # sector prices
    # -----------------
    l1_prices = (
        sector_prices[
            ["ts_code", "trade_date", "close"]
        ]
        .rename(
            columns={
                "ts_code": "sw_l1",
                "close": "sw_l1_close"
            }
        )
    )

    panel = panel.merge(
        l1_prices,
        on=["sw_l1", "trade_date"],
        how="left"
    )

    l2_prices = (
        sector_prices[
            ["ts_code", "trade_date", "close"]
        ]
        .rename(
            columns={
                "ts_code": "sw_l2",
                "close": "sw_l2_close"
            }
        )
    )

    panel = panel.merge(
        l2_prices,
        on=["sw_l2", "trade_date"],
        how="left"
    )

    # -----------------
    # 🚀 merge benchmark index (HS300)
    # -----------------
    if not index_prices.empty:
        # 提取沪深300的收盘价
        hs300 = (
            index_prices[index_prices["ts_code"] == "000300.SH"]
            [["trade_date", "close"]]
            .rename(columns={"close": "hs300_close"})
        )

        # 广播合并到所有个股面板 (每天一个固定的 hs300_close 值)
        panel = panel.merge(
            hs300,
            on="trade_date",
            how="left"
        )

    # -----------------
    # clean up and sort
    # -----------------
    mf_cols = [
      c for c in panel.columns
      if ("buy_" in c or "sell_" in c or "net_mf" in c)
    ]

    panel[mf_cols] = panel[mf_cols].fillna(0)
    panel = panel.sort_values(["ts_code", "trade_date"])

    return panel