import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from data_loader import load_and_prepare_data, EmotionDataLoader
from emotion_strategy import EmotionSignalStrategy, EmotionMomentumStrategy

class EmotionBacktestEngine:
    """情绪指标回测引擎"""
    
    def __init__(self, initial_cash=100000, commission=0.001):
        self.initial_cash = initial_cash
        self.commission = commission
        self.cerebro = None
        self.results = None
        
    def setup_cerebro(self):
        """设置回测引擎"""
        self.cerebro = bt.Cerebro()
        
        # 设置初始资金
        self.cerebro.broker.setcash(self.initial_cash)
        
        # 设置手续费
        self.cerebro.broker.setcommission(commission=self.commission)
        
        # 设置滑点
        self.cerebro.broker.set_slippage_perc(0.001)
        
        # 添加分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
    def run_backtest(self, filename, strategy_class, strategy_params=None, 
                    start_date=None, end_date=None, plot=True):
        """运行回测"""
        print(f"开始回测: {filename}")
        print(f"策略: {strategy_class.__name__}")
        print(f"参数: {strategy_params}")
        print("-" * 50)
        
        # 设置引擎
        self.setup_cerebro()
        
        # 加载数据
        try:
            df, data_feed = load_and_prepare_data(filename)
            print(f"数据加载成功: {df.shape}")
            
            # 数据过滤
            if start_date:
                data_feed = self._filter_data_by_date(data_feed, start_date, end_date)
            
            # 添加数据
            self.cerebro.adddata(data_feed)
            
            # 添加策略
            if strategy_params:
                self.cerebro.addstrategy(strategy_class, **strategy_params)
            else:
                self.cerebro.addstrategy(strategy_class)
            
            # 运行回测
            print("运行回测...")
            self.results = self.cerebro.run()
            
            # 获取结果
            strat = self.results[0]
            
            # 打印结果
            self._print_results(strat)
            
            # 绘制图表
            if plot:
                self._plot_results(strat, filename)
            
            return strat
            
        except Exception as e:
            print(f"回测失败: {e}")
            return None
    
    def _filter_data_by_date(self, data_feed, start_date, end_date):
        """按日期过滤数据"""
        # 这里需要根据backtrader的数据过滤机制来实现
        # 暂时返回原始数据
        return data_feed
    
    def _print_results(self, strat):
        """打印回测结果"""
        print("\n" + "="*50)
        print("回测结果")
        print("="*50)
        
        # 资金曲线
        final_value = self.cerebro.broker.getvalue()
        initial_value = self.initial_cash
        total_return = (final_value - initial_value) / initial_value * 100
        
        print(f"初始资金: {initial_value:,.2f}")
        print(f"最终资金: {final_value:,.2f}")
        print(f"总收益率: {total_return:.2f}%")
        
        # 分析器结果
        try:
            if hasattr(strat.analyzers, 'sharpe'):
                sharpe_ratio = strat.analyzers.sharpe.get_analysis()
                if 'sharperatio' in sharpe_ratio and sharpe_ratio['sharperatio'] is not None:
                    print(f"夏普比率: {sharpe_ratio['sharperatio']:.3f}")
        except:
            pass
        
        try:
            if hasattr(strat.analyzers, 'drawdown'):
                drawdown = strat.analyzers.drawdown.get_analysis()
                if 'max' in drawdown and 'drawdown' in drawdown['max']:
                    print(f"最大回撤: {drawdown['max']['drawdown']:.2f}%")
        except:
            pass
        
        try:
            if hasattr(strat.analyzers, 'returns'):
                returns = strat.analyzers.returns.get_analysis()
                if 'rtot' in returns and returns['rtot'] is not None:
                    print(f"年化收益率: {returns['rtot']:.2f}%")
        except:
            pass
        
        try:
            if hasattr(strat.analyzers, 'trades'):
                trades = strat.analyzers.trades.get_analysis()
                if 'total' in trades and 'total' in trades['total']:
                    print(f"总交易次数: {trades['total']['total']}")
                    if 'won' in trades and 'total' in trades['won']:
                        print(f"盈利交易: {trades['won']['total']}")
                    if 'lost' in trades and 'total' in trades['lost']:
                        print(f"亏损交易: {trades['lost']['total']}")
        except:
            pass
        
        print("="*50)
    
    def _plot_results(self, strat, filename):
        """绘制回测结果"""
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建图表
            fig, axes = plt.subplots(2, 1, figsize=(15, 10))
            
            # 绘制资金曲线
            self.cerebro.plot(style='candlestick', volume=False, 
                            numfigs=1, barup='red', bardown='green',
                            ax=axes[0])
            
            # 绘制情绪指标
            if hasattr(strat, 'signal_strength'):
                axes[1].plot(strat.signal_strength.array, label='信号量', color='blue')
            if hasattr(strat, 'polarity'):
                axes[1].plot(strat.polarity.array, label='极性', color='red', alpha=0.7)
            
            axes[1].set_title('情绪指标')
            axes[1].legend()
            axes[1].grid(True)
            
            plt.tight_layout()
            plt.savefig(f'backtest_results_{filename.replace(".xlsx", "")}.png', dpi=300, bbox_inches='tight')
            plt.show()
            
        except Exception as e:
            print(f"绘图失败: {e}")

def run_comparison_backtest():
    """运行对比回测"""
    engine = EmotionBacktestEngine(initial_cash=100000, commission=0.001)
    
    # 获取可用文件
    loader = EmotionDataLoader()
    files = loader.get_available_files()
    
    if not files:
        print("没有找到数据文件")
        return
    
    # 选择第一个文件进行测试
    test_file = files[0]
    print(f"使用文件: {test_file}")
    
    # 策略参数
    strategy_params = {
        'signal_threshold': 0.5,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.04,
        'use_volume': True,
        'use_emotion_level': True
    }
    
    # 运行情绪信号策略
    print("\n运行情绪信号策略...")
    emotion_results = engine.run_backtest(
        test_file, 
        EmotionSignalStrategy, 
        strategy_params,
        plot=True
    )
    
    # 运行情绪动量策略
    print("\n运行情绪动量策略...")
    momentum_params = {
        'momentum_period': 20,
        'signal_period': 5,
        'position_size': 0.1,
        'stop_loss': 0.03
    }
    
    momentum_results = engine.run_backtest(
        test_file,
        EmotionMomentumStrategy,
        momentum_params,
        plot=True
    )
    
    return emotion_results, momentum_results

if __name__ == "__main__":
    # 运行对比回测
    emotion_results, momentum_results = run_comparison_backtest() 