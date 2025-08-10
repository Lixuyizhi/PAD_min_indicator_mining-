import backtrader as bt
import numpy as np
import pandas as pd

class BollingerBandsStrategy(bt.Strategy):
    """简化的布林带策略 - 只使用布林带信号"""
    
    params = (
        ('bb_period', 20),          # 布林带周期 (标准20期)
        ('bb_dev', 2.0),            # 布林带标准差倍数 (标准2倍)
        ('position_size', 0.25),     # 仓位大小 (降低到25%，减少风险)
        ('stop_loss', 0.06),         # 止损比例 (提高到6%，给价格更多空间)
        ('take_profit', 0.10),       # 止盈比例 (提高到10%，增加盈利空间)
        ('cooldown_period', 8),      # 交易冷却期 (增加到8个bar，减少过度交易)
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
        
        # 交易控制
        self.last_trade_bar = -10  # 上次交易的bar数
        
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
        
        self.log(f'交易完成, 盈亏: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
        
        # 记录交易日期
        self.trade_dates.append(self.data.datetime.date(0))
    
    def next(self):
        """简化的布林带策略逻辑 - 只使用布林带信号"""
        # 记录资金变化
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 检查交易冷却期
        current_bar = len(self.data)
        if current_bar - self.last_trade_bar < self.p.cooldown_period:
            return
        
        # 获取当前价格和布林带值
        current_price = self.data.close[0]
        bb_upper = self.bb.lines.top[0]
        bb_lower = self.bb.lines.bot[0]
        bb_middle = self.bb.lines.mid[0]
        
        # 检查是否持仓
        if not self.position:
            # 优化的买入信号（更严格的布林带信号）
            buy_signal = False
            buy_reason = ""
            
            # 信号1: 布林带下轨买入 (主要信号) - 更严格的条件
            if (current_price <= bb_lower * 1.01 and  # 价格接近或跌破下轨
                current_price > bb_lower * 0.98):     # 但不能过度超卖
                buy_signal = True
                buy_reason = f"布林带下轨买入 (价格: {current_price:.2f}, 下轨: {bb_lower:.2f})"
            
            # 信号2: 价格回调到布林带中轨附近 - 更严格的条件
            elif (current_price <= bb_middle * 1.005 and current_price > bb_lower and 
                  current_price > bb_middle * 0.995 and
                  current_price > bb_lower * 1.01):  # 确保不是从下轨反弹
                buy_signal = True
                buy_reason = f"中轨回调买入 (价格: {current_price:.2f}, 中轨: {bb_middle:.2f})"
            
            # 信号3: 布林带突破买入 - 更严格的条件
            elif (current_price > bb_upper and 
                  current_price > bb_upper * 1.005):  # 确保有效突破
                buy_signal = True
                buy_reason = f"布林带突破买入 (价格: {current_price:.2f}, 上轨: {bb_upper:.2f})"
            
            # 信号4: 价格从下轨反弹确认 - 更严格的条件
            elif (current_price > bb_lower * 1.015 and current_price < bb_middle and 
                  current_price > bb_lower * 1.02):  # 从下轨反弹1.5%以上
                buy_signal = True
                buy_reason = f"下轨反弹买入 (价格: {current_price:.2f}, 下轨: {bb_lower:.2f}, 中轨: {bb_middle:.2f})"
            
            # 新增信号5: 布林带收缩后扩张买入
            bb_width = bb_upper - bb_lower
            bb_width_ratio = bb_width / bb_middle
            if (bb_width_ratio < 0.05 and  # 布林带收缩（宽度小于5%）
                current_price > bb_middle and  # 价格在中轨之上
                current_price < bb_upper):     # 价格未突破上轨
                buy_signal = True
                buy_reason = f"布林带收缩买入 (价格: {current_price:.2f}, 宽度比: {bb_width_ratio:.3f})"
            
            if buy_signal:
                # 计算买入数量
                available_cash = self.broker.getcash()
                total_value = self.broker.getvalue()
                target_value = total_value * self.p.position_size
                
                if target_value <= available_cash:
                    shares = int(target_value / current_price)
                    if shares > 0:
                        self.log(f'{buy_reason}, 买入股数: {shares}')
                        self.order = self.buy(size=shares)
                        self.last_trade_bar = current_bar
        
        else:
            # 持仓时的卖出逻辑 - 优化后的卖出信号
            sell_signal = False
            sell_reason = ""
            position_size = self.position.size
            
            # 信号1: 固定止损 - 更宽松的止损
            if current_price < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                sell_reason = "固定止损"
            
            # 信号2: 止盈 - 更合理的止盈
            elif current_price > self.buyprice * (1 + self.p.take_profit):
                sell_signal = True
                sell_reason = "止盈"
            
            # 信号3: 布林带上轨卖出 - 更严格的条件
            elif (current_price >= bb_upper and 
                  current_price > bb_upper * 1.002):  # 确保有效触及上轨
                sell_signal = True
                sell_reason = f"布林带上轨卖出 (价格: {current_price:.2f}, 上轨: {bb_upper:.2f})"
            
            # 信号4: 价格跌破中轨 - 更严格的条件
            elif (current_price < bb_middle and 
                  current_price < bb_middle * 0.998):  # 确保有效跌破中轨
                sell_signal = True
                sell_reason = f"跌破中轨卖出 (价格: {current_price:.2f}, 中轨: {bb_middle:.2f})"
            
            # 新增信号5: 布林带过度扩张卖出
            bb_width = bb_upper - bb_lower
            bb_width_ratio = bb_width / bb_middle
            if (bb_width_ratio > 0.15 and  # 布林带过度扩张（宽度大于15%）
                current_price > bb_upper * 1.01):  # 价格突破上轨较多
                sell_signal = True
                sell_reason = f"布林带过度扩张卖出 (价格: {current_price:.2f}, 宽度比: {bb_width_ratio:.3f})"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar

class TurtleTradingStrategy(bt.Strategy):
    """纯粹的海龟交易策略 - 经典海龟交易法则"""
    
    params = (
        ('entry_period', 12),       # 唐奇安通道入场周期 (从20缩短到12，适应数据集)
        ('exit_period', 6),         # 唐奇安通道出场周期 (从10缩短到6)
        ('atr_period', 14),         # ATR周期 (从20缩短到14)
        ('position_size', 0.25),    # 仓位大小 (25%)
        ('atr_multiplier', 2.0),    # ATR倍数 (经典2倍)
        ('risk_percent', 0.02),     # 风险百分比 (2%)
    )
    
    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 经典海龟交易指标
        self.entry_high = bt.indicators.Highest(self.data.high, period=self.p.entry_period)  # 唐奇安通道上轨
        self.entry_low = bt.indicators.Lowest(self.data.low, period=self.p.entry_period)     # 唐奇安通道下轨
        self.exit_high = bt.indicators.Highest(self.data.high, period=self.p.exit_period)    # 出场通道上轨
        self.exit_low = bt.indicators.Lowest(self.data.low, period=self.p.exit_period)       # 出场通道下轨
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)                   # 平均真实波幅
        
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
        """纯粹的海龟交易策略逻辑"""
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
        
        # 突破水平
        entry_high = self.entry_high[0]
        entry_low = self.entry_low[0]
        
        # 出场水平
        exit_high = self.exit_high[0]
        exit_low = self.exit_low[0]
        
        # 检查是否持仓
        if not self.position:
            # 纯粹的海龟交易买入信号：唐奇安通道突破
            buy_signal = False
            buy_reason = ""
            
            # 信号1: 突破20期高点买入（经典海龟入场）
            if current_high > entry_high:
                buy_signal = True
                buy_reason = f"唐奇安通道突破买入 (价格: {current_price:.2f}, 突破高点: {entry_high:.2f})"
            
            if buy_signal:
                # 计算仓位大小（基于ATR的风险管理）
                if self.atr[0] > 0:
                    # 基于ATR的仓位计算（经典海龟方法）
                    risk_amount = self.broker.getvalue() * self.p.risk_percent
                    position_size = risk_amount / (self.p.atr_multiplier * self.atr[0])
                    shares = int(position_size)
                else:
                    # 固定仓位计算（备用方案）
                    position_size = self.p.position_size
                    available_cash = self.broker.getcash()
                    total_value = self.broker.getvalue()
                    target_value = total_value * position_size
                    shares = int(target_value / current_price)
                
                if shares > 0:
                    self.log(f'买入信号: {buy_reason}, 买入股数: {shares}')
                    self.order = self.buy(size=shares)
                    self.last_trade_bar = current_bar
        
        else:
            # 持仓时的卖出逻辑 - 纯粹的海龟出场规则
            sell_signal = False
            sell_reason = ""
            position_size = self.position.size
            
            # 信号1: 海龟出场：突破10期低点（经典海龟出场）
            if current_low < exit_low:
                sell_signal = True
                sell_reason = f"海龟出场 (价格: {current_price:.2f}, 突破低点: {exit_low:.2f})"
            
            # 信号2: ATR止损（经典海龟风险管理）
            elif self.atr[0] > 0:
                atr_stop = self.buyprice - self.p.atr_multiplier * self.atr[0]  # 2倍ATR止损
                if current_price < atr_stop:
                    sell_signal = True
                    sell_reason = f"ATR止损 (价格: {current_price:.2f}, 止损价: {atr_stop:.2f})"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar

class SignalLevelReverseStrategy(bt.Strategy):
    """简化的信号量等级反向策略（只考虑信号量等级，根据IC检验结果，信号量等级和5期收益率成反比）"""
    
    params = (
        ('signal_level_threshold', 3),  # 信号量等级阈值 (更严格，减少假信号)
        ('position_size', 0.12),        # 仓位大小 (降低到12%，减少风险)
        ('stop_loss', 0.02),            # 止损比例 (收紧到2%，减少大额亏损)
        ('take_profit', 0.06),          # 止盈比例 (提高到6%，增加盈利空间)
        ('lookback_period', 12),         # 回看期数 (增加到12期，更稳定)
        ('min_volume_ratio', 1.3),      # 最小成交量比率 (提高要求，确保流动性)
        ('trend_filter', True),          # 趋势过滤 (开启，避免逆势交易)
    )
    
    def __init__(self):
        # 初始化订单变量
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 情绪指标 - 只考虑信号量等级
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
        self.cooldown_period = 3   # 交易冷却期（减少到3个bar，大幅增加交易频率）
        
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
        """简化的信号量等级反向策略逻辑 - 只考虑信号量等级"""
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
            # 买入条件：低信号量等级买入（预期未来上涨）
            buy_signal = False
            buy_reason = ""
            
            # 条件1：低信号量等级买入 - 核心逻辑（IC检验显示信号量等级与未来收益率成反比）
            if (current_signal_level <= self.p.signal_level_threshold and  # 使用参数化的阈值
                volume_filter and 
                (not self.p.trend_filter or self.sma_fast[0] > self.sma_slow[0])):
                buy_signal = True
                buy_reason = f"低信号量等级买入 (信号量等级: {current_signal_level}, 阈值: {self.p.signal_level_threshold}, 预期未来上涨)"
            
            # 条件2：信号量等级突降买入（强化信号）
            elif (current_signal_level < self.signal_level[-1] * 0.8 and 
                  current_signal_level <= self.p.signal_level_threshold + 1 and volume_filter):
                buy_signal = True
                buy_reason = f"信号量等级突降买入 (当前: {current_signal_level}, 前值: {self.signal_level[-1]:.2f})"
            
            # 条件3：价格回调+低信号量等级买入
            elif (current_price < self.data.close[-1] * 0.998 and 
                  current_signal_level <= self.p.signal_level_threshold and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"价格回调+低信号量等级买入 (价格变化: {((current_price/self.data.close[-1])-1)*100:.2f}%, 信号量等级: {current_signal_level})"
            
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
            
            # 条件1：高信号量等级卖出（预期未来收益率低）
            elif current_signal_level >= 5:  # 信号量等级 ≥ 4 时卖出（预期未来下跌）
                sell_signal = True
                sell_reason = f"高信号量等级卖出 (当前: {current_signal_level}, 预期未来下跌)"
            
            # 条件2：信号量等级持续升高时卖出（强化卖出信号）
            elif (current_signal_level >= 4 and 
                  self.signal_level[-1] >= 4 and 
                  self.signal_level[-2] >= 4 ):
                sell_signal = True
                sell_reason = f"连续高信号量等级卖出 (当前: {current_signal_level}, 前1: {self.signal_level[-1]:.1f}, 前2: {self.signal_level[-2]:.2f})"
            
            # 条件3：价格大幅上涨时卖出
            elif current_price > self.buyprice * 1.05:  # 上涨5%以上
                sell_signal = True
                sell_reason = f"价格大幅上涨 (涨幅: {((current_price/self.buyprice)-1)*100:.2f}%)"
            
            # 条件4：信号量等级快速升高时卖出
            elif (current_signal_level > self.signal_level[-1] * 1.5 and 
                  current_signal_level >= 4):
                sell_signal = True
                sell_reason = f"信号量等级快速升高 (当前: {current_signal_level}, 前值: {self.signal_level[-1]:.2f})"
            
            # 趋势转向卖出（暂时关闭）
            # elif (self.p.trend_filter and 
            #       self.sma_fast[0] < self.sma_slow[0]):
            #     sell_signal = True
            #     sell_reason = "趋势转向卖出"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar 

class SignalLevelTechnicalStrategy(bt.Strategy):
    """信号量等级+技术指标综合策略"""
    
    params = (
        ('signal_level_threshold', 3),  # 信号量等级阈值
        ('position_size', 0.2),         # 仓位大小
        ('stop_loss', 0.02),            # 止损比例
        ('take_profit', 0.04),          # 止盈比例
        ('rsi_period', 14),             # RSI周期
        ('rsi_oversold', 30),           # RSI超卖阈值
        ('rsi_overbought', 70),         # RSI超买阈值
        ('macd_fast', 12),              # MACD快线
        ('macd_slow', 26),              # MACD慢线
        ('macd_signal', 9),             # MACD信号线
        ('bb_period', 20),              # 布林带周期
        ('bb_dev', 2.0),                # 布林带标准差
        ('volume_ratio', 1.1),          # 成交量比率
        ('cooldown_period', 5),         # 交易冷却期
    )
    
    def __init__(self):
        # 初始化订单变量
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 情绪指标
        self.signal_level = self.datas[0].信号量_等级
        self.polarity = self.datas[0].极性
        self.intensity = self.datas[0].强度
        
        # 技术指标
        # RSI指标
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        
        # MACD指标
        self.macd = bt.indicators.MACD(
            self.data.close, 
            period_me1=self.p.macd_fast, 
            period_me2=self.p.macd_slow, 
            period_signal=self.p.macd_signal
        )
        
        # 布林带指标
        self.bb = bt.indicators.BollingerBands(
            self.data.close, 
            period=self.p.bb_period, 
            devfactor=self.p.bb_dev
        )
        
        # 移动平均线
        self.sma_fast = bt.indicators.SMA(self.data.close, period=10)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=20)
        
        # 成交量指标
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=20)
        
        # 动量指标
        self.momentum = bt.indicators.Momentum(self.data.close, period=10)
        
        # 交易控制
        self.last_trade_bar = -10
        self.cooldown_period = self.p.cooldown_period
        
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
        """信号量等级+技术指标综合策略逻辑"""
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
        current_polarity = self.polarity[0]
        current_intensity = self.intensity[0]
        current_volume = self.data.volume[0]
        
        # 技术指标值
        current_rsi = self.rsi[0]
        current_macd = self.macd.macd[0]
        current_macd_signal = self.macd.signal[0]
        current_macd_hist = current_macd - current_macd_signal  # MACD直方图 = MACD线 - 信号线
        
        bb_upper = self.bb.lines.top[0]
        bb_lower = self.bb.lines.bot[0]
        bb_middle = self.bb.lines.mid[0]
        
        sma_fast_val = self.sma_fast[0]
        sma_slow_val = self.sma_slow[0]
        
        momentum_val = self.momentum[0]
        
        # 成交量过滤
        volume_filter = current_volume > self.volume_sma[0] * self.p.volume_ratio
        
        # 检查是否持仓
        if not self.position:
            # 多种买入条件组合
            buy_signal = False
            buy_reason = ""
            
            # 条件1：信号量等级低 + RSI超卖 + 布林带下轨
            if (current_signal_level <= self.p.signal_level_threshold and 
                current_rsi <= self.p.rsi_oversold and 
                current_price <= bb_lower and 
                volume_filter):
                buy_signal = True
                buy_reason = f"信号量低+RSI超卖+布林带下轨 (信号量: {current_signal_level}, RSI: {current_rsi:.1f})"
            
            # 条件2：信号量等级低 + MACD金叉 + 负面情绪
            elif (current_signal_level <= self.p.signal_level_threshold and 
                  current_macd > current_macd_signal and 
                  current_macd_hist > 0 and 
                  current_polarity <= -10 and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"信号量低+MACD金叉+负面情绪 (信号量: {current_signal_level}, MACD: {current_macd:.3f}, 极性: {current_polarity:.1f})"
            
            # 条件3：信号量等级突降 + 价格回调 + 动量反转
            elif (current_signal_level < self.signal_level[-1] * 0.8 and 
                  current_price < self.data.close[-1] * 0.995 and 
                  momentum_val > 0 and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"信号量突降+价格回调+动量反转 (信号量: {current_signal_level}, 动量: {momentum_val:.3f})"
            
            # 条件4：信号量等级低 + 均线支撑 + 高情绪强度
            elif (current_signal_level <= self.p.signal_level_threshold and 
                  current_price > sma_slow_val and 
                  current_intensity >= 15 and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"信号量低+均线支撑+高情绪强度 (信号量: {current_signal_level}, 强度: {current_intensity:.1f})"
            
            # 条件5：RSI超卖 + 布林带下轨 + 负面情绪
            elif (current_rsi <= self.p.rsi_oversold and 
                  current_price <= bb_lower and 
                  current_polarity <= -15 and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"RSI超卖+布林带下轨+负面情绪 (RSI: {current_rsi:.1f}, 极性: {current_polarity:.1f})"
            
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
            
            # 条件1：信号量等级升高 + RSI超买
            elif (current_signal_level > self.p.signal_level_threshold * 1.5 and 
                  current_rsi >= self.p.rsi_overbought):
                sell_signal = True
                sell_reason = f"信号量升高+RSI超买 (信号量: {current_signal_level}, RSI: {current_rsi:.1f})"
            
            # 条件2：信号量等级高 + MACD死叉
            elif (current_signal_level >= 5 and 
                  current_macd < current_macd_signal and 
                  current_macd_hist < 0):
                sell_signal = True
                sell_reason = f"信号量高+MACD死叉 (信号量: {current_signal_level}, MACD: {current_macd:.3f})"
            
            # 条件3：布林带上轨 + 正面情绪
            elif (current_price >= bb_upper and 
                  current_polarity >= 10):
                sell_signal = True
                sell_reason = f"布林带上轨+正面情绪 (极性: {current_polarity:.1f})"
            
            # 条件4：均线死叉 + 高信号量等级
            elif (sma_fast_val < sma_slow_val and 
                  current_signal_level >= 4):
                sell_signal = True
                sell_reason = f"均线死叉+高信号量 (信号量: {current_signal_level})"
            
            # 条件5：动量转负 + 高情绪强度
            elif (momentum_val < 0 and 
                  current_intensity >= 20):
                sell_signal = True
                sell_reason = f"动量转负+高情绪强度 (动量: {momentum_val:.3f}, 强度: {current_intensity:.1f})"
            
            if sell_signal:
                self.log(f'卖出信号: {sell_reason}')
                self.order = self.sell(size=abs(position_size))
                self.last_trade_bar = current_bar 