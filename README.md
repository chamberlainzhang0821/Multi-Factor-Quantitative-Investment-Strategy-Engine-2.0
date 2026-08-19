# Stock Picking System 2.0

![Backtest]
(backtest/results/backtest_performance_copy.png)


When the first time to create the quantitative stock picking system (SPS), I was quite a rookie. I just finish the first semester in Math, still wondering applied math how it can actually be applied irl. The core concept of the first SPS was to find those stocks that are devalued, and we will do short. However, the plan and the skill was not very good at the time. The backtest engine was totally future function. Thus I decided to make some adjustment, so here is the SPS 2.0.

The core concept is to follow the trend. We use the factors and weights to find the trend on the market, making profit in a medium time (roughly 20-120 days). The system fundamentally contain five main part. The first part is data fetching, we fetch the data from Tushare dataset. There will be filter for this round, we will drop the "688" or "300" or "900" stocks, basically has a high demand for the scale of the fund. The second part is data cleaning. We mostly use pandas and numpy for filling N/A data, attaching, reduction and other action. In the third part, there would be the facotr calculation and scoring process. We have nine factors here. After the facotr calculation, it is the research part. We may check monotonicity and the info coefficient. Then, most importantly, the backtest engine. It is a well considered engine, containg features for ploting, evaluation, risk, portfolio etc. 

Rather than the system 1.0, the code this time written in a quite more rigorous way, especially on math and code quality. The leakage of the future function is well reduced. Following is a more detailed introduction.