import backtrader as bt
import numpy as np
import pandas as pd

class BollingerBandsStrategy(bt.Strategy):
    """布林带策略"""
    
    params = (
        ('bb_period', 20),         # 布林带周期
        ('bb_dev', 2.0),           # 布林带标准差倍数
        ('position_size', 0.1),     # 仓位大小
        ('stop_loss', 0.02),        # 止损比例
        ('take_profit', 0.04),      # 止盈比例
    )
    
    def __init__(self):
        # 初始化订单变量
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 布林带指标
        self.bb = bt.indicators.BollingerBands(
            self.data.close, 
            period=self.p.bb_period, 
            devfactor=self.p.bb_dev
        )
        
        # 记录交易统计
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        
        # 资金跟踪
        self.portfolio_values = []
        self.trade_dates = []
        
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
        
        self.order = None
    
    def notify_trade(self, trade):
        """交易完成通知"""
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        if trade.pnl > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        self.log(f'交易完成, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
        if self.trade_count > 0:
            self.log(f'胜率: {self.win_count}/{self.trade_count} ({self.win_count/self.trade_count*100:.1f}%)')
    
    def next(self):
        """主要策略逻辑 - 布林带策略"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        self.trade_dates.append(len(self.data))
        
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 获取当前价格和布林带值
        current_price = self.data.close[0]
        bb_upper = self.bb.lines.top[0]
        bb_lower = self.bb.lines.bot[0]
        bb_middle = self.bb.lines.mid[0]
        
        # 检查是否持仓
        if not self.position:
            # 买入条件：价格触及下轨
            if current_price <= bb_lower:
                self.log(f'买入信号, 价格: {current_price:.2f}, 布林带下轨: {bb_lower:.2f}')
                self.order = self.buy(size=self.p.position_size)
        
        else:
            # 持仓时的卖出逻辑
            sell_signal = False
            sell_reason = ""
            
            # 止损
            if current_price < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                sell_reason = "止损"
            
            # 止盈
            elif current_price > self.buyprice * (1 + self.p.take_profit):
                sell_signal = True
                sell_reason = "止盈"
            
            # 布林带卖出信号：价格触及上轨
            elif current_price >= bb_upper:
                sell_signal = True
                sell_reason = f"布林带上轨卖出 (价格: {current_price:.2f}, 上轨: {bb_upper:.2f})"
            
            # 价格回到中轨附近
            elif current_price >= bb_middle * 0.99:
                sell_signal = True
                sell_reason = f"价格回到中轨 (价格: {current_price:.2f}, 中轨: {bb_middle:.2f})"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=self.p.position_size)

class TurtleTradingStrategy(bt.Strategy):
    """海龟交易策略"""
    
    params = (
        ('entry_period', 20),       # 入场突破周期
        ('exit_period', 10),        # 出场突破周期
        ('atr_period', 20),         # ATR周期
        ('position_size', 0.1),     # 仓位大小
        ('risk_percent', 0.02),     # 风险百分比
    )
    
    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 海龟交易指标
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.entry_period)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.entry_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # 出场指标
        self.exit_highest = bt.indicators.Highest(self.data.high, period=self.p.exit_period)
        self.exit_lowest = bt.indicators.Lowest(self.data.low, period=self.p.exit_period)
        
        # 记录交易统计
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        
        # 资金跟踪
        self.portfolio_values = []
        self.trade_dates = []
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}')
                self.buyprice = order.executed.price
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}')
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        if trade.pnl > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        self.log(f'交易完成, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
        if self.trade_count > 0:
            self.log(f'胜率: {self.win_count}/{self.trade_count} ({self.win_count/self.trade_count*100:.1f}%)')
    
    def next(self):
        """主要策略逻辑 - 海龟交易策略"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        self.trade_dates.append(len(self.data))
        
        if self.order:
            return
        
        # 获取当前价格和指标值
        current_price = self.data.close[0]
        current_high = self.data.high[0]
        current_low = self.data.low[0]
        
        # 突破水平
        entry_high = self.highest[0]
        entry_low = self.lowest[0]
        
        # 出场水平
        exit_high = self.exit_highest[0]
        exit_low = self.exit_lowest[0]
        
        # 检查是否持仓
        if not self.position:
            # 买入条件：突破20日高点
            if current_high > entry_high:
                self.log(f'买入信号, 价格: {current_price:.2f}, 突破高点: {entry_high:.2f}')
                self.order = self.buy(size=self.p.position_size)
        
        else:
            # 持仓时的卖出逻辑
            sell_signal = False
            sell_reason = ""
            
            # 海龟出场：突破10日低点
            if current_low < exit_low:
                sell_signal = True
                sell_reason = f"海龟出场 (价格: {current_price:.2f}, 突破低点: {exit_low:.2f})"
            
            # 止损：基于ATR的动态止损
            elif self.atr[0] > 0:
                atr_stop = self.buyprice - 2 * self.atr[0]
                if current_price < atr_stop:
                    sell_signal = True
                    sell_reason = f"ATR止损 (价格: {current_price:.2f}, 止损价: {atr_stop:.2f})"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=self.p.position_size)

