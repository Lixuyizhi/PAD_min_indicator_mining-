#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略参数测试脚本
测试不同的策略参数组合，展示交易效果
"""

from backtest_platform import BacktestPlatform
import pandas as pd

def test_aggressive_strategy():
    """测试激进策略"""
    print("="*60)
    print("测试激进策略")
    print("="*60)
    
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 激进策略参数
    aggressive_params = {
        'signal_threshold': 5.0,
        'position_size': 0.2,        # 更大仓位
        'stop_loss': 0.03,           # 更宽松止损
        'take_profit': 0.06,         # 更高止盈
        'max_holding_periods': 3,    # 更短持仓期
        'min_signal_strength': 0.3,  # 更宽松信号强度
        'trend_filter': False,
        'momentum_filter': False,
        'volatility_filter': False,
        'use_volume_filter': False
    }
    
    cerebro, results = platform.run_backtest(strategy_params=aggressive_params)
    print("激进策略测试完成！")

def test_conservative_strategy():
    """测试保守策略"""
    print("="*60)
    print("测试保守策略")
    print("="*60)
    
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 保守策略参数
    conservative_params = {
        'signal_threshold': 5.5,
        'position_size': 0.05,       # 更小仓位
        'stop_loss': 0.015,          # 更严格止损
        'take_profit': 0.03,         # 更低止盈
        'max_holding_periods': 8,    # 更长持仓期
        'min_signal_strength': 1.5,  # 更严格信号强度
        'trend_filter': True,
        'momentum_filter': True,
        'volatility_filter': True,
        'use_volume_filter': True
    }
    
    cerebro, results = platform.run_backtest(strategy_params=conservative_params)
    print("保守策略测试完成！")

def test_balanced_strategy():
    """测试平衡策略"""
    print("="*60)
    print("测试平衡策略")
    print("="*60)
    
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 平衡策略参数
    balanced_params = {
        'signal_threshold': 5.0,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04,
        'max_holding_periods': 5,
        'min_signal_strength': 0.8,
        'trend_filter': True,
        'momentum_filter': False,
        'volatility_filter': True,
        'use_volume_filter': True
    }
    
    cerebro, results = platform.run_backtest(strategy_params=balanced_params)
    print("平衡策略测试完成！")

def test_parameter_optimization():
    """测试参数优化"""
    print("="*60)
    print("测试参数优化")
    print("="*60)
    
    platform = BacktestPlatform(
        data_path='../futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
        output_dir='backtest_results'
    )
    
    # 自定义参数范围
    param_ranges = {
        'signal_threshold': [4.5, 5.0, 5.5],
        'position_size': [0.05, 0.1, 0.15],
        'stop_loss': [0.015, 0.02, 0.025],
        'take_profit': [0.03, 0.04, 0.05]
    }
    
    best_params, results_df = platform.optimize_parameters(param_ranges)
    print(f"参数优化完成！最佳参数: {best_params}")
    
    # 使用最佳参数运行回测
    print("\n使用最佳参数运行回测...")
    cerebro, results = platform.run_backtest(strategy_params=best_params)
    print("最佳参数回测完成！")

def main():
    """主函数"""
    print("开始多策略测试...")
    
    # 测试激进策略
    test_aggressive_strategy()
    
    # 测试保守策略
    test_conservative_strategy()
    
    # 测试平衡策略
    test_balanced_strategy()
    
    # 测试参数优化
    test_parameter_optimization()
    
    print("\n所有策略测试完成！")

if __name__ == "__main__":
    main() 