#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪指标回测系统主程序
基于backtrader构建的期货情绪指标回测框架
"""

import sys
import os
import argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import EmotionDataLoader
from backtest_engine import EmotionBacktestEngine
from optimizer import ParameterOptimizer
from emotion_strategy import EmotionSignalStrategy, EmotionMomentumStrategy

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

def run_single_backtest(filename, strategy_type="signal", plot=True):
    """运行单次回测"""
    engine = EmotionBacktestEngine(initial_cash=100000, commission=0.001)
    
    if strategy_type == "signal":
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
        return None
    
    print(f"运行 {strategy_type} 策略回测...")
    result = engine.run_backtest(filename, strategy_class, strategy_params, plot=plot)
    
    return result

def run_optimization(filename, strategy_type="signal"):
    """运行参数优化"""
    optimizer = ParameterOptimizer(initial_cash=100000, commission=0.001)
    
    if strategy_type == "signal":
        results = optimizer.optimize_emotion_signal_strategy(filename)
    elif strategy_type == "momentum":
        results = optimizer.optimize_emotion_momentum_strategy(filename)
    else:
        print(f"未知的策略类型: {strategy_type}")
        return None
    
    return results

def run_comparison_backtest(filename):
    """运行对比回测"""
    engine = EmotionBacktestEngine(initial_cash=100000, commission=0.001)
    
    # 情绪信号策略参数
    signal_params = {
        'signal_threshold': 0.5,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04,
        'use_volume': True,
        'use_emotion_level': True
    }
    
    # 情绪动量策略参数
    momentum_params = {
        'momentum_period': 20,
        'signal_period': 5,
        'position_size': 0.1,
        'stop_loss': 0.03
    }
    
    print("运行情绪信号策略...")
    signal_result = engine.run_backtest(filename, EmotionSignalStrategy, signal_params, plot=False)
    
    print("\n运行情绪动量策略...")
    momentum_result = engine.run_backtest(filename, EmotionMomentumStrategy, momentum_params, plot=False)
    
    # 对比结果
    print("\n" + "="*60)
    print("策略对比结果")
    print("="*60)
    
    if signal_result and momentum_result:
        print(f"{'指标':<15} {'情绪信号策略':<15} {'情绪动量策略':<15}")
        print("-" * 60)
        
        # 这里可以添加更多的对比指标
        print("回测完成，详细结果请查看上方输出")
    
    return signal_result, momentum_result

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='情绪指标回测系统')
    parser.add_argument('--list', action='store_true', help='列出可用的数据文件')
    parser.add_argument('--file', type=str, help='指定数据文件名')
    parser.add_argument('--strategy', choices=['signal', 'momentum'], default='signal', 
                       help='选择策略类型 (signal/momentum)')
    parser.add_argument('--optimize', action='store_true', help='运行参数优化')
    parser.add_argument('--compare', action='store_true', help='运行策略对比')
    parser.add_argument('--no-plot', action='store_true', help='不显示图表')
    
    args = parser.parse_args()
    
    # 列出文件
    if args.list:
        list_available_files()
        return
    
    # 检查数据文件
    loader = EmotionDataLoader()
    files = loader.get_available_files()
    
    if not files:
        print("没有找到数据文件，请检查数据目录")
        return
    
    # 选择文件
    if args.file:
        if args.file not in files:
            print(f"文件 {args.file} 不存在")
            print("可用的文件:")
            for file in files[:10]:  # 只显示前10个
                print(f"  {file}")
            return
        filename = args.file
    else:
        # 使用第一个文件
        filename = files[0]
        print(f"使用默认文件: {filename}")
    
    # 运行相应的功能
    if args.optimize:
        print(f"开始参数优化: {filename}")
        results = run_optimization(filename, args.strategy)
        
    elif args.compare:
        print(f"开始策略对比: {filename}")
        run_comparison_backtest(filename)
        
    else:
        # 默认运行单次回测
        print(f"开始回测: {filename}")
        run_single_backtest(filename, args.strategy, not args.no_plot)

if __name__ == "__main__":
    # 如果没有命令行参数，显示帮助信息
    if len(sys.argv) == 1:
        print("情绪指标回测系统")
        print("=" * 50)
        print("使用方法:")
        print("  python main.py --list                    # 列出可用数据文件")
        print("  python main.py --file <文件名>           # 运行回测")
        print("  python main.py --file <文件名> --optimize # 运行参数优化")
        print("  python main.py --file <文件名> --compare  # 运行策略对比")
        print("  python main.py --strategy momentum       # 选择动量策略")
        print("  python main.py --no-plot                 # 不显示图表")
        print()
        print("示例:")
        print("  python main.py --list")
        print("  python main.py --file ag2212_with_emotion_30min_lag90min.xlsx")
        print("  python main.py --file ag2212_with_emotion_30min_lag90min.xlsx --optimize")
        print()
        
        # 显示可用文件
        list_available_files()
    else:
        main() 