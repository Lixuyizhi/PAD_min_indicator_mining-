import backtrader as bt
import numpy as np
import pandas as pd

class EmotionSignalStrategy(bt.Strategy):
    """基于情绪信号的交易策略"""
    
    params = (
        ('signal_threshold', 0.5),  # 信号阈值
        ('position_size', 0.1),     # 仓位大小
        ('stop_loss', 0.02),        # 止损比例
        ('take_profit', 0.04),      # 止盈比例
        ('use_volume', True),       # 是否使用成交量
        ('use_emotion_level', True), # 是否使用情绪等级
    )
    
    def __init__(self):
        # 初始化指标
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 情绪指标 - 使用数组索引访问
        self.polarity = self.datas[0].极性
        self.intensity = self.datas[0].强度
        self.dominance = self.datas[0].支配维度
        self.signal_strength = self.datas[0].信号量
        self.signal_level = self.datas[0].信号量_等级
        
        # 技术指标
        self.sma_short = bt.indicators.SimpleMovingAverage(self.data.close, period=10)
        self.sma_long = bt.indicators.SimpleMovingAverage(self.data.close, period=30)
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        
        # 成交量指标
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=20)
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        
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
        
        self.log(f'交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
    
    def get_emotion_signal(self):
        """获取情绪信号"""
        # 综合情绪指标
        emotion_score = 0
        
        # 信号量权重最高
        if self.signal_strength[0] > self.p.signal_threshold:
            emotion_score += 2
        elif self.signal_strength[0] < -self.p.signal_threshold:
            emotion_score -= 2
        
        # 情绪等级
        if self.p.use_emotion_level:
            if self.signal_level[0] >= 6:
                emotion_score += 1
            elif self.signal_level[0] <= 3:
                emotion_score -= 1
        
        # 极性
        if self.polarity[0] > 0:
            emotion_score += 0.5
        elif self.polarity[0] < 0:
            emotion_score -= 0.5
        
        # 强度
        if self.intensity[0] > 50:
            emotion_score += 0.5
        
        return emotion_score
    
    def get_technical_signal(self):
        """获取技术分析信号"""
        tech_score = 0
        
        # 均线交叉
        if self.crossover > 0:  # 金叉
            tech_score += 1
        elif self.crossover < 0:  # 死叉
            tech_score -= 1
        
        # RSI
        if self.rsi[0] < 30:  # 超卖
            tech_score += 0.5
        elif self.rsi[0] > 70:  # 超买
            tech_score -= 0.5
        
        # 成交量
        if self.p.use_volume and self.data.volume[0] > self.volume_sma[0] * 1.5:
            tech_score += 0.5
        
        return tech_score
    
    def next(self):
        """主要策略逻辑"""
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 检查是否持仓
        if not self.position:
            # 计算综合信号
            emotion_signal = self.get_emotion_signal()
            tech_signal = self.get_technical_signal()
            total_signal = emotion_signal + tech_signal
            
            # 买入条件
            if total_signal >= 2:  # 综合信号强度
                self.log(f'买入信号, 情绪信号: {emotion_signal:.2f}, 技术信号: {tech_signal:.2f}')
                self.order = self.buy(size=self.p.position_size)
        
        else:
            # 持仓时的卖出逻辑
            emotion_signal = self.get_emotion_signal()
            tech_signal = self.get_technical_signal()
            total_signal = emotion_signal + tech_signal
            
            # 卖出条件
            sell_signal = False
            
            # 止损
            if self.data.close[0] < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                self.log('止损卖出')
            
            # 止盈
            elif self.data.close[0] > self.buyprice * (1 + self.p.take_profit):
                sell_signal = True
                self.log('止盈卖出')
            
            # 信号反转
            elif total_signal <= -1:
                sell_signal = True
                self.log(f'信号反转卖出, 情绪信号: {emotion_signal:.2f}, 技术信号: {tech_signal:.2f}')
            
            if sell_signal:
                self.order = self.sell(size=self.p.position_size)

class EmotionMomentumStrategy(bt.Strategy):
    """基于情绪动量的策略"""
    
    params = (
        ('momentum_period', 20),    # 动量计算周期
        ('signal_period', 5),       # 信号平滑周期
        ('position_size', 0.1),     # 仓位大小
        ('stop_loss', 0.03),        # 止损比例
    )
    
    def __init__(self):
        self.order = None
        self.buyprice = None
        
        # 情绪动量指标
        self.emotion_momentum = bt.indicators.SimpleMovingAverage(
            self.datas[0].信号量, period=self.p.momentum_period
        )
        
        # 情绪信号平滑
        self.emotion_signal = bt.indicators.SimpleMovingAverage(
            self.datas[0].信号量, period=self.p.signal_period
        )
        
        # 价格动量
        self.price_momentum = bt.indicators.MomentumOscillator(
            self.data.close, period=self.p.momentum_period
        )
        
        # 成交量动量
        self.volume_momentum = bt.indicators.MomentumOscillator(
            self.data.volume, period=self.p.momentum_period
        )
    
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
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 买入条件：情绪动量和价格动量都为正
            if (self.emotion_momentum[0] > 0 and 
                self.price_momentum[0] > 0 and
                self.emotion_signal[0] > 0):
                
                self.log(f'买入信号, 情绪动量: {self.emotion_momentum[0]:.2f}, 价格动量: {self.price_momentum[0]:.2f}')
                self.order = self.buy(size=self.p.position_size)
        
        else:
            # 卖出条件
            sell_signal = False
            
            # 止损
            if self.data.close[0] < self.buyprice * (1 - self.p.stop_loss):
                sell_signal = True
                self.log('止损卖出')
            
            # 动量反转
            elif (self.emotion_momentum[0] < 0 or 
                  self.price_momentum[0] < 0):
                sell_signal = True
                self.log(f'动量反转卖出, 情绪动量: {self.emotion_momentum[0]:.2f}, 价格动量: {self.price_momentum[0]:.2f}')
            
            if sell_signal:
                self.order = self.sell(size=self.p.position_size) 