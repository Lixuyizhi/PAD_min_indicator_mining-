#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于backtrader的信号量等级因子回测平台
基于IC分析结果构建的回测系统 - 重构版本
"""

import backtrader as bt
import warnings
import argparse

# 导入解耦后的模块
from strategy import SignalLevelStrategy
from data_loader import DataLoader
from analyzer import BacktestAnalyzer
from optimizer import ParameterOptimizer

warnings.filterwarnings('ignore')

class BacktestPlatform:
    """回测平台主类"""
    
    def __init__(self, data_path, output_dir='backtest_results'):
        """
        初始化回测平台
        
        Parameters:
        data_path: str, 数据文件路径
        output_dir: str, 结果输出目录
        """
        self.data_path = data_path
        self.output_dir = output_dir
        
        # 初始化各个模块
        self.data_loader = DataLoader(data_path)
        self.analyzer = BacktestAnalyzer(output_dir)
        self.optimizer = ParameterOptimizer(self.data_loader, SignalLevelStrategy, self.analyzer)
        
        # 回测引擎
        self.cerebro = None
        self.results = None
    
    def run_backtest(self, strategy_params=None, initial_cash=100000.0, commission=0.001):
        """
        运行回测
        
        Parameters:
        strategy_params: dict, 策略参数
        initial_cash: float, 初始资金
        commission: float, 手续费率
        
        Returns:
        tuple: (cerebro, results)
        """
        print("\n" + "="*50)
        print("开始回测")
        print("="*50)
        
        # 创建Cerebro引擎
        self.cerebro = bt.Cerebro()
        
        # 添加数据源
        data = self.data_loader.get_backtrader_data()
        self.cerebro.adddata(data)
        
        # 设置初始资金和手续费
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        
        # 添加策略
        if strategy_params:
            self.cerebro.addstrategy(SignalLevelStrategy, **strategy_params)
        else:
            self.cerebro.addstrategy(SignalLevelStrategy)
        
        # 添加分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 运行回测
        print("运行回测...")
        self.results = self.cerebro.run()
        
        # 获取数据信息
        data_info = self.data_loader.get_data_info()
        df = self.data_loader.load_data()
        
        # 打印结果
        self.analyzer.print_results(self.cerebro, self.results[0], data_info)
        
        # 绘制图表
        self.analyzer.plot_results(self.cerebro, self.results[0], data_info, df)
        
        return self.cerebro, self.results
    
    def optimize_parameters(self, param_ranges=None, initial_cash=100000.0, commission=0.001):
        """
        参数优化
        
        Parameters:
        param_ranges: dict, 参数范围，如果为None则使用默认范围
        initial_cash: float, 初始资金
        commission: float, 手续费率
        
        Returns:
        tuple: (最佳参数, 优化结果DataFrame)
        """
        if param_ranges is None:
            param_ranges = self.optimizer.get_default_param_ranges()
        
        best_params, results_df = self.optimizer.optimize_parameters(
            param_ranges, initial_cash, commission
        )
        
        return best_params, results_df
    
    def run_optimized_backtest(self, param_ranges=None):
        """
        运行参数优化后的回测
        
        Parameters:
        param_ranges: dict, 参数范围
        
        Returns:
        tuple: (cerebro, results)
        """
        # 先进行参数优化
        best_params, _ = self.optimize_parameters(param_ranges)
        
        # 使用最佳参数运行回测
        print("\n使用最佳参数运行最终回测...")
        return self.run_backtest(best_params)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='信号量等级因子回测平台')
    parser.add_argument('--data_path', type=str, 
                       default='futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
                       help='数据文件路径')
    parser.add_argument('--optimize', action='store_true', help='是否进行参数优化')
    parser.add_argument('--extended_optimize', action='store_true', help='是否进行扩展参数优化')
    parser.add_argument('--output_dir', type=str, default='backtest_results', help='输出目录')
    
    args = parser.parse_args()
    
    # 创建回测平台
    platform = BacktestPlatform(args.data_path, args.output_dir)
    
    if args.extended_optimize:
        # 扩展参数优化
        param_ranges = platform.optimizer.get_extended_param_ranges()
        platform.run_optimized_backtest(param_ranges)
    elif args.optimize:
        # 标准参数优化
        platform.run_optimized_backtest()
    else:
        # 直接运行回测
        platform.run_backtest()

if __name__ == "__main__":
    main() 