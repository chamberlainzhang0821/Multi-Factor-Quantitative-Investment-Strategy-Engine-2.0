# Multi-Factor Quantitative Investment Strategy Engine 2.0📈

[English](#english) | [中文](#中文)

### 📊 Visualization & Results


![Backtest performance](backtest_performance.png)

### English

## Overview

Multi-Factor Quantitative Investment Strategy Engine 2.0 is an end-to-end China A-share workflow covering Tushare data collection, panel construction, price adjustment, factor calculation, cross-sectional scoring, T+1 execution, and performance evaluation.

It includes safeguards for identified risks: panel-level adjustment, time-series imputation, duplicate stock-date detection, and anchored history filtering. These controls reduce known leakage and data-corruption risks; they do not guarantee the removal of every possible look-ahead bias.

## Repository Structure

```text
├── config/          # Paths and strategy configuration
├── data_engine/     # Tushare fetching, cleaning, and panel alignment
├── factor_engine/   # Factor calculations and pipeline
├── signal_engine/   # Z-score combination and buy list
├── backtest/        # Portfolio, risk, evaluation, and plotting
├── research/        # IC and monotonicity scripts
├── data/            # Runtime data, ignored by Git
├── main.py          # End-to-end entry point
└── requirements.txt # Python dependencies
```
## Installation

Use Python 3.11 or later and install the pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows PowerShell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
## Tushare Token

Fetching requires a Tushare Pro token and the relevant data permissions. The current code calls `ts.pro_api()` directly; it does **not** automatically read `TUSHARE_TOKEN` or a `.env` file. Configure and verify the token before running:


```bash
python -c "import tushare as ts; ts.set_token('YOUR_TUSHARE_TOKEN'); print(ts.pro_api())"
```
Never commit tokens. `.env`, `config/credentials.json`, and `config/tushare_token.txt` are ignored by Git, but the current implementation will not load them unless token-loading code is added.

## Quick Start

Run the full workflow from the repository root:
```bash
python main.py
```
The workflow stages and outputs are:

1. **Fetch** — `python data_engine/fetch/run_fetch_pipeline.py`; downloads the universe, daily bars, adjustment factors, Shenwan sectors, money flow, and indices to `data/raw/`.
2. **Clean and align** — `python data_engine/clean/run_clean_pipeline.py`; writes `data/clean/aligned_panel.parquet`.
3. **Calculate factors** — `python factor_engine/run_factor_pipeline.py`; writes `data/factors/all_factors.parquet`.
4. **Score securities** — `python signal_engine/rank_signal.py`; writes `data/factors/factor_scores.parquet` and `data/factors/buy_list_YYYYMMDD.csv`.
5. **Backtest** — `python backtest/run_backtest_pipeline.py`; prints metrics and writes `backtest/results/backtest_performance.png`.

Each stage may be run separately once its upstream inputs exist.

## Key Configuration

| Setting | Default | Source | Effect |
| --- | ---: | --- | --- |
| Data lookback | `1825` calendar days | `DURATION_DAYS` | Rolling fetch window. |
| Factor blend | 9 factors, weight `1.0` each | `rank_signal.py` → `FACTOR_WEIGHTS` | Z-score blend into `alpha_score`. |
| Initial capital | `100,000` | backtest runner | Starting capital. |
| Daily selections | `5` | `TOP_N` | Maximum daily buy candidates. |
| Score threshold | `10.0` | `SCORE_THRESHOLD` | Minimum buy-signal score. |
| Target position | `20%` | `target_value` | New-position target value. |
| Slippage | `0.00` | `SLIPPAGE` | Per-trade assumption. |
| Daily stop loss | `6%` | `DAILY_STOP_LOSS_PCT` | Single-day exit threshold. |
| Portfolio freeze | disabled | `ENABLE_PORTFOLIO_FREEZE` | If enabled: 15% drawdown freezes trading for 7 days. |
| Time exit | disabled | `ENABLE_TIME_EXIT`; `HOLD_DAYS=9999` | Trend-following holding behavior. |

The current backtest runner is authoritative. Some legacy values in `config/strategy_config.py` are not consumed by this default path.

## Reproducing Results

The example results—Total Return **178.45%**, Sharpe **0.99**, Maximum Drawdown **-22.70%**, Win Rate **48.05%**, PnL Ratio **2.39**, and Annual Alpha **25.89%**—are historical outputs, not promised or fixed results.

The fetch window rolls to the execution date; results can change with execution date, Tushare revisions and permissions, and existing checkpoint files. The default run uses Tushare A-share data, CSI 300 (`000300.SH`) as benchmark, T+1 execution, zero slippage, and forced liquidation after missing-price days when that safeguard is enabled. The initial universe contains currently listed stocks and filters ST, BJ, ChiNext, STAR Market, sub-CNY-1 stocks, and rows lacking a Shenwan Level-1 mapping; it does not claim to provide a complete historical delisting universe.

For reproducible research, record the execution date, Tushare account/data version, raw-data snapshot, code commit, and the configuration above, then run `python main.py`.

## Validation, Contributions, and Limitations

- `analysis/inspect_panel.py` checks panel adjustment and OHLC consistency.
- `analysis/inspect_factors.py` checks factor coverage and distributions.
- `research/ic_analysis.py` evaluates information coefficients.
- `research/monotonicity_check.py` evaluates score-bucket monotonicity.

Inspect generated data and research outputs before relying on a result. A formal automated test suite and CI workflow have not yet been added.

Runtime data, factors, logs, and generated results are ignored by Git because they can be large, subject to provider terms, and need separate versioning. Contributions are welcome: open an issue first, keep changes focused, add validation where practical, and do not commit data, credentials, or IDE temporary files such as `tempCodeRunnerFile.py`.

This repository is for educational and research purposes only. It is not financial, investment, legal, or tax advice. Historical performance does not predict future performance; market risk, costs, survivorship bias, data errors, Tushare permissions, and data revisions can materially affect results.

## License

This project is licensed under the [MIT License](LICENSE).



### 中文

## 🚀 项目简介

Multi-Factor Quantitative Investment Strategy Engine 2.0 是一个面向中国 A 股市场的多因子选股与 T+1 量化回测项目，覆盖 Tushare 数据获取、面板构建、复权、因子计算、截面打分、信号执行和绩效评估。



项目针对已识别的风险提供了全局面板复权、时序缺失值填充、股票-日期重复行检测和锚定式历史过滤等机制。这些机制用于降低已知的数据泄漏和数据污染风险，但不保证消除所有形式的未来函数或前视偏差。


## 📂 项目架构
```text
├── config/          # 路径与策略配置
├── data_engine/     # Tushare 数据抓取、清洗与面板对齐
├── factor_engine/   # 因子计算与因子流水线
├── signal_engine/   # Z-score 合成与买入清单
├── backtest/        # 组合、风控、评估与绘图
├── research/        # IC 与单调性研究脚本
├── data/            # 运行时数据，已被 Git 忽略
├── main.py          # 完整流程入口
└── requirements.txt # Python 依赖
```
## 环境与安装

建议使用 Python 3.11 或更高版本，并安装锁定版本的依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows PowerShell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Tushare Token 配置
数据抓取需要 Tushare Pro Token 及相应的数据权限。当前代码直接调用 `ts.pro_api()`，**不会**自动读取 `TUSHARE_TOKEN` 或 `.env` 文件。请先配置并验证 Token：

```bash
python -c "import tushare as ts; ts.set_token('YOUR_TUSHARE_TOKEN'); print(ts.pro_api())"
```
请勿提交 Token。`.env`、`config/credentials.json` 和 `config/tushare_token.txt` 虽然已被 Git 忽略，但当前代码不会主动读取它们，除非你另行添加加载逻辑。

## 快速启动

在仓库根目录运行完整流程：
```bash
python main.py
```
流水线依次执行：

1. **数据抓取** — `python data_engine/fetch/run_fetch_pipeline.py`：下载股票池、日线、复权因子、申万行业、资金流和指数至 `data/raw/`。
2. **清洗与对齐** — `python data_engine/clean/run_clean_pipeline.py`：输出 `data/clean/aligned_panel.parquet`。
3. **因子计算** — `python factor_engine/run_factor_pipeline.py`：输出 `data/factors/all_factors.parquet`。
4. **股票打分** — `python signal_engine/rank_signal.py`：输出 `data/factors/factor_scores.parquet` 与 `data/factors/buy_list_YYYYMMDD.csv`。
5. **回测评估** — `python backtest/run_backtest_pipeline.py`：打印指标，并输出 `backtest/results/backtest_performance.png`。

在上游输入文件已存在时，各阶段均可以单独运行。

## 关键配置

| 配置项 | 默认值 | 来源 | 作用 |
| --- | ---: | --- | --- |
| 数据回溯窗口 | `1825` 个自然日 | `DURATION_DAYS` | 滚动抓取窗口。 |
| 因子合成 | 9 个因子，权重均为 `1.0` | `rank_signal.py` → `FACTOR_WEIGHTS` | 截面 Z-score 后合成为 `alpha_score`。 |
| 初始资金 | `100,000` | 回测入口 | 回测初始资金。 |
| 每日候选数 | `5` | `TOP_N` | 每日最多买入候选数。 |
| 分数阈值 | `10.0` | `SCORE_THRESHOLD` | 触发买入信号的最低分数。 |
| 单仓目标 | `20%` | `target_value` | 每笔新仓目标金额。 |
| 滑点 | `0.00` | `SLIPPAGE` | 单笔交易假设。 |
| 单日止损 | `6%` | `DAILY_STOP_LOSS_PCT` | 单日跌幅退出阈值。 |
| 组合熔断 | 默认关闭 | `ENABLE_PORTFOLIO_FREEZE` | 开启后，15% 回撤暂停交易 7 天。 |
| 时间退出 | 默认关闭 | `ENABLE_TIME_EXIT`；`HOLD_DAYS=9999` | 趋势跟随持有方式。 |

当前回测入口中的配置为默认执行路径的准则；`config/strategy_config.py` 中部分遗留配置未被该入口使用。

## 回测复现与结果解读

示例结果——总收益率 **178.45%**、夏普比率 **0.99**、最大回撤 **-22.70%**、胜率 **48.05%**、盈亏比 **2.39**、年化 Alpha **25.89%**——均为历史运行输出，不代表收益承诺，也不是固定不变的结果。

抓取窗口会滚动至执行当天，因此运行日期、Tushare 数据修订与权限、已有检查点文件均可能改变结果。默认设置使用 Tushare A 股数据、沪深 300（`000300.SH`）作为基准、T+1 信号执行和零滑点；在保护开关开启时，连续缺价达到阈值会强制平仓。初始股票池来自当前上市股票，并剔除 ST、北交所、创业板、科创板、低于 1 元股票和缺失申万一级行业映射的行；项目不声明提供完整的历史退市股票池。

如需进行可复现研究，请记录运行日期、Tushare 账户/数据版本、原始数据快照、代码提交版本和上述全部配置，再运行 `python main.py`。

## 验证、贡献与限制

- `analysis/inspect_panel.py`：检查面板复权和 OHLC 一致性。
- `analysis/inspect_factors.py`：检查因子覆盖与分布。
- `research/ic_analysis.py`：评估信息系数（IC）。
- `research/monotonicity_check.py`：评估分数组别单调性。

在依赖任何结果前，请检查生成数据与研究输出。项目目前尚未提供正式自动化测试套件和 CI 流程。

运行时数据、因子、日志和生成结果被 Git 忽略，因为它们可能体积较大、受数据供应商条款限制，并需要独立版本化。欢迎贡献：请先提交 Issue，保持改动聚焦，在可行时补充验证，且不要提交数据、凭据或 `tempCodeRunnerFile.py` 等 IDE 临时文件。

本仓库仅供教育与研究使用，不构成金融、投资、法律或税务建议。历史回测不能预测未来表现；市场风险、交易成本、幸存者偏差、数据错误、Tushare 权限和数据修订均可能显著影响结果。

## 许可证

本项目采用 [MIT License](LICENSE) 开源。