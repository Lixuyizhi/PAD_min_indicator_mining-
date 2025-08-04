#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯布林带策略回测运行脚本
"""

import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
from datetime import datetime
import sys

# 导入自定义模块
from data_loader import DataLoader
from analyzer import BacktestAnalyzer
from bollinger_strategy import BollingerBandsStrategy

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class BollingerBacktestRunner:
    """布林带策略回测运行器"""
    
    def __init__(self, data_path, output_dir='bollinger_results'):
        """
        初始化回测运行器
        
        Parameters:
        data_path: str, 数据文件路径
        output_dir: str, 输出目录
        """
        self.data_path = data_path
        self.output_dir = output_dir
        self.data_loader = DataLoader(data_path)
        self.analyzer = BacktestAnalyzer(output_dir)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
    
    def run_backtest(self, strategy_params=None):
        """
        运行布林带策略回测
        
        Parameters:
        strategy_params: dict, 策略参数字典
        
        Returns:
        tuple: (cerebro, results, data_info)
        """
        # 默认策略参数
        default_params = {
            'boll_period': 20,
            'boll_dev': 2.0,
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'max_holding_periods': 10,
        }
        
        # 更新参数
        if strategy_params:
            default_params.update(strategy_params)
        
        print("="*60)
        print("纯布林带策略回测开始")
        print("="*60)
        print(f"数据文件: {self.data_path}")
        print(f"策略参数: {default_params}")
        
        # 创建Cerebro引擎
        cerebro = bt.Cerebro()
        
        # 设置初始资金
        cerebro.broker.setcash(100000.0)
        
        # 设置手续费
        cerebro.broker.setcommission(commission=0.001)
        
        # 加载数据
        data = self.data_loader.get_backtrader_data()
        cerebro.adddata(data)
        
        # 添加策略
        cerebro.addstrategy(BollingerBandsStrategy, **default_params)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 运行回测
        print("正在运行回测...")
        results = cerebro.run()
        
        # 获取数据信息
        data_info = self.data_loader.get_data_info()
        
        # 打印结果
        self.analyzer.print_results(cerebro, results[0], data_info)
        
        # 绘制结果
        df = self.data_loader.load_data()
        self.analyzer.plot_results(cerebro, results[0], data_info, df)
        
        # 保存参数配置
        self._save_parameters(default_params, data_info)
        
        print("="*60)
        print("回测完成")
        print("="*60)
        
        return cerebro, results[0], data_info
    
    def _save_parameters(self, params, data_info):
        """保存策略参数配置"""
        param_file = os.path.join(self.output_dir, 
                                 f'bollinger_params_{data_info["resample_rule"]}_lag{data_info["lag_minutes"]}min.txt')
        
        with open(param_file, 'w', encoding='utf-8') as f:
            f.write("布林带策略参数配置\n")
            f.write("="*30 + "\n")
            f.write(f"数据文件: {self.data_path}\n")
            f.write(f"数据粒度: {data_info['resample_rule']}\n")
            f.write(f"滞后时间: {data_info['lag_minutes']}分钟\n")
            f.write(f"参数配置时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in params.items():
                f.write(f"{key}: {value}\n")
        
        print(f"参数配置已保存到: {param_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='纯布林带策略回测')
    parser.add_argument('--data_path', type=str, 
                       default='../futures_emo_combined_data/sc2210_with_emotion_1h_lag120min.xlsx',
                       help='数据文件路径 (默认: ../futures_emo_combined_data/sc2210_with_emotion_1h_lag120min.xlsx)')
    parser.add_argument('--output_dir', type=str, default='bollinger_results',
                       help='输出目录')
    parser.add_argument('--boll_period', type=int, default=20,
                       help='布林带周期')
    parser.add_argument('--boll_dev', type=float, default=2.0,
                       help='布林带标准差倍数')
    parser.add_argument('--position_size', type=float, default=0.1,
                       help='仓位大小')
    parser.add_argument('--stop_loss', type=float, default=0.02,
                       help='止损比例')
    parser.add_argument('--take_profit', type=float, default=0.04,
                       help='止盈比例')
    parser.add_argument('--max_holding_periods', type=int, default=10,
                       help='最大持仓期数')
    
    args = parser.parse_args()
    
    # 检查数据文件是否存在
    if not os.path.exists(args.data_path):
        print(f"错误: 数据文件不存在: {args.data_path}")
        print("可用的数据文件:")
        data_dir = "../futures_emo_combined_data"
        if os.path.exists(data_dir):
            files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
            files.sort()  # 按文件名排序
            for file in files:
                print(f"  - {os.path.join(data_dir, file)}")
        else:
            print(f"数据目录不存在: {data_dir}")
        sys.exit(1)
    
    # 创建回测运行器
    runner = BollingerBacktestRunner(args.data_path, args.output_dir)
    
    # 设置策略参数
    strategy_params = {
        'boll_period': args.boll_period,
        'boll_dev': args.boll_dev,
        'position_size': args.position_size,
        'stop_loss': args.stop_loss,
        'take_profit': args.take_profit,
        'max_holding_periods': args.max_holding_periods,
    }
    
    # 运行回测
    runner.run_backtest(strategy_params)

if __name__ == '__main__':
    main() 