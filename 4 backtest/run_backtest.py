#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测运行示例脚本
展示如何使用解耦后的回测系统
"""

from backtest_platform import BacktestPlatform

def run_basic_backtest():
    """运行基础回测"""
    print("="*60)
    print("运行基础回测")
    print("="*60)
    
    # 创建回测平台
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 运行回测
    cerebro, results = platform.run_backtest()
    
    print("基础回测完成！")

def run_optimized_backtest():
    """运行参数优化回测"""
    print("="*60)
    print("运行参数优化回测")
    print("="*60)
    
    # 创建回测平台
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 运行参数优化回测
    cerebro, results = platform.run_optimized_backtest()
    
    print("参数优化回测完成！")

def run_custom_parameters_backtest():
    """运行自定义参数回测"""
    print("="*60)
    print("运行自定义参数回测")
    print("="*60)
    
    # 创建回测平台
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 自定义策略参数
    custom_params = {
        'signal_threshold': 5.5,  # 更高的信号阈值
        'position_size': 0.15,    # 更大的仓位
        'stop_loss': 0.025,       # 更宽松的止损
        'take_profit': 0.05,      # 更高的止盈
        'max_holding_periods': 3  # 更短的持仓期
    }
    
    # 运行回测
    cerebro, results = platform.run_backtest(strategy_params=custom_params)
    
    print("自定义参数回测完成！")

def run_parameter_optimization_only():
    """仅运行参数优化"""
    print("="*60)
    print("仅运行参数优化")
    print("="*60)
    
    # 创建回测平台
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 自定义参数范围
    custom_param_ranges = {
        'signal_threshold': [4.0, 4.5, 5.0, 5.5],
        'position_size': [0.05, 0.1, 0.15],
        'stop_loss': [0.015, 0.02, 0.025],
        'take_profit': [0.03, 0.04, 0.05]
    }
    
    # 运行参数优化
    best_params, results_df = platform.optimize_parameters(custom_param_ranges)
    
    print(f"参数优化完成！最佳参数: {best_params}")
    print(f"优化结果已保存到CSV文件")

if __name__ == "__main__":
    # 选择要运行的测试类型
    test_type = "basic"  # 可选: "basic", "optimized", "custom", "optimization_only"
    
    if test_type == "basic":
        run_basic_backtest()
    elif test_type == "optimized":
        run_optimized_backtest()
    elif test_type == "custom":
        run_custom_parameters_backtest()
    elif test_type == "optimization_only":
        run_parameter_optimization_only()
    else:
        print("未知的测试类型，运行基础回测...")
        run_basic_backtest() 