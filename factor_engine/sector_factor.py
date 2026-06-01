def sector_factor(df):
    print("Calculating sector score...")
    df=df.copy()

    df=df.sort_values(
        ["sw_l1","sw_l2","trade_date"]
    )

    # ---------- 一级行业（去重后计算避免重复滚动） ----------

    l1=(
        df[["trade_date","sw_l1","sw_l1_close"]]
        .drop_duplicates()
        .sort_values(
            ["sw_l1","trade_date"]
        )
    )

    l1["l1_ma5"]=(
        l1.groupby("sw_l1")["sw_l1_close"]
        .transform(
           lambda x:x.rolling(5).mean()
        )
    )

    l1["l1_ma10"]=(
        l1.groupby("sw_l1")["sw_l1_close"]
        .transform(
           lambda x:x.rolling(10).mean()
        )
    )

    l1["l1_ma20"]=(
        l1.groupby("sw_l1")["sw_l1_close"]
        .transform(
           lambda x:x.rolling(20).mean()
        )
    )

    l1["l1_ma30"]=(
        l1.groupby("sw_l1")["sw_l1_close"]
        .transform(
           lambda x:x.rolling(30).mean()
        )
    )

    df=df.merge(
        l1[[
          "trade_date",
          "sw_l1",
          "l1_ma5",
          "l1_ma10",
          "l1_ma20",
          "l1_ma30"
        ]],
        on=["trade_date","sw_l1"],
        how="left"
    )


    # ---------- 二级行业（去重后计算避免重复滚动） ----------

    l2=(
        df[["trade_date","sw_l2","sw_l2_close"]]
        .drop_duplicates()
        .sort_values(
            ["sw_l2","trade_date"]
        )
    )

    l2["l2_ma5"]=(
        l2.groupby("sw_l2")["sw_l2_close"]
        .transform(
           lambda x:x.rolling(5).mean()
        )
    )

    l2["l2_ma10"]=(
        l2.groupby("sw_l2")["sw_l2_close"]
        .transform(
           lambda x:x.rolling(10).mean()
        )
    )

    l2["l2_ma20"]=(
        l2.groupby("sw_l2")["sw_l2_close"]
        .transform(
           lambda x:x.rolling(20).mean()
        )
    )

    l2["l2_ma30"]=(
        l2.groupby("sw_l2")["sw_l2_close"]
        .transform(
           lambda x:x.rolling(30).mean()
        )
    )

    df=df.merge(
        l2[[
          "trade_date",
          "sw_l2",
          "l2_ma5",
          "l2_ma10",
          "l2_ma20",
          "l2_ma30"
        ]],
        on=["trade_date","sw_l2"],
        how="left"
    )


    df["sector_score"]=0.0


    # 一级加分

    df.loc[
       df.l1_ma5>df.l1_ma10,
       "sector_score"
    ] +=1

    df.loc[
       df.l1_ma5>df.l1_ma20,
       "sector_score"
    ] +=0.75

    df.loc[
       df.l1_ma5>df.l1_ma30,
       "sector_score"
    ] +=0.5


    # 二级加分

    df.loc[
       df.l2_ma5>df.l2_ma10,
       "sector_score"
    ] +=1

    df.loc[
       df.l2_ma5>df.l2_ma20,
       "sector_score"
    ] +=0.75

    df.loc[
       df.l2_ma5>df.l2_ma30,
       "sector_score"
    ] +=0.5


    return df