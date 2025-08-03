#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测结果分析模块
负责分析回测结果和生成可视化图表
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class BacktestAnalyzer:
    """回测结果分析器"""
    
    def __init__(self, output_dir='backtest_results'):
        """
        初始化分析器
        
        Parameters:
        output_dir: str, 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def print_results(self, cerebro, results, data_info):
        """打印回测结果"""
        print("\n" + "="*50)
        print("回测结果汇总")
        print("="*50)
        
        # 资金曲线
        final_value = cerebro.broker.getvalue()
        initial_value = 100000.0
        total_return = (final_value - initial_value) / initial_value
        
        print(f"初始资金: {initial_value:,.2f}")
        print(f"最终资金: {final_value:,.2f}")
        print(f"总收益率: {total_return:.2%}")
        
        # 分析器结果
        if hasattr(results.analyzers, 'sharpe'):
            sharpe = results.analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe.get('sharperatio', 0)
            if sharpe_ratio is not None:
                print(f"夏普比率: {sharpe_ratio:.3f}")
            else:
                print("夏普比率: 无法计算")
        
        if hasattr(results.analyzers, 'drawdown'):
            drawdown = results.analyzers.drawdown.get_analysis()
            max_dd = drawdown.get('max', {}).get('drawdown', 0)
            if max_dd is not None:
                print(f"最大回撤: {max_dd:.2%}")
            else:
                print("最大回撤: 无法计算")
        
        if hasattr(results.analyzers, 'returns'):
            returns = results.analyzers.returns.get_analysis()
            annual_return = returns.get('rnorm100', 0)
            if annual_return is not None:
                print(f"年化收益率: {annual_return:.2f}%")
            else:
                print("年化收益率: 无法计算")
        
        if hasattr(results.analyzers, 'trades'):
            trades = results.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            
            print(f"总交易次数: {total_trades}")
            print(f"盈利交易: {won_trades}")
            print(f"亏损交易: {lost_trades}")
            if total_trades > 0:
                print(f"胜率: {won_trades/total_trades:.2%}")
    
    def plot_results(self, cerebro, results, data_info, df):
        """绘制回测结果图表"""
        print("生成回测结果图表...")
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'信号量等级策略回测结果 ({data_info["resample_rule"]}粒度, 滞后{data_info["lag_minutes"]}分钟)', 
                    fontsize=16, fontweight='bold')
        
        # 1. 价格走势和交易点
        ax1 = axes[0, 0]
        # 绘制价格走势
        ax1.plot(df.index, df['Close'], label='收盘价', color='blue', alpha=0.7)
        ax1.set_title('价格走势')
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 信号量等级分布
        ax2 = axes[0, 1]
        ax2.hist(df['信号量_等级'], bins=20, alpha=0.7, color='blue', edgecolor='black')
        ax2.axvline(5.0, color='red', linestyle='--', label='信号阈值')
        ax2.set_title('信号量等级分布')
        ax2.set_xlabel('信号量等级')
        ax2.set_ylabel('频次')
        ax2.legend()
        
        # 3. 信号量等级时间序列
        ax3 = axes[1, 0]
        ax3.plot(df.index, df['信号量_等级'], label='信号量等级', color='green', alpha=0.7)
        ax3.axhline(5.0, color='red', linestyle='--', label='信号阈值')
        ax3.set_title('信号量等级时间序列')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('信号量等级')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 收益率分布
        ax4 = axes[1, 1]
        if hasattr(results.analyzers, 'trades'):
            trades = results.analyzers.trades.get_analysis()
            if 'pnl' in trades and len(trades['pnl']) > 0:
                pnls = trades['pnl']
                ax4.hist(pnls, bins=20, alpha=0.7, color='green', edgecolor='black')
                ax4.axvline(0, color='red', linestyle='--', label='盈亏平衡线')
                ax4.set_title('交易盈亏分布')
                ax4.set_xlabel('盈亏')
                ax4.set_ylabel('频次')
                ax4.legend()
            else:
                ax4.text(0.5, 0.5, '暂无交易数据', ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('交易盈亏分布')
        else:
            ax4.text(0.5, 0.5, '暂无交易数据', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('交易盈亏分布')
        
        plt.tight_layout()
        
        # 保存图表
        output_file = os.path.join(self.output_dir, 
                                  f'backtest_results_{data_info["resample_rule"]}_lag{data_info["lag_minutes"]}min.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存到: {output_file}")
    
    def save_optimization_results(self, results_df, data_info):
        """保存参数优化结果"""
        output_file = os.path.join(self.output_dir, 
                                  f'parameter_optimization_{data_info["resample_rule"]}_lag{data_info["lag_minutes"]}min.csv')
        results_df.to_csv(output_file, index=False)
        print(f"优化结果已保存到: {output_file}")
        
        return output_file 