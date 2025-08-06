import backtrader as bt
import numpy as np
import pandas as pd

class BollingerBandsStrategy(bt.Strategy):
    """优化的布林带策略"""
    
    params = (
        ('bb_period', 15),         # 布林带周期 (缩短以提高敏感度)
        ('bb_dev', 1.8),           # 布林带标准差倍数 (降低以增加信号)
        ('position_size', 0.3),     # 仓位大小 (增加到30%)
        ('stop_loss', 0.03),        # 止损比例 (适当放宽)
        ('take_profit', 0.06),      # 止盈比例 (提高盈利目标)
        ('min_volume_ratio', 1.2),  # 最小成交量比率
        ('trend_filter', True),     # 是否启用趋势过滤
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
        
        # 趋势指标
        if self.p.trend_filter:
            self.sma_fast = bt.indicators.SMA(self.data.close, period=10)
            self.sma_slow = bt.indicators.SMA(self.data.close, period=20)
        
        # 成交量指标
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=20)
        
        # 动态仓位计算
        self.atr = bt.indicators.ATR(self.data, period=14)
        
        # 交易控制
        self.last_trade_bar = -10  # 上次交易的bar数
        self.cooldown_period = 5   # 交易冷却期（5个bar）
        
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
        """修复的布林带策略逻辑"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 检查交易冷却期
        current_bar = len(self.data)
        if current_bar - self.last_trade_bar < self.cooldown_period:
            return
        
        # 获取当前价格和指标值
        current_price = self.data.close[0]
        bb_upper = self.bb.lines.top[0]
        bb_lower = self.bb.lines.bot[0]
        bb_middle = self.bb.lines.mid[0]
        current_volume = self.data.volume[0]
        
        # 成交量过滤（降低要求）
        volume_filter = current_volume > self.volume_sma[0] * 1.1  # 降低成交量要求
        
        # 趋势过滤
        trend_filter = True
        if self.p.trend_filter:
            trend_filter = self.sma_fast[0] > self.sma_slow[0]
        
        # 检查是否持仓
        if not self.position:
            # 简化的买入条件
            buy_signal = False
            buy_reason = ""
            
            # 布林带下轨买入信号
            if current_price <= bb_lower and volume_filter and trend_filter:
                buy_signal = True
                buy_reason = f"布林带下轨买入 (价格: {current_price:.2f}, 下轨: {bb_lower:.2f})"
            
            if buy_signal:
                # 固定仓位，避免复杂的动态计算
                position_size = self.p.position_size
                
                # 计算买入数量（基于总资金）
                available_cash = self.broker.getcash()
                total_value = self.broker.getvalue()
                target_value = total_value * position_size
                
                if target_value <= available_cash:
                    shares = int(target_value / current_price)
                    if shares > 0:
                        self.log(f'买入信号: {buy_reason}, 买入股数: {shares}')
                        self.order = self.buy(size=shares)
                        self.last_trade_bar = current_bar
        
        else:
            # 持仓时的卖出逻辑
            sell_signal = False
            sell_reason = ""
            position_size = self.position.size
            
            # 固定止损
            if current_price < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                sell_reason = "固定止损"
            
            # 止盈
            elif current_price > self.buyprice * (1 + self.p.take_profit):
                sell_signal = True
                sell_reason = "止盈"
            
            # 布林带上轨卖出
            elif current_price >= bb_upper:
                sell_signal = True
                sell_reason = f"布林带上轨卖出 (价格: {current_price:.2f}, 上轨: {bb_upper:.2f})"
            
            # 趋势转向卖出
            elif (self.p.trend_filter and 
                  self.sma_fast[0] < self.sma_slow[0]):
                sell_signal = True
                sell_reason = "趋势转向卖出"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar

class TurtleTradingStrategy(bt.Strategy):
    """优化的海龟交易策略"""
    
    params = (
        ('entry_period', 15),       # 入场突破周期 (缩短以提高敏感度)
        ('exit_period', 8),         # 出场突破周期 (缩短以更快止损)
        ('atr_period', 14),         # ATR周期 (标准周期)
        ('position_size', 0.25),    # 仓位大小 (增加到25%)
        ('risk_percent', 0.015),    # 风险百分比 (略微降低)
        ('min_volume_ratio', 1.1),  # 最小成交量比率
        ('trend_strength', 0.02),   # 趋势强度阈值
        ('pyramid_enable', True),   # 是否启用金字塔加仓
        ('max_pyramids', 2),        # 最大加仓次数
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
        
        # 趋势强度指标
        self.sma_short = bt.indicators.SMA(self.data.close, period=10)
        self.sma_long = bt.indicators.SMA(self.data.close, period=30)
        
        # 成交量指标
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=20)
        
        # 动量指标
        self.momentum = bt.indicators.Momentum(self.data.close, period=10)
        
        # 金字塔加仓跟踪（暂时禁用以简化策略）
        self.pyramid_count = 0
        self.last_entry_price = None
        
        # 交易控制
        self.last_trade_bar = -10
        self.cooldown_period = 5
        
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
        """简化的海龟交易策略逻辑"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        
        if self.order:
            return
        
        # 检查交易冷却期
        current_bar = len(self.data)
        if current_bar - self.last_trade_bar < self.cooldown_period:
            return
        
        # 获取当前价格和指标值
        current_price = self.data.close[0]
        current_high = self.data.high[0]
        current_low = self.data.low[0]
        current_volume = self.data.volume[0]
        
        # 突破水平
        entry_high = self.highest[0]
        entry_low = self.lowest[0]
        
        # 出场水平
        exit_high = self.exit_highest[0]
        exit_low = self.exit_lowest[0]
        
        # 简化的过滤条件（进一步降低要求）
        volume_filter = current_volume > self.volume_sma[0] * 0.8  # 进一步降低成交量要求
        trend_filter = True  # 暂时取消趋势过滤，先看看能否产生交易
        
        # 检查是否持仓
        if not self.position:
            # 简化的买入条件
            buy_signal = False
            buy_reason = ""
            
            # 突破前高（最简单的条件，无过滤）
            if current_high > entry_high:
                buy_signal = True
                buy_reason = f"突破买入 (价格: {current_price:.2f}, 突破高点: {entry_high:.2f})"
            
            if buy_signal:
                # 固定仓位计算
                position_size = self.p.position_size
                available_cash = self.broker.getcash()
                total_value = self.broker.getvalue()
                target_value = total_value * position_size
                
                if target_value <= available_cash:
                    shares = int(target_value / current_price)
                    if shares > 0:
                        self.log(f'买入信号: {buy_reason}, 买入股数: {shares}')
                        self.order = self.buy(size=shares)
                        self.last_trade_bar = current_bar
        
        else:
            # 持仓时的卖出逻辑
            sell_signal = False
            sell_reason = ""
            position_size = self.position.size
            
            # 海龟出场：突破低点
            if current_low < exit_low:
                sell_signal = True
                sell_reason = f"海龟出场 (价格: {current_price:.2f}, 突破低点: {exit_low:.2f})"
            
            # 简化的ATR止损
            elif self.atr[0] > 0:
                atr_stop = self.buyprice - 2.0 * self.atr[0]  # 固定2倍ATR止损
                if current_price < atr_stop:
                    sell_signal = True
                    sell_reason = f"ATR止损 (价格: {current_price:.2f}, 止损价: {atr_stop:.2f})"
            
            # 趋势转向出场
            elif not trend_filter:  # 趋势转为下降
                sell_signal = True
                sell_reason = "趋势转向出场"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar

