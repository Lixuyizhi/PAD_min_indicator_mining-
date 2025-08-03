#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数优化模块
负责策略参数优化和网格搜索
"""

import pandas as pd
import backtrader as bt
from itertools import product

class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self, data_loader, strategy_class, analyzer):
        """
        初始化参数优化器
        
        Parameters:
        data_loader: DataLoader实例
        strategy_class: 策略类
        analyzer: BacktestAnalyzer实例
        """
        self.data_loader = data_loader
        self.strategy_class = strategy_class
        self.analyzer = analyzer
    
    def optimize_parameters(self, param_ranges, initial_cash=100000.0, commission=0.001):
        """
        参数优化主函数
        
        Parameters:
        param_ranges: dict, 参数范围字典
        initial_cash: float, 初始资金
        commission: float, 手续费率
        
        Returns:
        tuple: (最佳参数, 优化结果DataFrame)
        """
        print("\n" + "="*50)
        print("开始参数优化")
        print("="*50)
        
        # 计算总组合数
        total_combinations = 1
        for param_name, param_range in param_ranges.items():
            total_combinations *= len(param_range)
        
        print(f"总共需要测试 {total_combinations} 种参数组合")
        
        best_params = None
        best_sharpe = -999
        results_list = []
        
        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        for param_combination in product(*param_values):
            params = dict(zip(param_names, param_combination))
            
            print(f"测试参数: {params}")
            
            try:
                # 运行回测
                results = self._run_single_backtest(params, initial_cash, commission)
                
                # 获取夏普比率
                if hasattr(results[0].analyzers, 'sharpe'):
                    sharpe = results[0].analyzers.sharpe.get_analysis()
                    current_sharpe = sharpe.get('sharperatio', -999)
                else:
                    current_sharpe = -999
                
                # 记录结果
                result_info = {
                    'params': str(params),
                    'sharpe': current_sharpe,
                    'final_value': results[0].cerebro.broker.getvalue(),
                    'total_return': (results[0].cerebro.broker.getvalue() - initial_cash) / initial_cash
                }
                
                # 添加具体参数值
                for key, value in params.items():
                    result_info[f'param_{key}'] = value
                
                results_list.append(result_info)
                
                # 更新最佳参数
                if current_sharpe > best_sharpe:
                    best_sharpe = current_sharpe
                    best_params = params
                    print(f"发现更好的参数组合: {params}, 夏普比率: {current_sharpe:.3f}")
            
            except Exception as e:
                print(f"参数组合 {params} 测试失败: {e}")
                continue
        
        # 保存优化结果
        results_df = pd.DataFrame(results_list)
        data_info = self.data_loader.get_data_info()
        self.analyzer.save_optimization_results(results_df, data_info)
        
        print(f"\n参数优化完成!")
        print(f"最佳参数: {best_params}")
        print(f"最佳夏普比率: {best_sharpe:.3f}")
        
        return best_params, results_df
    
    def _run_single_backtest(self, strategy_params, initial_cash, commission):
        """运行单次回测"""
        # 创建Cerebro引擎
        cerebro = bt.Cerebro()
        
        # 添加数据源
        data = self.data_loader.get_backtrader_data()
        cerebro.adddata(data)
        
        # 设置初始资金和手续费
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=commission)
        
        # 添加策略
        cerebro.addstrategy(self.strategy_class, **strategy_params)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 运行回测
        results = cerebro.run()
        
        return results
    
    def get_default_param_ranges(self):
        """获取默认参数范围"""
        return {
            'signal_threshold': [4.5, 5.0, 5.5],
            'position_size': [0.05, 0.1, 0.15],
            'stop_loss': [0.015, 0.02, 0.025],
            'take_profit': [0.03, 0.04, 0.05]
        }
    
    def get_extended_param_ranges(self):
        """获取扩展参数范围（更细致的搜索）"""
        return {
            'signal_threshold': [4.0, 4.5, 5.0, 5.5, 6.0],
            'position_size': [0.03, 0.05, 0.08, 0.1, 0.12, 0.15],
            'stop_loss': [0.01, 0.015, 0.02, 0.025, 0.03],
            'take_profit': [0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
        } 