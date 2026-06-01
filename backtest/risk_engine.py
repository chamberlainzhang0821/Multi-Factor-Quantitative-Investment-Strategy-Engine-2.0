import pandas as pd

class RiskEngine:
    
    def __init__(
        self, 
        max_portfolio_dd=0.15, 
        freeze_days=7, 
        daily_stop_loss_pct=0.06,        # 新增：单日跌幅止损阈值（6%）
        enable_time_exit=False,          # 开关1：到期平仓
        enable_stop_loss=True,           # 开关2：单日暴跌止损
        enable_portfolio_freeze=True,    # 开关3：大盘回撤熔断
        enable_delist_liquidation=True,  # 开关4：退市/停牌强平
        delist_missing_days=3,           # 容忍缺失天数
        delist_penalty=0.8               # 强平价格折扣 (8折)
    ):
        self.max_portfolio_dd = max_portfolio_dd
        self.freeze_days = freeze_days
        self.pause_until = None
        self.internal_peak = None        # 🚀 新增：内部独立维护资金最高点，彻底解决死锁
        self.daily_stop_loss_pct = daily_stop_loss_pct
        
        # 绑定开关状态
        self.enable_time_exit = enable_time_exit
        self.enable_stop_loss = enable_stop_loss
        self.enable_portfolio_freeze = enable_portfolio_freeze
        self.enable_delist_liquidation = enable_delist_liquidation
        self.delist_missing_days = delist_missing_days
        self.delist_penalty = delist_penalty

    def check_stock_exit(self, current_price, position, current_date, hold_days):
        """
        判断是否平仓，统一返回: (exit_flag, reason, exit_price)
        注意：外部调用时，不需要再传 atr_val 参数了
        """
        # 0. 处理数据缺失/停牌/退市 (处理 current_price 为 NaN 的情况)
        if pd.isna(current_price):
            position['missing_days'] = position.get('missing_days', 0) + 1
            
            if self.enable_delist_liquidation and position['missing_days'] >= self.delist_missing_days:
                # 触发打折强平，计算惩罚价
                penalty_price = position['entry_price'] * self.delist_penalty
                return True, "forced_delist_liquidation", penalty_price
                
            return False, None, current_price

        # 价格正常，重置缺失天数计数器
        position['missing_days'] = 0

        # 🚀 核心逻辑升级：记录“上一日的收盘价”，用于计算单日跌幅
        if 'last_price' not in position:
            position['last_price'] = position['entry_price']
            
        # 计算今天相对昨天（或建仓价）的真实跌幅
        daily_drop = 1 - (current_price / position['last_price'])
        
        # 无论今天卖不卖，先把今天的价格存下来，给明天做计算用
        position['last_price'] = current_price

        # 1. Time-based exit (到期强制卖出)
        if self.enable_time_exit:
            if (current_date - position['entry_date']).days >= hold_days:
                return True, "time_exit", current_price
            
        # 2. 单日暴跌止损 (浮动单日跌6%)
        if self.enable_stop_loss:
            # 如果今天比昨天跌了 6% (0.06) 及以上，直接止损
            if daily_drop >= self.daily_stop_loss_pct:
                return True, "daily_stop_loss", current_price
            
        # 安全度过所有风控检查，不卖
        return False, None, current_price

    def check_portfolio_risk(self, current_capital, current_date, peak_capital=None):
        """
        检查资金曲线是否严重回撤。
        注意：外部即使传入 peak_capital 也会被忽略，引擎将使用更安全的 internal_peak。
        """
        if not self.enable_portfolio_freeze:
            return False
            
        # 更新内部最高净值
        if self.internal_peak is None or current_capital > self.internal_peak:
            self.internal_peak = current_capital
            
        if self.internal_peak <= 0:
            return False
            
        # 计算距离最近一次“有效最高点”的回撤
        dd = 1 - (current_capital / self.internal_peak)
        
        if dd > self.max_portfolio_dd:
            self.pause_until = current_date + pd.Timedelta(days=self.freeze_days)
            
            # 💡 解决熔断死锁的关键点：
            # 熔断触发后，将【最高净值基准】强制重置为【当前资金】
            # 这意味着：熔断结束后，除非从当前这个烂摊子继续再跌 15%，否则恢复正常交易！
            self.internal_peak = current_capital 
            
            return True # 触发熔断
            
        return False

    def is_trading_frozen(self, current_date):
        """
        Returns True if the system is currently under a risk freeze.
        """
        if not self.enable_portfolio_freeze:
            return False
            
        if self.pause_until and current_date < self.pause_until:
            return True
            
        return False
