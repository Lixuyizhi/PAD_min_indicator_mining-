#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布林带策略（可选情绪过滤）
"""
import backtrader as bt

class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('boll_period', 20),
        ('boll_dev', 2.0),
        ('position_size', 0.1),
        ('stop_loss', 0.02),
        ('take_profit', 0.04),
        ('max_holding_periods', 10),
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.order = None
        self.entry_price = 0
        self.holding_periods = 0
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0
        self.boll = bt.indicators.BollingerBands(self.close, period=self.params.boll_period, devfactor=self.params.boll_dev)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}')
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/拒绝')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.trade_count += 1
        if trade.pnl > 0:
            self.win_count += 1
        self.total_pnl += trade.pnl
        self.log(f'交易完成: 盈亏={trade.pnl:.2f}, 总盈亏={self.total_pnl:.2f}')

    def next(self):
        if self.order:
            return
        # 持仓管理
        if self.position:
            self.holding_periods += 1
            current_price = self.close[0]
            if self.entry_price > 0:
                if self.position.size > 0:
                    loss_ratio = (self.entry_price - current_price) / self.entry_price
                    profit_ratio = (current_price - self.entry_price) / self.entry_price
                else:
                    loss_ratio = (current_price - self.entry_price) / self.entry_price
                    profit_ratio = (self.entry_price - current_price) / self.entry_price
                if (loss_ratio >= self.params.stop_loss or
                    profit_ratio >= self.params.take_profit or
                    self.holding_periods >= self.params.max_holding_periods):
                    self.close()
                    self.holding_periods = 0
                    self.entry_price = 0
                    return
        # 开仓逻辑
        else:
            # 多头：价格触及下轨
            if self.close[0] <= self.boll.lines.bot[0]:
                self.order = self.buy(size=self.params.position_size)
                self.entry_price = self.close[0]
                self.holding_periods = 0
                self.log(f'布林带下轨开多: close={self.close[0]:.2f}')
            # 空头：价格触及上轨
            elif self.close[0] >= self.boll.lines.top[0]:
                self.order = self.sell(size=self.params.position_size)
                self.entry_price = self.close[0]
                self.holding_periods = 0
                self.log(f'布林带上轨开空: close={self.close[0]:.2f}')

    def stop(self):
        print('==================================================')
        print('布林带策略回测结果统计')
        print('==================================================')
        print(f'总交易次数: {self.trade_count}')
        print(f'盈利交易次数: {self.win_count}')
        print(f'胜率: {self.win_count/self.trade_count*100:.2f}%' if self.trade_count > 0 else '胜率: 0%')
        print(f'总盈亏: {self.total_pnl:.2f}')