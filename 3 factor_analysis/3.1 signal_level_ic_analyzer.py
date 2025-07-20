import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
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
        
    def load_data(self):
        """加载数据"""
        print("正在加载数据...")
        self.data = pd.read_excel(self.data_path)
        print(f"数据加载完成，形状: {self.data.shape}")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        return self.data
    
    def calculate_interval_ic(self, return_col, method='pearson'):
        """
        计算信号等级各区间的IC值
        
        Parameters:
        return_col: str, 收益率列名
        method: str, 相关系数计算方法
        
        Returns:
        dict: 包含不同区间的IC值
        """
        valid_data = self.data[['信号量_等级', return_col]].dropna()
        
        if len(valid_data) == 0:
            print(f"警告: 信号量_等级 和 {return_col} 之间没有有效数据")
            return {}
        
        # 定义区间
        negative_mask = (valid_data['信号量_等级'] >= 1) & (valid_data['信号量_等级'] <= 3)
        neutral_mask = (valid_data['信号量_等级'] >= 4) & (valid_data['信号量_等级'] <= 6)
        positive_mask = valid_data['信号量_等级'] > 6
        
        ic_results = {}
        
        # 计算消极情绪区间的IC
        negative_data = valid_data[negative_mask]
        if len(negative_data) > 10:
            if method == 'pearson':
                ic_results['消极情绪(1-3)'] = negative_data['信号量_等级'].corr(negative_data[return_col])
            elif method == 'spearman':
                ic_results['消极情绪(1-3)'] = negative_data['信号量_等级'].corr(negative_data[return_col], method='spearman')
        else:
            ic_results['消极情绪(1-3)'] = np.nan
        
        # 计算中性情绪区间的IC
        neutral_data = valid_data[neutral_mask]
        if len(neutral_data) > 10:
            if method == 'pearson':
                ic_results['中性情绪(4-6)'] = neutral_data['信号量_等级'].corr(neutral_data[return_col])
            elif method == 'spearman':
                ic_results['中性情绪(4-6)'] = neutral_data['信号量_等级'].corr(neutral_data[return_col], method='spearman')
        else:
            ic_results['中性情绪(4-6)'] = np.nan
        
        # 计算积极情绪区间的IC
        positive_data = valid_data[positive_mask]
        if len(positive_data) > 10:
            if method == 'pearson':
                ic_results['积极情绪(>6)'] = positive_data['信号量_等级'].corr(positive_data[return_col])
            elif method == 'spearman':
                ic_results['积极情绪(>6)'] = positive_data['信号量_等级'].corr(positive_data[return_col], method='spearman')
        else:
            ic_results['积极情绪(>6)'] = np.nan
        
        # 计算整体IC
        if method == 'pearson':
            ic_results['整体'] = valid_data['信号量_等级'].corr(valid_data[return_col])
        elif method == 'spearman':
            ic_results['整体'] = valid_data['信号量_等级'].corr(valid_data[return_col], method='spearman')
        
        return ic_results
    
    def analyze_signal_level(self):
        """分析信号等级因子"""
        print("开始分析信号等级因子...")
        
        returns = ['FutureReturn_1period', 'FutureReturn_5period']
        
        for return_col in returns:
            ic_results = self.calculate_interval_ic(return_col)
            for interval, ic in ic_results.items():
                self.ic_results[f"信号量_等级_{interval}_vs_{return_col}"] = ic
                print(f"信号量_等级_{interval} vs {return_col}: IC = {ic:.4f}")
        
        return self.ic_results
    
    def plot_interval_analysis(self):
        """绘制区间分析图表"""
        if not self.ic_results:
            print("请先运行 analyze_signal_level()")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('信号等级因子IC分析', fontsize=16, fontweight='bold')
        
        # 1. 区间IC对比图
        ax1 = axes[0, 0]
        intervals = ['消极情绪(1-3)', '中性情绪(4-6)', '积极情绪(>6)', '整体']
        ic_1period = []
        ic_5period = []
        
        for interval in intervals:
            ic_1 = self.ic_results.get(f'信号量_等级_{interval}_vs_FutureReturn_1period', np.nan)
            ic_5 = self.ic_results.get(f'信号量_等级_{interval}_vs_FutureReturn_5period', np.nan)
            ic_1period.append(ic_1)
            ic_5period.append(ic_5)
        
        x = np.arange(len(intervals))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, ic_1period, width, label='1期收益率', alpha=0.7, color='skyblue')
        bars2 = ax1.bar(x + width/2, ic_5period, width, label='5期收益率', alpha=0.7, color='lightcoral')
        ax1.set_title('不同情绪区间的IC值对比')
        ax1.set_xlabel('情绪区间')
        ax1.set_ylabel('IC值')
        ax1.set_xticks(x)
        ax1.set_xticklabels(intervals, rotation=45, ha='right')
        ax1.legend()
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if not np.isnan(height):
                    ax1.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height > 0 else -0.01),
                            f'{height:.3f}', ha='center', va='bottom' if height > 0 else 'top', fontsize=8)
        
        # 2. 信号等级分布
        ax2 = axes[0, 1]
        signal_counts = self.data['信号量_等级'].value_counts().sort_index()
        ax2.bar(signal_counts.index, signal_counts.values, color='lightgreen')
        ax2.set_title('信号等级分布')
        ax2.set_xlabel('信号等级')
        ax2.set_ylabel('频次')
        
        # 3. 各区间收益率分布
        ax3 = axes[1, 0]
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period']].dropna()
        
        negative_data = valid_data[(valid_data['信号量_等级'] >= 1) & (valid_data['信号量_等级'] <= 3)]
        neutral_data = valid_data[(valid_data['信号量_等级'] >= 4) & (valid_data['信号量_等级'] <= 6)]
        positive_data = valid_data[valid_data['信号量_等级'] > 6]
        
        all_data = [negative_data['FutureReturn_1period'], neutral_data['FutureReturn_1period'], 
                   positive_data['FutureReturn_1period']]
        labels = ['消极情绪', '中性情绪', '积极情绪']
        
        ax3.boxplot(all_data, labels=labels)
        ax3.set_title('不同情绪区间的收益率分布')
        ax3.set_ylabel('1期收益率')
        ax3.grid(True, alpha=0.3)
        
        # 4. 散点图（按区间着色）
        ax4 = axes[1, 1]
        negative_mask = (valid_data['信号量_等级'] >= 1) & (valid_data['信号量_等级'] <= 3)
        neutral_mask = (valid_data['信号量_等级'] >= 4) & (valid_data['信号量_等级'] <= 6)
        positive_mask = valid_data['信号量_等级'] > 6
        
        ax4.scatter(valid_data[negative_mask]['信号量_等级'], 
                   valid_data[negative_mask]['FutureReturn_1period'], 
                   alpha=0.6, s=20, color='red', label='消极情绪')
        ax4.scatter(valid_data[neutral_mask]['信号量_等级'], 
                   valid_data[neutral_mask]['FutureReturn_1period'], 
                   alpha=0.6, s=20, color='green', label='中性情绪')
        ax4.scatter(valid_data[positive_mask]['信号量_等级'], 
                   valid_data[positive_mask]['FutureReturn_1period'], 
                   alpha=0.6, s=20, color='blue', label='积极情绪')
        
        ax4.set_title('信号等级与收益率关系')
        ax4.set_xlabel('信号等级')
        ax4.set_ylabel('1期收益率')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('ic_analysis_plot/signal_level_ic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()  # 关闭图表，不显示
    
    def generate_report(self):
        """生成分析报告"""
        print("\n" + "="*50)
        print("信号等级因子IC分析报告")
        print("="*50)
        
        print(f"\n数据概览:")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        print(f"数据总行数: {len(self.data)}")
        print(f"信号等级分布:")
        print(self.data['信号量_等级'].value_counts().sort_index())
        
        print(f"\nIC分析结果:")
        for factor_return, ic in self.ic_results.items():
            print(f"{factor_return}: {ic:.4f}")
        
        print(f"\n建议:")
        best_ic = max(self.ic_results.values(), key=lambda x: abs(x) if not np.isnan(x) else 0)
        best_factor = [k for k, v in self.ic_results.items() if v == best_ic][0]
        print(f"最佳IC区间: {best_factor} (IC = {best_ic:.4f})")
        
        if abs(best_ic) > 0.1:
            print("该区间显示出较强的预测能力")
        elif abs(best_ic) > 0.05:
            print("该区间显示出中等预测能力")
        else:
            print("该区间预测能力较弱，建议进一步优化")

def main():
    """主函数"""
    analyzer = SignalLevelICAnalyzer('futures_emo_combined_data/sc2210_with_emotion_lag15min.xlsx')
    analyzer.load_data()
    analyzer.analyze_signal_level()
    analyzer.plot_interval_analysis()
    analyzer.generate_report()

if __name__ == "__main__":
    main() 