#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪指标回测系统主程序
基于backtrader构建的期货情绪指标回测框架
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import EmotionDataLoader
from backtest_engine import EmotionBacktestEngine
from optimizer import ParameterOptimizer
from emotion_strategy import EmotionSignalStrategy, EmotionMomentumStrategy, SignalLevelStrategy

def run_backtest(data_file_path, strategy_type="signal_level", plot=True):
    """
    运行回测
    
    参数:
        data_file_path: 数据文件路径
        strategy_type: 策略类型 ('signal_level', 'signal', 'momentum')
        plot: 是否显示图表
    """
    print("=" * 60)
    print("情绪指标回测系统")
    print("=" * 60)
    print(f"数据文件: {data_file_path}")
    print(f"策略类型: {strategy_type}")
    print("-" * 60)
    
    # 创建回测引擎
    engine = EmotionBacktestEngine(initial_cash=100000, commission=0.001)
    
    # 根据策略类型设置参数
    if strategy_type == "signal_level":
        strategy_class = SignalLevelStrategy
        strategy_params = {
            'buy_level': 6,      # 买入等级阈值
            'sell_level': 3,     # 卖出等级阈值
            'position_size': 0.1, # 仓位大小
            'stop_loss': 0.02,   # 止损比例
            'take_profit': 0.04  # 止盈比例
        }
    elif strategy_type == "signal":
        strategy_class = EmotionSignalStrategy
        strategy_params = {
            'signal_threshold': 0.5,
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'use_volume': True,
            'use_emotion_level': True
        }
    elif strategy_type == "momentum":
        strategy_class = EmotionMomentumStrategy
        strategy_params = {
            'momentum_period': 20,
            'signal_period': 5,
            'position_size': 0.1,
            'stop_loss': 0.03
        }
    else:
        print(f"未知的策略类型: {strategy_type}")
        print("支持的策略类型: signal_level, signal, momentum")
        return None
    
    # 运行回测
    result = engine.run_backtest(data_file_path, strategy_class, strategy_params, plot=plot)
    
    return result

def run_optimization(data_file_path, strategy_type="signal_level"):
    """
    运行参数优化
    
    参数:
        data_file_path: 数据文件路径
        strategy_type: 策略类型 ('signal_level', 'signal', 'momentum')
    """
    print("=" * 60)
    print("参数优化")
    print("=" * 60)
    print(f"数据文件: {data_file_path}")
    print(f"策略类型: {strategy_type}")
    print("-" * 60)
    
    optimizer = ParameterOptimizer(initial_cash=100000, commission=0.001)
    
    if strategy_type == "signal_level":
        results = optimizer.optimize_signal_level_strategy(data_file_path)
    elif strategy_type == "signal":
        results = optimizer.optimize_emotion_signal_strategy(data_file_path)
    elif strategy_type == "momentum":
        results = optimizer.optimize_emotion_momentum_strategy(data_file_path)
    else:
        print(f"未知的策略类型: {strategy_type}")
        return None
    
    return results

def run_strategy_comparison(data_file_path):
    """
    运行策略对比
    
    参数:
        data_file_path: 数据文件路径
    """
    print("=" * 60)
    print("策略对比")
    print("=" * 60)
    print(f"数据文件: {data_file_path}")
    print("-" * 60)
    
    engine = EmotionBacktestEngine(initial_cash=100000, commission=0.001)
    
    # 信号量等级策略参数
    signal_level_params = {
        'buy_level': 6,
        'sell_level': 3,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04
    }
    
    # 情绪信号策略参数
    emotion_params = {
        'signal_threshold': 0.5,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04,
        'use_volume': True,
        'use_emotion_level': True
    }
    
    print("运行信号量等级策略...")
    signal_level_result = engine.run_backtest(data_file_path, SignalLevelStrategy, signal_level_params, plot=False)
    
    print("\n运行情绪信号策略...")
    emotion_result = engine.run_backtest(data_file_path, EmotionSignalStrategy, emotion_params, plot=False)
    
    # 对比结果
    print("\n" + "="*60)
    print("策略对比结果")
    print("="*60)
    
    if signal_level_result and emotion_result:
        print(f"{'指标':<15} {'信号量等级策略':<15} {'情绪信号策略':<15}")
        print("-" * 60)
        print("回测完成，详细结果请查看上方输出")
    
    return signal_level_result, emotion_result

def list_available_files():
    """列出可用的数据文件"""
    loader = EmotionDataLoader()
    files = loader.get_available_files()
    
    print("可用的数据文件:")
    print("=" * 50)
    
    for i, file in enumerate(files, 1):
        try:
            info = loader.get_file_info(file)
            print(f"{i:2d}. {file}")
            print(f"    数据形状: {info['shape']}")
            print(f"    时间范围: {info['date_range'][0].strftime('%Y-%m-%d')} 到 {info['date_range'][1].strftime('%Y-%m-%d')}")
            print()
        except Exception as e:
            print(f"{i:2d}. {file} (读取失败: {e})")
            print()
    
    return files

def main():
    """
    主函数 - 在这里直接指定数据文件路径和策略类型
    """
    
    # ==================== 配置区域 ====================
    # 在这里直接指定数据文件路径
    DATA_FILE_PATH = "sc2210_with_emotion_1h_lag120min.xlsx"  # 修改为您的数据文件路径
    
    # 在这里直接指定策略类型
    STRATEGY_TYPE = "signal_level"  # 可选: "signal_level", "signal", "momentum"
    
    # 在这里指定运行模式
    RUN_MODE = "backtest"  # 可选: "backtest", "optimize", "compare"
    
    # 是否显示图表
    SHOW_PLOT = True
    # ================================================
    
    # 检查数据文件是否存在
    loader = EmotionDataLoader()
    available_files = loader.get_available_files()
    
    if DATA_FILE_PATH not in available_files:
        print(f"错误: 数据文件 '{DATA_FILE_PATH}' 不存在")
        print("可用的数据文件:")
        for file in available_files:
            print(f"  {file}")
        return
    
    # 根据运行模式执行相应操作
    if RUN_MODE == "backtest":
        print("运行回测模式")
        result = run_backtest(DATA_FILE_PATH, STRATEGY_TYPE, SHOW_PLOT)
        
    elif RUN_MODE == "optimize":
        print("运行参数优化模式")
        results = run_optimization(DATA_FILE_PATH, STRATEGY_TYPE)
        
    elif RUN_MODE == "compare":
        print("运行策略对比模式")
        signal_level_result, emotion_result = run_strategy_comparison(DATA_FILE_PATH)
        
    else:
        print(f"未知的运行模式: {RUN_MODE}")
        print("支持的运行模式: backtest, optimize, compare")

if __name__ == "__main__":
    main() 