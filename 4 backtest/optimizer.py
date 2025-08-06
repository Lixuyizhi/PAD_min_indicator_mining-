import backtrader as bt
import pandas as pd
import numpy as np
from itertools import product
import warnings
warnings.filterwarnings('ignore')

from data_loader import load_and_prepare_data
from emotion_strategy import BollingerBandsStrategy, TurtleTradingStrategy, SignalLevelReverseStrategy, SignalLevelTechnicalStrategy

class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self, initial_cash=100000, commission=0.001):
        self.initial_cash = initial_cash
        self.commission = commission
        self.results = []
        
    def optimize_strategy(self, filename, strategy_class, param_ranges, 
                         start_date=None, end_date=None):
        """优化策略参数"""
        print(f"开始参数优化: {strategy_class.__name__}")
        print(f"参数范围: {param_ranges}")
        print("-" * 50)
        
        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_ranges)
        total_combinations = len(param_combinations)
        
        print(f"总共需要测试 {total_combinations} 种参数组合")
        
        # 存储结果
        optimization_results = []
        
        for i, params in enumerate(param_combinations):
            print(f"测试参数组合 {i+1}/{total_combinations}: {params}")
            
            try:
                # 运行回测
                result = self._run_single_backtest(filename, strategy_class, params, 
                                                start_date, end_date)
                
                if result:
                    optimization_results.append({
                        'params': params,
                        'final_value': result['final_value'],
                        'total_return': result['total_return'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'max_drawdown': result['max_drawdown'],
                        'total_trades': result['total_trades'],
                        'win_rate': result['win_rate']
                    })
                    
            except Exception as e:
                print(f"参数组合 {params} 测试失败: {e}")
                continue
        
        # 排序结果
        optimization_results.sort(key=lambda x: x['total_return'], reverse=True)
        
        # 打印最佳结果
        self._print_optimization_results(optimization_results)
        
        return optimization_results
    
    def _generate_param_combinations(self, param_ranges):
        """生成参数组合"""
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        combinations = []
        for values in product(*param_values):
            combination = dict(zip(param_names, values))
            combinations.append(combination)
        
        return combinations
    
    def _run_single_backtest(self, filename, strategy_class, params, 
                           start_date=None, end_date=None):
        """运行单次回测"""
        # 设置cerebro
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=self.commission)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 加载数据
        df, data_feed = load_and_prepare_data(filename)
        cerebro.adddata(data_feed)
        
        # 添加策略
        cerebro.addstrategy(strategy_class, **params)
        
        # 运行回测
        results = cerebro.run()
        
        if not results:
            return None
        
        strat = results[0]
        
        # 获取结果
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - self.initial_cash) / self.initial_cash * 100
        
        # 获取分析器结果
        sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
        if sharpe is None:
            sharpe = 0
        
        drawdown = strat.analyzers.drawdown.get_analysis()
        max_dd = drawdown.get('max', {}).get('drawdown', 0)
        if max_dd is None:
            max_dd = 0
        
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get('total', {}).get('total', 0)
        
        # 计算胜率
        won_trades = trades.get('won', {}).get('total', 0)
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 如果是SignalLevelStrategy，使用策略内部的胜率统计
        if hasattr(strat, 'trade_count') and strat.trade_count > 0:
            win_rate = (strat.win_count / strat.trade_count * 100)
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'total_trades': total_trades,
            'win_rate': win_rate
        }
    
    def _print_optimization_results(self, results):
        """打印优化结果"""
        print("\n" + "="*80)
        print("参数优化结果 (按总收益率排序)")
        print("="*80)
        
        if not results:
            print("没有有效的优化结果")
            return
        
        # 打印前10个最佳结果
        for i, result in enumerate(results[:10]):
            print(f"\n排名 {i+1}:")
            print(f"参数: {result['params']}")
            print(f"总收益率: {result['total_return']:.2f}%")
            print(f"夏普比率: {result['sharpe_ratio']:.3f}")
            print(f"最大回撤: {result['max_drawdown']:.2f}%")
            print(f"总交易次数: {result['total_trades']}")
            print(f"胜率: {result['win_rate']:.2f}%")
        
        # 统计信息
        returns = [r['total_return'] for r in results]
        print(f"\n统计信息:")
        print(f"平均收益率: {np.mean(returns):.2f}%")
        print(f"收益率标准差: {np.std(returns):.2f}%")
        print(f"最高收益率: {max(returns):.2f}%")
        print(f"最低收益率: {min(returns):.2f}%")
    
    def optimize_bollinger_bands_strategy(self, filename, start_date=None, end_date=None):
        """优化布林带策略"""
        param_ranges = {
            'bb_period': [15, 20, 25, 30],       # 布林带周期
            'bb_dev': [1.5, 2.0, 2.5, 3.0],      # 布林带标准差倍数
            'position_size': [0.05, 0.1, 0.15, 0.2], # 仓位大小
            'stop_loss': [0.015, 0.02, 0.025, 0.03], # 止损比例
            'take_profit': [0.03, 0.04, 0.05, 0.06]  # 止盈比例
        }
        
        return self.optimize_strategy(filename, BollingerBandsStrategy, param_ranges, 
                                   start_date, end_date)
    
    def optimize_turtle_trading_strategy(self, filename, start_date=None, end_date=None):
        """优化海龟交易策略"""
        param_ranges = {
            'entry_period': [15, 20, 25, 30],     # 入场突破周期
            'exit_period': [8, 10, 12, 15],       # 出场突破周期
            'atr_period': [15, 20, 25, 30],       # ATR周期
            'position_size': [0.05, 0.1, 0.15, 0.2], # 仓位大小
            'risk_percent': [0.015, 0.02, 0.025, 0.03] # 风险百分比
        }
        
        return self.optimize_strategy(filename, TurtleTradingStrategy, param_ranges, 
                                   start_date, end_date)
    
    def optimize_signal_level_reverse_strategy(self, filename, start_date=None, end_date=None):
        """优化信号量等级反向策略"""
        param_ranges = {
            'signal_level_threshold': [5, 6, 7, 8],  # 信号量等级阈值
            'position_size': [0.05, 0.1, 0.15, 0.2], # 仓位大小
            'stop_loss': [0.015, 0.02, 0.025, 0.03], # 止损比例
            'take_profit': [0.03, 0.04, 0.05, 0.06], # 止盈比例
            'lookback_period': [3, 5, 7, 10]         # 回看期数
        }
        
        return self.optimize_strategy(filename, SignalLevelReverseStrategy, param_ranges, 
                                   start_date, end_date)
    
    def optimize_signal_level_technical_strategy(self, filename, start_date=None, end_date=None):
        """优化信号量等级技术策略"""
        param_ranges = {
            'signal_level_threshold': [2, 3, 4, 5],  # 信号量等级阈值
            'position_size': [0.1, 0.15, 0.2, 0.25], # 仓位大小
            'stop_loss': [0.015, 0.02, 0.025, 0.03], # 止损比例
            'take_profit': [0.03, 0.04, 0.05, 0.06], # 止盈比例
            'rsi_period': [10, 14, 20],               # RSI周期
            'rsi_oversold': [25, 30, 35],             # RSI超卖阈值
            'rsi_overbought': [65, 70, 75],           # RSI超买阈值
            'macd_fast': [10, 12, 14],                # MACD快线
            'macd_slow': [24, 26, 28],                # MACD慢线
            'macd_signal': [7, 9, 11],                # MACD信号线
            'bb_period': [15, 20, 25],                # 布林带周期
            'bb_dev': [1.8, 2.0, 2.2],               # 布林带标准差
            'volume_ratio': [1.0, 1.1, 1.2],         # 成交量比率
            'cooldown_period': [3, 5, 7]              # 交易冷却期
        }
        
        return self.optimize_strategy(filename, SignalLevelTechnicalStrategy, param_ranges, 
                                   start_date, end_date)

