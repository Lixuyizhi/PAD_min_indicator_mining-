#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测结果可视化分析模块
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

class BacktestVisualizer:
    """回测结果可视化器"""
    
    def __init__(self, initial_cash=100000):
        self.initial_cash = initial_cash
        
    def plot_backtest_results(self, strat, filename, show_trades=True, max_trades_to_show=100):
        """绘制回测结果
        参数:
            strat: 策略实例
            filename: 文件名
            show_trades: 是否显示交易点
            max_trades_to_show: 最大显示的交易点数
        """
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建子图布局
            fig = plt.figure(figsize=(20, 16))
            gs = fig.add_gridspec(4, 2, height_ratios=[2, 1, 1, 1], width_ratios=[3, 1])
            
            # 第一个子图：K线图和交易信号
            ax1 = fig.add_subplot(gs[0, 0])
            self._plot_candlestick_with_trades(strat, ax1, show_trades, max_trades_to_show)
            
            # 第二个子图：资金曲线
            ax2 = fig.add_subplot(gs[1, 0])
            self._plot_portfolio_value(strat, ax2)
            
            # 第三个子图：策略指标
            ax3 = fig.add_subplot(gs[2, 0])
            self._plot_strategy_indicators(strat, ax3)
            
            # 第四个子图：回撤曲线
            ax4 = fig.add_subplot(gs[3, 0])
            self._plot_drawdown(strat, ax4)
            
            # 右侧子图：统计信息
            ax5 = fig.add_subplot(gs[:, 1])
            self._plot_statistics(strat, ax5)
            
            plt.tight_layout()
            
            # 确保结果目录存在
            results_dir = 'backtest_results'
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            # 保存图表
            save_path = os.path.join(results_dir, f'backtest_results_{filename.replace(".xlsx", "")}.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存至: {save_path}")
            
            # 显示图表
            try:
                plt.show()
            except Exception as e:
                print(f"无法显示图表: {e}")
                print("图表已保存，您可以在文件系统中查看")
            
        except Exception as e:
            print(f"绘图失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _plot_candlestick_with_trades(self, strat, ax, show_trades=True, max_trades_to_show=100):
        """绘制K线图和交易点"""
        # 获取价格数据 - 使用更安全的backtrader数据访问方式
        try:
            # 尝试从数组中获取数据
            opens = strat.data.open.array
            highs = strat.data.high.array
            lows = strat.data.low.array
            closes = strat.data.close.array
            
            # 过滤掉无效数据 (NaN值)
            valid_mask = ~np.isnan(opens) & ~np.isnan(highs) & ~np.isnan(lows) & ~np.isnan(closes)
            
            opens = opens[valid_mask]
            highs = highs[valid_mask]
            lows = lows[valid_mask]
            closes = closes[valid_mask]
            
            dates = list(range(len(opens)))
            
        except Exception as e:
            print(f"无法获取价格数据: {e}")
            # 创建简单的收盘价线图作为备选
            try:
                closes = []
                for i in range(min(len(strat.data), 100)):  # 限制最多100个数据点
                    try:
                        closes.append(strat.data.close[0-i])
                    except:
                        break
                if closes:
                    closes.reverse()  # 恢复时间顺序
                    dates = list(range(len(closes)))
                    ax.plot(dates, closes, label='收盘价', color='blue')
                    ax.set_title('价格走势')
                    ax.legend()
                return
            except:
                print("无法绘制价格数据")
                return
        
        # 绘制K线图（简化版本，避免过于密集）
        # 如果数据点太多，进行采样
        if len(dates) > 1000:
            step = len(dates) // 1000
            dates = dates[::step]
            opens = opens[::step]
            highs = highs[::step]
            lows = lows[::step]
            closes = closes[::step]
        
        # 绘制K线图
        for i in range(len(dates)):
            color = 'red' if closes[i] > opens[i] else 'green'
            ax.plot([i, i], [lows[i], highs[i]], color='black', linewidth=0.5)
            ax.plot([i, i], [opens[i], closes[i]], color=color, linewidth=2)
        
        # 添加策略指标线
        if hasattr(strat, 'bb'):
            # 布林带
            bb_dates = list(range(len(strat.bb.lines.mid.array)))
            if len(bb_dates) > 1000:
                step = len(bb_dates) // 1000
                bb_mid = strat.bb.lines.mid.array[::step]
                bb_top = strat.bb.lines.top.array[::step]
                bb_bot = strat.bb.lines.bot.array[::step]
            else:
                bb_mid = strat.bb.lines.mid.array
                bb_top = strat.bb.lines.top.array
                bb_bot = strat.bb.lines.bot.array
            
            ax.plot(bb_dates, bb_mid, color='blue', linewidth=1, alpha=0.7, label='布林带中轨')
            ax.plot(bb_dates, bb_top, color='red', linewidth=1, alpha=0.5, label='布林带上轨')
            ax.plot(bb_dates, bb_bot, color='green', linewidth=1, alpha=0.5, label='布林带下轨')
        
        elif hasattr(strat, 'highest'):
            # 海龟交易指标
            highest_dates = list(range(len(strat.highest.array)))
            if len(highest_dates) > 1000:
                step = len(highest_dates) // 1000
                highest_dates = highest_dates[::step]
                highest = strat.highest.array[::step]
                lowest = strat.lowest.array[::step]
            else:
                highest = strat.highest.array
                lowest = strat.lowest.array
            
            ax.plot(highest_dates, highest, color='red', linewidth=1, alpha=0.7, label='20日高点')
            ax.plot(highest_dates, lowest, color='green', linewidth=1, alpha=0.7, label='20日低点')
        
        # 绘制交易点（简化）
        if show_trades and hasattr(strat, 'trade_count') and strat.trade_count > 0:
            # 显示交易统计信息
            ax.text(0.02, 0.98, f'交易次数: {strat.trade_count}\n胜率: {strat.win_count/strat.trade_count*100:.1f}%', 
                   transform=ax.transAxes, fontsize=10, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        
        ax.set_title('K线图和策略指标', fontsize=14, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('价格')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_portfolio_value(self, strat, ax):
        """绘制资金曲线"""
        # 使用策略中记录的资金数据
        if hasattr(strat, 'portfolio_values') and strat.portfolio_values:
            portfolio_values = strat.portfolio_values
            dates = list(range(len(portfolio_values)))
            
            # 绘制资金曲线
            ax.plot(dates, portfolio_values, color='blue', linewidth=2, label='总资产')
            
            # 添加基准线
            ax.axhline(y=self.initial_cash, color='red', linestyle='--', alpha=0.7, label='初始资金')
            
            # 计算收益率
            if len(portfolio_values) > 0:
                final_value = portfolio_values[-1]
                total_return = (final_value - self.initial_cash) / self.initial_cash * 100
                ax.text(0.02, 0.98, f'总收益率: {total_return:.2f}%', 
                       transform=ax.transAxes, fontsize=10, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        else:
            # 如果没有记录资金数据，使用简化的方法
            initial_value = self.initial_cash
            portfolio_values = [initial_value] * len(strat.data)
            dates = list(range(len(portfolio_values)))
            ax.plot(dates, portfolio_values, color='blue', linewidth=2, label='总资产')
            ax.axhline(y=self.initial_cash, color='red', linestyle='--', alpha=0.7, label='初始资金')
        
        ax.set_title('资金曲线', fontsize=14, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('资金')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_strategy_indicators(self, strat, ax):
        """绘制策略指标"""
        if hasattr(strat, 'bb'):
            # 布林带策略
            dates = list(range(len(strat.data)))
            ax.plot(dates, strat.bb.lines.mid.array, label='布林带中轨', color='blue', linewidth=2)
            ax.plot(dates, strat.bb.lines.top.array, label='布林带上轨', color='red', alpha=0.7)
            ax.plot(dates, strat.bb.lines.bot.array, label='布林带下轨', color='green', alpha=0.7)
            ax.set_title('布林带指标', fontsize=14, fontweight='bold')
            
        elif hasattr(strat, 'highest'):
            # 海龟交易策略
            dates = list(range(len(strat.data)))
            ax.plot(dates, strat.highest.array, label='20日高点', color='red', alpha=0.7)
            ax.plot(dates, strat.lowest.array, label='20日低点', color='green', alpha=0.7)
            if hasattr(strat, 'atr'):
                ax.plot(dates, strat.atr.array, label='ATR', color='orange', alpha=0.7)
            ax.set_title('海龟交易指标', fontsize=14, fontweight='bold')
            
        elif hasattr(strat, 'signal_level'):
            # 信号量等级反向策略
            dates = list(range(len(strat.data)))
            ax.plot(dates, strat.signal_level.array, label='信号量_等级', color='green', linewidth=2)
            if hasattr(strat, 'returns_5'):
                ax.plot(dates, strat.returns_5.array, label='5期收益率', color='blue', alpha=0.7)
            # 添加阈值线
            if hasattr(strat.p, 'signal_level_threshold'):
                ax.axhline(y=strat.p.signal_level_threshold, color='red', linestyle='--', alpha=0.7, label=f'信号量阈值({strat.p.signal_level_threshold})')
            ax.set_title('信号量等级指标', fontsize=14, fontweight='bold')
        
        ax.set_xlabel('时间')
        ax.set_ylabel('指标值')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_drawdown(self, strat, ax):
        """绘制回撤曲线"""
        # 使用策略中记录的资金数据计算回撤
        if hasattr(strat, 'portfolio_values') and strat.portfolio_values:
            portfolio_values = strat.portfolio_values
            
            # 计算回撤
            peak = portfolio_values[0]
            drawdown = []
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak * 100
                drawdown.append(dd)
            
            dates = list(range(len(drawdown)))
            
            # 绘制回撤曲线
            ax.fill_between(dates, drawdown, 0, color='red', alpha=0.3, label='回撤')
            ax.plot(dates, drawdown, color='red', linewidth=1)
            
            # 显示最大回撤
            max_dd = max(drawdown)
            ax.text(0.02, 0.98, f'最大回撤: {max_dd:.2f}%', 
                   transform=ax.transAxes, fontsize=10, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
        else:
            # 如果没有资金数据，使用分析器结果
            if hasattr(strat.analyzers, 'drawdown'):
                drawdown = strat.analyzers.drawdown.get_analysis()
                if 'drawdown' in drawdown:
                    dd_data = drawdown['drawdown']
                    dates = list(range(len(dd_data)))
                    ax.fill_between(dates, dd_data, 0, color='red', alpha=0.3, label='回撤')
                    ax.plot(dates, dd_data, color='red', linewidth=1)
        
        ax.set_title('回撤曲线', fontsize=14, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('回撤 (%)')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_statistics(self, strat, ax):
        """绘制统计信息"""
        ax.axis('off')
        
        # 获取回测结果
        final_value = strat.broker.getvalue()
        initial_value = self.initial_cash
        total_return = (final_value - initial_value) / initial_value * 100
        
        # 获取分析器结果
        sharpe = 0
        max_dd = 0
        total_trades = 0
        win_rate = 0
        
        try:
            if hasattr(strat.analyzers, 'sharpe'):
                sharpe_analysis = strat.analyzers.sharpe.get_analysis()
                sharpe = sharpe_analysis.get('sharperatio', 0) or 0
        except:
            pass
        
        try:
            if hasattr(strat.analyzers, 'drawdown'):
                drawdown = strat.analyzers.drawdown.get_analysis()
                max_dd = drawdown.get('max', {}).get('drawdown', 0) or 0
        except:
            pass
        
        try:
            if hasattr(strat.analyzers, 'trades'):
                trades = strat.analyzers.trades.get_analysis()
                total_trades = trades.get('total', {}).get('total', 0)
                won_trades = trades.get('won', {}).get('total', 0)
                win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
        except:
            pass
        
        # 如果是策略内部统计
        if hasattr(strat, 'trade_count') and strat.trade_count > 0:
            win_rate = (strat.win_count / strat.trade_count * 100)
        
        # 创建统计文本
        stats_text = f"""
回测统计结果

总收益率: {total_return:.2f}%
夏普比率: {sharpe:.3f}
最大回撤: {max_dd:.2f}%
总交易次数: {total_trades}
胜率: {win_rate:.1f}%
初始资金: {initial_value:,.0f}
最终资金: {final_value:,.0f}
        """
        
        ax.text(0.1, 0.9, stats_text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

class BacktestAnalyzer:
    """回测结果分析器"""
    
    def __init__(self):
        pass
    
    def analyze_strategy_performance(self, strat):
        """分析策略性能"""
        analysis = {}
        
        # 基本统计
        final_value = strat.broker.getvalue()
        initial_value = 100000  # 假设初始资金
        total_return = (final_value - initial_value) / initial_value * 100
        
        analysis['total_return'] = total_return
        analysis['final_value'] = final_value
        analysis['initial_value'] = initial_value
        
        # 交易统计
        if hasattr(strat, 'trade_count'):
            analysis['total_trades'] = strat.trade_count
            analysis['win_count'] = strat.win_count
            analysis['loss_count'] = strat.loss_count
            analysis['win_rate'] = (strat.win_count / strat.trade_count * 100) if strat.trade_count > 0 else 0
        
        # 分析器结果
        try:
            if hasattr(strat.analyzers, 'sharpe'):
                sharpe_analysis = strat.analyzers.sharpe.get_analysis()
                analysis['sharpe_ratio'] = sharpe_analysis.get('sharperatio', 0) or 0
        except:
            analysis['sharpe_ratio'] = 0
        
        try:
            if hasattr(strat.analyzers, 'drawdown'):
                drawdown = strat.analyzers.drawdown.get_analysis()
                analysis['max_drawdown'] = drawdown.get('max', {}).get('drawdown', 0) or 0
        except:
            analysis['max_drawdown'] = 0
        
        return analysis
    
    def print_analysis_report(self, analysis, strategy_name):
        """打印分析报告"""
        print(f"\n{'='*60}")
        print(f"{strategy_name} 分析报告")
        print(f"{'='*60}")
        print(f"总收益率: {analysis['total_return']:.2f}%")
        print(f"夏普比率: {analysis['sharpe_ratio']:.3f}")
        print(f"最大回撤: {analysis['max_drawdown']:.2f}%")
        print(f"总交易次数: {analysis.get('total_trades', 0)}")
        print(f"胜率: {analysis.get('win_rate', 0):.1f}%")
        print(f"初始资金: {analysis['initial_value']:,.0f}")
        print(f"最终资金: {analysis['final_value']:,.0f}")
        print(f"{'='*60}")

def create_comparison_chart(strategies_results, strategy_names):
    """创建策略对比图表"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 收益率对比
    returns = [result['total_return'] for result in strategies_results]
    axes[0, 0].bar(strategy_names, returns, color=['blue', 'green', 'red'])
    axes[0, 0].set_title('总收益率对比')
    axes[0, 0].set_ylabel('收益率 (%)')
    
    # 夏普比率对比
    sharpe_ratios = [result['sharpe_ratio'] for result in strategies_results]
    axes[0, 1].bar(strategy_names, sharpe_ratios, color=['blue', 'green', 'red'])
    axes[0, 1].set_title('夏普比率对比')
    axes[0, 1].set_ylabel('夏普比率')
    
    # 最大回撤对比
    max_drawdowns = [result['max_drawdown'] for result in strategies_results]
    axes[1, 0].bar(strategy_names, max_drawdowns, color=['blue', 'green', 'red'])
    axes[1, 0].set_title('最大回撤对比')
    axes[1, 0].set_ylabel('回撤 (%)')
    
    # 胜率对比
    win_rates = [result.get('win_rate', 0) for result in strategies_results]
    axes[1, 1].bar(strategy_names, win_rates, color=['blue', 'green', 'red'])
    axes[1, 1].set_title('胜率对比')
    axes[1, 1].set_ylabel('胜率 (%)')
    
    plt.tight_layout()
    
    # 保存对比图表
    results_dir = 'backtest_results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    save_path = os.path.join(results_dir, 'strategy_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"策略对比图表已保存至: {save_path}")
    
    try:
        plt.show()
    except Exception as e:
        print(f"无法显示对比图表: {e}")
    
    return fig 