#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布林带策略回测示例脚本
简单易用的回测运行示例
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_bollinger_backtest import BollingerBacktestRunner

def main():
    """主函数 - 运行布林带策略回测示例"""
    
    # 选择数据文件（您可以根据需要修改）
    # 这里选择15分钟粒度，滞后30分钟的数据作为示例
    data_path = "../futures_emo_combined_data/sc2210_with_emotion_15min_lag30min.xlsx"
    
    # 检查数据文件是否存在
    if not os.path.exists(data_path):
        print(f"错误：数据文件不存在: {data_path}")
        print("\n可用的数据文件:")
        data_dir = "../futures_emo_combined_data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.xlsx'):
                    print(f"  - {file}")
        return
    
    # 创建回测运行器
    runner = BollingerBacktestRunner(data_path, output_dir='bollinger_results')
    
    # 运行回测（使用默认参数）
    print("运行布林带策略回测（默认参数）...")
    cerebro, results, data_info = runner.run_backtest()
    
    # 运行参数优化（可选）
    print("\n" + "="*60)
    print("是否要运行参数优化？(y/n): ", end="")
    user_input = input().strip().lower()
    
    if user_input in ['y', 'yes', '是']:
        print("开始参数优化...")
        param_ranges = {
            'boll_period': [15, 20, 25],  # 减少参数组合以加快速度
            'boll_dev': [1.8, 2.0, 2.2],
            'position_size': [0.08, 0.1, 0.12],
            'stop_loss': [0.018, 0.02, 0.022],
            'take_profit': [0.035, 0.04, 0.045],
        }
        optimization_results = runner.run_parameter_optimization(param_ranges)
        
        # 使用最佳参数重新运行回测
        if not optimization_results.empty:
            best_idx = optimization_results['total_return'].idxmax()
            best_params = optimization_results.loc[best_idx]
            
            print("\n使用最佳参数重新运行回测...")
            best_strategy_params = {
                'boll_period': int(best_params['boll_period']),
                'boll_dev': best_params['boll_dev'],
                'position_size': best_params['position_size'],
                'stop_loss': best_params['stop_loss'],
                'take_profit': best_params['take_profit'],
                'max_holding_periods': 10,
            }
            runner.run_backtest(best_strategy_params)
    
    print("\n回测完成！结果已保存到 'bollinger_results' 目录")

if __name__ == '__main__':
    main() 