def run_optimization_example():
    """运行参数优化示例"""
    optimizer = ParameterOptimizer(initial_cash=100000, commission=0.001)
    
    # 获取可用文件
    from data_loader import EmotionDataLoader
    loader = EmotionDataLoader()
    files = loader.get_available_files()
    
    if not files:
        print("没有找到数据文件")
        return
    
    # 选择第一个文件进行优化
    test_file = files[0]
    print(f"使用文件: {test_file}")
    
    # 优化布林带策略
    print("\n优化布林带策略...")
    bollinger_results = optimizer.optimize_bollinger_bands_strategy(test_file)
    
    # 优化海龟交易策略
    print("\n优化海龟交易策略...")
    turtle_results = optimizer.optimize_turtle_trading_strategy(test_file)
    
    # 优化信号量等级反向策略
    print("\n优化信号量等级反向策略...")
    signal_reverse_results = optimizer.optimize_signal_level_reverse_strategy(test_file)
    
    # 优化信号量等级技术策略
    print("\n优化信号量等级技术策略...")
    signal_technical_results = optimizer.optimize_signal_level_technical_strategy(test_file)
    
    return bollinger_results, turtle_results, signal_reverse_results, signal_technical_results

if __name__ == "__main__":
    # 运行参数优化
    bollinger_results, turtle_results, signal_reverse_results, signal_technical_results = run_optimization_example() 