class SignalLevelReverseStrategy(bt.Strategy):
    """基于信号量等级的反向策略（根据IC检验结果，信号量等级和5期收益率成反比）"""
    
    params = (
        ('signal_level_threshold', 6),  # 信号量等级阈值
        ('position_size', 0.1),         # 仓位大小
        ('stop_loss', 0.02),            # 止损比例
        ('take_profit', 0.04),          # 止盈比例
        ('lookback_period', 5),         # 回看期数（对应5期收益率）
    )
    
    def __init__(self):
        # 初始化订单变量
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 信号量等级指标
        self.signal_level = self.datas[0].信号量_等级
        
        # 计算5期收益率
        self.returns_5 = bt.indicators.PercentChange(self.data.close, period=self.p.lookback_period)
        
        # 记录交易统计
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        
        # 资金跟踪
        self.portfolio_values = []
        self.trade_dates = []
        
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}')
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
        
        self.order = None
    
    def notify_trade(self, trade):
        """交易完成通知"""
        if not trade.isclosed:
            return
        
        self.trade_count += 1
        if trade.pnl > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        self.log(f'交易完成, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
        if self.trade_count > 0:
            self.log(f'胜率: {self.win_count}/{self.trade_count} ({self.win_count/self.trade_count*100:.1f}%)')
    
    def next(self):
        """主要策略逻辑 - 基于信号量等级的反向策略"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        self.trade_dates.append(len(self.data))
        
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 获取当前信号量等级和5期收益率
        current_signal_level = self.signal_level[0]
        current_returns_5 = self.returns_5[0]
        
        # 检查是否持仓
        if not self.position:
            # 反向买入条件：信号量等级高时买入（预期未来收益率会下降）
            if current_signal_level >= self.p.signal_level_threshold:
                self.log(f'反向买入信号, 信号量等级: {current_signal_level}, 5期收益率: {current_returns_5:.4f}')
                self.order = self.buy(size=self.p.position_size)
        
        else:
            # 持仓时的卖出逻辑
            sell_signal = False
            sell_reason = ""
            
            # 止损
            if self.data.close[0] < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                sell_reason = "止损"
            
            # 止盈
            elif self.data.close[0] > self.buyprice * (1 + self.p.take_profit):
                sell_signal = True
                sell_reason = "止盈"
            
            # 反向卖出信号：信号量等级降低时卖出
            elif current_signal_level < self.p.signal_level_threshold * 0.8:
                sell_signal = True
                sell_reason = f"信号量等级降低 (当前: {current_signal_level}, 阈值: {self.p.signal_level_threshold})"
            
            # 5期收益率反转信号
            elif current_returns_5 < -0.01:  # 5期收益率为负时卖出
                sell_signal = True
                sell_reason = f"5期收益率反转 (收益率: {current_returns_5:.4f})"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=self.p.position_size) 