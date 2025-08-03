#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号量等级交易策略模块
基于IC分析结果构建的交易策略
"""

import backtrader as bt
import numpy as np

class SignalLevelStrategy(bt.Strategy):
    """
    基于信号量等级的交易策略
    根据IC分析结果，信号量等级与5期收益率有负相关关系
    """
    
    params = (
        ('signal_threshold', 5.0),  # 信号阈值，高于此值做空，低于此值做多
        ('position_size', 0.1),     # 仓位大小
        ('stop_loss', 0.02),        # 止损比例
        ('take_profit', 0.04),      # 止盈比例
        ('max_holding_periods', 5), # 最大持仓期数
        ('use_volume_filter', True), # 是否使用成交量过滤
        ('volume_threshold', 1.5),  # 成交量阈值倍数
    )
    
    def __init__(self):
        """初始化策略"""
        # 数据字段
        self.signal_level = self.datas[0].signal_level
        self.volume = self.datas[0].volume
        self.high = self.datas[0].high
        self.low = self.datas[0].low
        self.close = self.datas[0].close
        
        # 确保信号量等级数据可用
        if not hasattr(self.datas[0], 'signal_level'):
            raise ValueError("数据源缺少signal_level字段")
        
        print(f"策略初始化完成 - 信号阈值: {self.params.signal_threshold}")
        print(f"数据字段检查: signal_level={hasattr(self.datas[0], 'signal_level')}")
        
        # 策略状态
        self.order = None
        self.holding_periods = 0
        self.entry_price = 0
        self.entry_signal = 0
        
        # 统计指标
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0
        
        # 记录交易历史
        self.trade_history = []
        
        # 计算移动平均用于过滤
        self.sma_20 = bt.indicators.SimpleMovingAverage(self.close, period=20)
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.volume, period=20)
        
        print(f"策略初始化完成 - 信号阈值: {self.params.signal_threshold}")
    
    def log(self, txt, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 手续费={order.executed.comm:.2f}')
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 手续费={order.executed.comm:.2f}')
        
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
        
        self.total_pnl += trade.pnl
        
        # 记录交易历史
        trade_info = {
            'entry_date': bt.num2date(trade.dtopen),
            'exit_date': bt.num2date(trade.dtclose),
            'entry_price': trade.price,
            'exit_price': trade.pclose,
            'size': trade.size,
            'pnl': trade.pnl,
            'pnl_pct': trade.pnlcomm / trade.price if trade.price > 0 else 0,
            'signal_level': self.entry_signal
        }
        self.trade_history.append(trade_info)
        
        self.log(f'交易完成: 盈利={trade.pnl:.2f}, 盈利比例={trade.pnlcomm/trade.price:.2%}')
    
    def should_trade(self):
        """判断是否应该交易"""
        # 基本条件检查
        if not self.signal_level[0] or not self.close[0]:
            return False
        
        # 成交量过滤
        if self.params.use_volume_filter:
            if self.volume[0] < self.volume_sma[0] * self.params.volume_threshold:
                return False
        
        # 价格过滤 - 避免在极端价格时交易
        if self.close[0] < self.sma_20[0] * 0.95 or self.close[0] > self.sma_20[0] * 1.05:
            return False
        
        return True
    
    def get_signal(self):
        """获取交易信号"""
        signal_level = self.signal_level[0]
        
        # 基于IC分析结果：信号量等级与收益率负相关
        # 信号量等级高时做空，低时做多
        if signal_level > self.params.signal_threshold:
            return -1  # 做空信号
        elif signal_level < (10 - self.params.signal_threshold):  # 对称阈值
            return 1   # 做多信号
        else:
            return 0   # 无信号
    
    def next(self):
        """主要策略逻辑"""
        # 如果有未完成的订单，等待
        if self.order:
            return
        
        # 检查是否应该交易
        if not self.should_trade():
            return
        
        # 获取交易信号
        signal = self.get_signal()
        
        # 如果当前有持仓
        if self.position:
            self.holding_periods += 1
            
            # 检查止损止盈
            current_price = self.close[0]
            if self.entry_price > 0:  # 确保入场价格有效
                if self.position.size > 0:  # 多头持仓
                    loss_ratio = (self.entry_price - current_price) / self.entry_price
                    profit_ratio = (current_price - self.entry_price) / self.entry_price
                else:  # 空头持仓
                    loss_ratio = (current_price - self.entry_price) / self.entry_price
                    profit_ratio = (self.entry_price - current_price) / self.entry_price
            else:
                # 如果入场价格无效，重置持仓状态
                self.close()
                self.holding_periods = 0
                self.entry_price = 0
                self.entry_signal = 0
                return
            
            # 止损止盈或最大持仓期
            if (loss_ratio >= self.params.stop_loss or 
                profit_ratio >= self.params.take_profit or 
                self.holding_periods >= self.params.max_holding_periods):
                
                self.close()
                self.holding_periods = 0
                self.entry_price = 0
                self.entry_signal = 0
                return
        
        # 开新仓
        elif signal != 0:
            size = self.params.position_size
            if signal == 1:  # 做多
                self.order = self.buy(size=size)
                self.entry_price = self.close[0]
                self.entry_signal = self.signal_level[0]
                self.holding_periods = 0
                self.log(f'买入信号: 信号等级={self.signal_level[0]:.2f}, 价格={self.close[0]:.2f}')
            elif signal == -1:  # 做空
                self.order = self.sell(size=size)
                self.entry_price = self.close[0]
                self.entry_signal = self.signal_level[0]
                self.holding_periods = 0
                self.log(f'卖出信号: 信号等级={self.signal_level[0]:.2f}, 价格={self.close[0]:.2f}')
    
    def stop(self):
        """策略结束时的统计"""
        print('=' * 50)
        print('策略回测结果统计')
        print('=' * 50)
        print(f'总交易次数: {self.trade_count}')
        print(f'盈利交易次数: {self.win_count}')
        print(f'胜率: {self.win_count/self.trade_count:.2%}' if self.trade_count > 0 else '胜率: 0%')
        print(f'总盈亏: {self.total_pnl:.2f}')
        print(f'平均每笔盈亏: {self.total_pnl/self.trade_count:.2f}' if self.trade_count > 0 else '平均每笔盈亏: 0')
        
        # 计算更多统计指标
        if self.trade_history:
            pnls = [trade['pnl'] for trade in self.trade_history]
            pnl_pcts = [trade['pnl_pct'] for trade in self.trade_history]
            
            print(f'最大单笔盈利: {max(pnls):.2f}')
            print(f'最大单笔亏损: {min(pnls):.2f}')
            print(f'平均收益率: {np.mean(pnl_pcts):.2%}')
            print(f'收益率标准差: {np.std(pnl_pcts):.2%}')
            print(f'夏普比率: {np.mean(pnl_pcts)/np.std(pnl_pcts):.2f}' if np.std(pnl_pcts) > 0 else '夏普比率: 0') 