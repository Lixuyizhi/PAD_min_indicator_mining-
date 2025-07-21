import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import re
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class SignalLevelICAnalyzer:
    """
    信号等级因子IC分析器
    专门分析信号量_等级与未来收益率的相关性
    """
    
    def __init__(self, data_path):
        """
        初始化分析器
        
        Parameters:
        data_path: str, 数据文件路径
        """
        self.data_path = data_path
        self.data = None
        self.ic_results = {}
        # 自动从文件名提取粒度和滞后时间
        match = re.search(r'_([0-9a-zA-Z]+)_lag(\d+)min', data_path)
        if match:
            self.resample_rule = match.group(1)
            self.lag_minutes = match.group(2)
        else:
            self.resample_rule = 'unknown'
            self.lag_minutes = 'unknown'
        self.fig_prefix = f"ic_analysis_plot/signal_level_ic_{self.resample_rule}_lag{self.lag_minutes}min"
        
    def load_data(self):
        """加载数据"""
        print("正在加载数据...")
        self.data = pd.read_excel(self.data_path)
        print(f"数据加载完成，形状: {self.data.shape}")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        return self.data
    
    def calculate_global_ic(self, method='pearson'):
        """
        计算信号量_等级与未来收益率的全局IC值
        """
        results = {}
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        if method == 'pearson':
            ic_1 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_1period'])
            ic_5 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_5period'])
        elif method == 'spearman':
            ic_1 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_1period'], method='spearman')
            ic_5 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_5period'], method='spearman')
        else:
            raise ValueError('method must be "pearson" or "spearman"')
        results['信号量_等级_vs_FutureReturn_1period'] = ic_1
        results['信号量_等级_vs_FutureReturn_5period'] = ic_5
        self.ic_results = results
        print(f"信号量_等级_vs_FutureReturn_1period: {ic_1:.4f}")
        print(f"信号量_等级_vs_FutureReturn_5period: {ic_5:.4f}")
        return results

    def plot_global_relationship(self):
        """
        可视化信号量_等级与1期、5期收益率的关系
        """
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('信号量等级与未来收益率关系', fontsize=16, fontweight='bold')
        # 1. 信号量等级 vs 1期收益率
        ax1 = axes[0]
        ax1.scatter(valid_data['信号量_等级'], valid_data['FutureReturn_1period'], alpha=0.5, s=20, color='blue')
        ax1.set_title('信号量等级 vs 1期收益率')
        ax1.set_xlabel('信号量等级 (0-10)')
        ax1.set_ylabel('1期收益率')
        ax1.grid(True, alpha=0.3)
        # 添加趋势线
        z1 = np.polyfit(valid_data['信号量_等级'], valid_data['FutureReturn_1period'], 1)
        p1 = np.poly1d(z1)
        ax1.plot(valid_data['信号量_等级'], p1(valid_data['信号量_等级']), "r--", alpha=0.8, label='趋势线')
        ax1.legend()
        # 2. 信号量等级 vs 5期收益率
        ax2 = axes[1]
        ax2.scatter(valid_data['信号量_等级'], valid_data['FutureReturn_5period'], alpha=0.5, s=20, color='green')
        ax2.set_title('信号量等级 vs 5期收益率')
        ax2.set_xlabel('信号量等级 (0-10)')
        ax2.set_ylabel('5期收益率')
        ax2.grid(True, alpha=0.3)
        # 添加趋势线
        z5 = np.polyfit(valid_data['信号量_等级'], valid_data['FutureReturn_5period'], 1)
        p5 = np.poly1d(z5)
        ax2.plot(valid_data['信号量_等级'], p5(valid_data['信号量_等级']), "r--", alpha=0.8, label='趋势线')
        ax2.legend()
        plt.tight_layout()
        plt.savefig(f'{self.fig_prefix}.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_rolling_ic(self, window=100, method='pearson'):
        """
        绘制信号量等级与未来收益率的滚动IC变化曲线，并加均值线
        """
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        if valid_data.empty:
            print("无有效数据用于滚动IC分析！")
            return
        rolling_ic_1 = []
        rolling_ic_5 = []
        idx = []
        for i in range(window, len(valid_data)):
            window_data = valid_data.iloc[i-window:i]
            if method == 'pearson':
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'])
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'])
            elif method == 'spearman':
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'], method='spearman')
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'], method='spearman')
            else:
                raise ValueError('method must be "pearson" or "spearman"')
            rolling_ic_1.append(ic1)
            rolling_ic_5.append(ic5)
            idx.append(valid_data.iloc[i].name)
        # 计算均值
        mean_ic1 = np.mean(rolling_ic_1)
        mean_ic5 = np.mean(rolling_ic_5)
        # 绘图
        plt.figure(figsize=(12, 6))
        plt.plot(idx, rolling_ic_1, label='1期收益率滚动IC', color='blue')
        plt.plot(idx, rolling_ic_5, label='5期收益率滚动IC', color='green')
        plt.axhline(0, color='black', linestyle='--', alpha=0.5)
        plt.axhline(mean_ic1, color='blue', linestyle=':', alpha=0.8, label=f'1期IC均值: {mean_ic1:.4f}')
        plt.axhline(mean_ic5, color='green', linestyle=':', alpha=0.8, label=f'5期IC均值: {mean_ic5:.4f}')
        plt.title(f'信号量等级与未来收益率的滚动IC（窗口={window}）')
        plt.xlabel('样本序号')
        plt.ylabel('IC值')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'{self.fig_prefix}_rolling.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_rolling_ic_stability(self, window=100, method='pearson'):
        """
        绘制滚动IC的稳定性分析图表（均值、标准差、分布直方图）
        """
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        if valid_data.empty:
            print("无有效数据用于滚动IC分析！")
            return
        rolling_ic_1 = []
        rolling_ic_5 = []
        for i in range(window, len(valid_data)):
            window_data = valid_data.iloc[i-window:i]
            if method == 'pearson':
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'])
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'])
            elif method == 'spearman':
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'], method='spearman')
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'], method='spearman')
            else:
                raise ValueError('method must be "pearson" or "spearman"')
            rolling_ic_1.append(ic1)
            rolling_ic_5.append(ic5)
        # 画图
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f'滚动IC稳定性分析（窗口={window}）', fontsize=16, fontweight='bold')
        # 1. 1期收益率IC分布
        axes[0].hist(rolling_ic_1, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0].axvline(np.mean(rolling_ic_1), color='red', linestyle='--', label=f'均值: {np.mean(rolling_ic_1):.4f}')
        axes[0].axvline(np.mean(rolling_ic_1)+np.std(rolling_ic_1), color='green', linestyle=':', label=f'+1σ: {np.mean(rolling_ic_1)+np.std(rolling_ic_1):.4f}')
        axes[0].axvline(np.mean(rolling_ic_1)-np.std(rolling_ic_1), color='green', linestyle=':', label=f'-1σ: {np.mean(rolling_ic_1)-np.std(rolling_ic_1):.4f}')
        axes[0].set_title('1期收益率滚动IC分布')
        axes[0].set_xlabel('IC值')
        axes[0].set_ylabel('频次')
        axes[0].legend()
        # 2. 5期收益率IC分布
        axes[1].hist(rolling_ic_5, bins=30, color='lightcoral', edgecolor='black', alpha=0.7)
        axes[1].axvline(np.mean(rolling_ic_5), color='red', linestyle='--', label=f'均值: {np.mean(rolling_ic_5):.4f}')
        axes[1].axvline(np.mean(rolling_ic_5)+np.std(rolling_ic_5), color='green', linestyle=':', label=f'+1σ: {np.mean(rolling_ic_5)+np.std(rolling_ic_5):.4f}')
        axes[1].axvline(np.mean(rolling_ic_5)-np.std(rolling_ic_5), color='green', linestyle=':', label=f'-1σ: {np.mean(rolling_ic_5)-np.std(rolling_ic_5):.4f}')
        axes[1].set_title('5期收益率滚动IC分布')
        axes[1].set_xlabel('IC值')
        axes[1].set_ylabel('频次')
        axes[1].legend()
        plt.tight_layout()
        plt.savefig(f'{self.fig_prefix}_rolling_stability.png', dpi=300, bbox_inches='tight')
        plt.close()

    def generate_report(self):
        """生成分析报告"""
        print("\n" + "="*50)
        print("信号量等级IC分析报告")
        print("="*50)
        print(f"\n数据概览:")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        print(f"数据总行数: {len(self.data)}")
        print(f"信号量等级分布:")
        print(self.data['信号量_等级'].describe())
        print(f"\nIC分析结果:")
        for k, v in self.ic_results.items():
            print(f"{k}: {v:.4f}")
        best_ic = max(self.ic_results.values(), key=lambda x: abs(x) if not np.isnan(x) else 0)
        best_factor = [k for k, v in self.ic_results.items() if v == best_ic][0]
        print(f"\n最佳IC: {best_factor} (IC = {best_ic:.4f})")
        if abs(best_ic) > 0.1:
            print("该因子显示出较强的预测能力")
        elif abs(best_ic) > 0.05:
            print("该因子显示出中等预测能力")
        else:
            print("该因子预测能力较弱，建议进一步优化")

def main():
    """主函数"""
    analyzer = SignalLevelICAnalyzer('futures_emo_combined_data/sc2210_with_emotion_1min_lag5min.xlsx')
    analyzer.load_data()
    analyzer.calculate_global_ic()
    analyzer.plot_global_relationship()
    analyzer.plot_rolling_ic(window=10000)
    analyzer.plot_rolling_ic_stability(window=10000) # 新增调用
    analyzer.generate_report()

if __name__ == "__main__":
    main() 