class SignalLevelReverseStrategy(bt.Strategy):
    """优化的信号量等级反向策略（根据IC检验结果，信号量等级和5期收益率成反比）"""
    
    params = (
        ('signal_level_threshold', 4),  # 信号量等级阈值 (调整为4，平衡交易机会和信号质量)
        ('position_size', 0.25),        # 仓位大小 (增加到25%)
        ('stop_loss', 0.02),            # 止损比例 (收紧止损)
        ('take_profit', 0.04),          # 止盈比例 (降低止盈目标，更快获利)
        ('lookback_period', 5),         # 回看期数（对应5期收益率）
        ('min_volume_ratio', 0.8),      # 最小成交量比率 (降低成交量要求)
        ('trend_filter', False),         # 暂时关闭趋势过滤，增加交易机会
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
        
        # 趋势指标
        if self.p.trend_filter:
            self.sma_fast = bt.indicators.SMA(self.data.close, period=10)
            self.sma_slow = bt.indicators.SMA(self.data.close, period=20)
        
        # 成交量指标
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=20)
        
        # 交易控制
        self.last_trade_bar = -10  # 上次交易的bar数
        self.cooldown_period = 5   # 交易冷却期（5个bar）
        
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
        """优化的信号量等级反向策略逻辑"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 检查交易冷却期
        current_bar = len(self.data)
        if current_bar - self.last_trade_bar < self.cooldown_period:
            return
        
        # 获取当前价格和指标值
        current_price = self.data.close[0]
        current_signal_level = self.signal_level[0]
        current_returns_5 = self.returns_5[0]
        current_volume = self.data.volume[0]
        
        # 成交量过滤
        volume_filter = current_volume > self.volume_sma[0] * self.p.min_volume_ratio
        
        # 趋势过滤
        trend_filter = True
        if self.p.trend_filter:
            trend_filter = self.sma_fast[0] > self.sma_slow[0]
        
        # 检查是否持仓
        if not self.position:
            # 多种买入条件，增加交易机会
            buy_signal = False
            buy_reason = ""
            
            # 条件1：信号量等级低时买入（预期未来收益率高）
            if current_signal_level <= self.p.signal_level_threshold and volume_filter:
                buy_signal = True
                buy_reason = f"信号量等级低买入 (等级: {current_signal_level}, 阈值: {self.p.signal_level_threshold})"
            
            # 条件2：信号量等级突然下降时买入
            elif (current_signal_level < self.signal_level[-1] * 0.85 and 
                  current_signal_level <= 5 and volume_filter):
                buy_signal = True
                buy_reason = f"信号量等级突降买入 (当前: {current_signal_level}, 前值: {self.signal_level[-1]:.2f})"
            
            # 条件3：价格回调且信号量等级较低时买入
            elif (current_price < self.data.close[-1] * 0.998 and 
                  current_signal_level <= 4 and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"价格回调买入 (价格变化: {((current_price/self.data.close[-1])-1)*100:.2f}%, 信号量等级: {current_signal_level})"
            
            if buy_signal:
                # 计算买入数量
                position_size = self.p.position_size
                available_cash = self.broker.getcash()
                total_value = self.broker.getvalue()
                target_value = total_value * position_size
                
                if target_value <= available_cash:
                    shares = int(target_value / current_price)
                    if shares > 0:
                        self.log(f'买入信号: {buy_reason}, 买入股数: {shares}')
                        self.order = self.buy(size=shares)
                        self.last_trade_bar = current_bar
        
        else:
            # 持仓时的卖出逻辑
            sell_signal = False
            sell_reason = ""
            position_size = self.position.size
            
            # 止损
            if current_price < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                sell_reason = "止损"
            
            # 止盈
            elif current_price > self.buyprice * (1 + self.p.take_profit):
                sell_signal = True
                sell_reason = "止盈"
            
            # 信号量等级升高时卖出（预期未来收益率低）
            elif current_signal_level > self.p.signal_level_threshold * 1.2:
                sell_signal = True
                sell_reason = f"信号量等级升高 (当前: {current_signal_level}, 阈值: {self.p.signal_level_threshold * 1.2:.1f})"
            
            # 价格大幅上涨时卖出
            elif current_price > self.buyprice * 1.025:  # 上涨2.5%以上
                sell_signal = True
                sell_reason = f"价格大幅上涨 (涨幅: {((current_price/self.buyprice)-1)*100:.2f}%)"
            
            # 趋势转向卖出（暂时关闭）
            # elif (self.p.trend_filter and 
            #       self.sma_fast[0] < self.sma_slow[0]):
            #     sell_signal = True
            #     sell_reason = "趋势转向卖出"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar 