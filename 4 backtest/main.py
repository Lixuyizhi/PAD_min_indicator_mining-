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
from emotion_strategy import BollingerBandsStrategy, TurtleTradingStrategy, SignalLevelReverseStrategy
from analyst_visualize import BacktestAnalyzer, create_comparison_chart

def run_backtest(data_file_path, strategy_type="bollinger_bands", plot=True):
    """
    运行回测
    
    参数:
        data_file_path: 数据文件路径
        strategy_type: 策略类型 ('bollinger_bands', 'turtle_trading', 'signal_level_reverse')
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
    if strategy_type == "bollinger_bands":
        strategy_class = BollingerBandsStrategy
        strategy_params = {
            'bb_period': 20,        # 布林带周期
            'bb_dev': 2.0,          # 布林带标准差倍数
            'position_size': 0.1,   # 仓位大小
            'stop_loss': 0.02,      # 止损比例
            'take_profit': 0.04     # 止盈比例
        }
    elif strategy_type == "turtle_trading":
        strategy_class = TurtleTradingStrategy
        strategy_params = {
            'entry_period': 20,     # 入场突破周期
            'exit_period': 10,      # 出场突破周期
            'atr_period': 20,       # ATR周期
            'position_size': 0.1,   # 仓位大小
            'risk_percent': 0.02    # 风险百分比
        }
    elif strategy_type == "signal_level_reverse":
        strategy_class = SignalLevelReverseStrategy
        strategy_params = {
            'signal_level_threshold': 6,  # 信号量等级阈值
            'position_size': 0.1,         # 仓位大小
            'stop_loss': 0.02,            # 止损比例
            'take_profit': 0.04,          # 止盈比例
            'lookback_period': 5          # 回看期数
        }
    else:
        print(f"未知的策略类型: {strategy_type}")
        print("支持的策略类型: bollinger_bands, turtle_trading, signal_level_reverse")
        return None
    
    # 运行回测
    result = engine.run_backtest(data_file_path, strategy_class, strategy_params, plot=plot)
    
    return result

def run_optimization(data_file_path, strategy_type="bollinger_bands"):
    """
    运行参数优化
    
    参数:
        data_file_path: 数据文件路径
        strategy_type: 策略类型 ('bollinger_bands', 'turtle_trading', 'signal_level_reverse')
    """
    print("=" * 60)
    print("参数优化")
    print("=" * 60)
    print(f"数据文件: {data_file_path}")
    print(f"策略类型: {strategy_type}")
    print("-" * 60)
    
    optimizer = ParameterOptimizer(initial_cash=100000, commission=0.001)
    
    if strategy_type == "bollinger_bands":
        results = optimizer.optimize_bollinger_bands_strategy(data_file_path)
    elif strategy_type == "turtle_trading":
        results = optimizer.optimize_turtle_trading_strategy(data_file_path)
    elif strategy_type == "signal_level_reverse":
        results = optimizer.optimize_signal_level_reverse_strategy(data_file_path)
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
    analyzer = BacktestAnalyzer()
    
    # 布林带策略参数
    bollinger_params = {
        'bb_period': 20,
        'bb_dev': 2.0,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04
    }
    
    # 海龟交易策略参数
    turtle_params = {
        'entry_period': 20,
        'exit_period': 10,
        'atr_period': 20,
        'position_size': 0.1,
        'risk_percent': 0.02
    }
    
    # 信号量等级反向策略参数
    signal_reverse_params = {
        'signal_level_threshold': 6,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04,
        'lookback_period': 5
    }
    
    print("运行布林带策略...")
    bollinger_result = engine.run_backtest(data_file_path, BollingerBandsStrategy, bollinger_params, plot=False)
    
    print("\n运行海龟交易策略...")
    turtle_result = engine.run_backtest(data_file_path, TurtleTradingStrategy, turtle_params, plot=False)
    
    print("\n运行信号量等级反向策略...")
    signal_reverse_result = engine.run_backtest(data_file_path, SignalLevelReverseStrategy, signal_reverse_params, plot=False)
    
    # 分析结果
    results = []
    strategy_names = []
    
    if bollinger_result:
        bollinger_analysis = analyzer.analyze_strategy_performance(bollinger_result)
        analyzer.print_analysis_report(bollinger_analysis, "布林带策略")
        results.append(bollinger_analysis)
        strategy_names.append("布林带策略")
    
    if turtle_result:
        turtle_analysis = analyzer.analyze_strategy_performance(turtle_result)
        analyzer.print_analysis_report(turtle_analysis, "海龟交易策略")
        results.append(turtle_analysis)
        strategy_names.append("海龟交易策略")
    
    if signal_reverse_result:
        signal_analysis = analyzer.analyze_strategy_performance(signal_reverse_result)
        analyzer.print_analysis_report(signal_analysis, "信号量反向策略")
        results.append(signal_analysis)
        strategy_names.append("信号量反向策略")
    
    # 创建对比图表
    if len(results) > 1:
        print("\n" + "="*60)
        print("创建策略对比图表...")
        print("="*60)
        create_comparison_chart(results, strategy_names)
    
    return bollinger_result, turtle_result, signal_reverse_result

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
    STRATEGY_TYPE = "bollinger_bands"  # 可选: "bollinger_bands", "turtle_trading", "signal_level_reverse"
    
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