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
        ('signal_level_threshold', 1),  # 信号量等级阈值 (降低到1，更严格)
        ('position_size', 0.15),        # 仓位大小 (降低到15%，减少风险)
        ('stop_loss', 0.025),           # 止损比例 (放宽到2.5%，减少频繁止损)
        ('take_profit', 0.05),          # 止盈比例 (提高到5%，增加盈利空间)
        ('lookback_period', 10),         # 回看期数
        ('min_volume_ratio', 1.2),      # 最小成交量比率 (提高要求)
        ('trend_filter', False),         # 趋势过滤
        ('polarity_threshold', -15),     # 极性阈值 (更严格的负面情绪要求)
        ('intensity_threshold', 10),     # 强度阈值 (提高要求)
        ('dominance_threshold', -3),     # 支配维度阈值 (更严格)
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
        self.dominance = self.datas[0].支配维度
        
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
        self.cooldown_period = 8   # 交易冷却期（8个bar，大幅减少交易频率）
        
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
        current_polarity = self.polarity[0]
        current_intensity = self.intensity[0]
        current_dominance = self.dominance[0]
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
            
            # 条件1：综合情绪指标买入 - 负面情绪+低信号量等级
            if (current_polarity <= self.p.polarity_threshold and 
                current_signal_level <= self.p.signal_level_threshold and 
                volume_filter):
                buy_signal = True
                buy_reason = f"负面情绪+低信号量买入 (极性: {current_polarity:.1f}, 信号量等级: {current_signal_level})"
            
            # 条件2：高情绪强度+低信号量等级买入
            elif (current_intensity >= self.p.intensity_threshold and 
                  current_signal_level <= self.p.signal_level_threshold and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"高情绪强度+低信号量买入 (强度: {current_intensity:.1f}, 信号量等级: {current_signal_level})"
            
            # 条件3：低支配维度+低信号量等级买入
            elif (current_dominance <= self.p.dominance_threshold and 
                  current_signal_level <= self.p.signal_level_threshold and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"低支配维度+低信号量买入 (支配维度: {current_dominance:.1f}, 信号量等级: {current_signal_level})"
            
            # 条件4：信号量等级突降买入
            elif (current_signal_level < self.signal_level[-1] * 0.8 and 
                  current_signal_level <= 2 and volume_filter):
                buy_signal = True
                buy_reason = f"信号量等级突降买入 (当前: {current_signal_level}, 前值: {self.signal_level[-1]:.2f})"
            
            # 条件5：价格回调+负面情绪买入
            elif (current_price < self.data.close[-1] * 0.998 and 
                  current_polarity <= self.p.polarity_threshold and 
                  volume_filter):
                buy_signal = True
                buy_reason = f"价格回调+负面情绪买入 (价格变化: {((current_price/self.data.close[-1])-1)*100:.2f}%, 极性: {current_polarity:.1f})"
            
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
            
            # 条件1：信号量等级升高时卖出（预期未来收益率低）
            elif current_signal_level > 3:  # 信号量等级超过3时卖出
                sell_signal = True
                sell_reason = f"信号量等级升高 (当前: {current_signal_level}, 阈值: 3)"
            
            # 条件2：正面情绪+高信号量等级卖出
            elif (current_polarity > 10 and current_signal_level >= 4):
                sell_signal = True
                sell_reason = f"正面情绪+高信号量卖出 (极性: {current_polarity:.1f}, 信号量等级: {current_signal_level})"
            
            # 条件3：高情绪强度+高信号量等级卖出
            elif (current_intensity > 20 and current_signal_level >= 4):
                sell_signal = True
                sell_reason = f"高情绪强度+高信号量卖出 (强度: {current_intensity:.1f}, 信号量等级: {current_signal_level})"
            
            # 条件4：价格大幅上涨时卖出
            elif current_price > self.buyprice * 1.03:  # 上涨3%以上
                sell_signal = True
                sell_reason = f"价格大幅上涨 (涨幅: {((current_price/self.buyprice)-1)*100:.2f}%)"
            
            # 条件5：连续高信号量等级时卖出
            elif (current_signal_level >= 4 and 
                  self.signal_level[-1] >= 4 and 
                  self.signal_level[-2] >= 4):
                sell_signal = True
                sell_reason = f"连续高信号量等级卖出 (当前: {current_signal_level}, 前1: {self.signal_level[-1]:.1f}, 前2: {self.signal_level[-2]:.1f})"
            
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