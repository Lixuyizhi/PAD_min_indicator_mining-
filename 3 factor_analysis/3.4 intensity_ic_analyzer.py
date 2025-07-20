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

class IntensityICAnalyzer:
    """
    强度因子IC分析器
    专门分析强度（Arousal）与未来收益率的相关性
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
    
    def calculate_ic(self, factor_col, return_col, method='pearson'):
        """
        计算IC值
        
        Parameters:
        factor_col: str, 因子列名
        return_col: str, 收益率列名
        method: str, 相关系数计算方法
        
        Returns:
        float: IC值
        """
        valid_data = self.data[[factor_col, return_col]].dropna()
        
        if len(valid_data) == 0:
            print(f"警告: {factor_col} 和 {return_col} 之间没有有效数据")
            return np.nan
        
        if method == 'pearson':
            ic = valid_data[factor_col].corr(valid_data[return_col])
        elif method == 'spearman':
            ic = valid_data[factor_col].corr(valid_data[return_col], method='spearman')
        else:
            raise ValueError("method must be 'pearson' or 'spearman'")
        
        return ic
    
    def calculate_rolling_ic(self, factor_col, return_col, window=50, method='pearson'):
        """
        计算滚动IC值
        
        Parameters:
        factor_col: str, 因子列名
        return_col: str, 收益率列名
        window: int, 滚动窗口大小
        method: str, 相关系数计算方法
        
        Returns:
        pd.Series: 滚动IC值
        """
        rolling_ic = []
        dates = []
        
        for i in range(window, len(self.data)):
            window_data = self.data.iloc[i-window:i]
            valid_data = window_data[[factor_col, return_col]].dropna()
            
            if len(valid_data) >= window * 0.8:
                if method == 'pearson':
                    ic = valid_data[factor_col].corr(valid_data[return_col])
                elif method == 'spearman':
                    ic = valid_data[factor_col].corr(valid_data[return_col], method='spearman')
                
                rolling_ic.append(ic)
                dates.append(self.data.iloc[i]['DateTime'])
            else:
                rolling_ic.append(np.nan)
                dates.append(self.data.iloc[i]['DateTime'])
        
        return pd.Series(rolling_ic, index=dates)
    
    def analyze_intensity(self):
        """分析强度因子"""
        print("开始分析强度因子...")
        
        returns = ['FutureReturn_1period', 'FutureReturn_5period']
        
        for return_col in returns:
            ic = self.calculate_ic('强度', return_col)
            self.ic_results[f"强度_vs_{return_col}"] = ic
            print(f"强度 vs {return_col}: IC = {ic:.4f}")
        
        return self.ic_results
    
    def plot_intensity_analysis(self):
        """绘制强度分析图表"""
        if not self.ic_results:
            print("请先运行 analyze_intensity()")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('强度因子IC分析', fontsize=16, fontweight='bold')
        
        # 1. IC值对比
        ax1 = axes[0, 0]
        ic_values = list(self.ic_results.values())
        ic_names = list(self.ic_results.keys())
        
        bars = ax1.bar(range(len(ic_values)), ic_values, 
                      color=['skyblue' if x > 0 else 'lightcoral' for x in ic_values])
        ax1.set_title('强度IC值')
        ax1.set_ylabel('IC值')
        ax1.set_xticks(range(len(ic_names)))
        ax1.set_xticklabels(ic_names, rotation=45, ha='right')
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height > 0 else -0.01),
                    f'{height:.3f}', ha='center', va='bottom' if height > 0 else 'top')
        
        # 2. 强度分布
        ax2 = axes[0, 1]
        intensity_data = self.data['强度'].dropna()
        ax2.hist(intensity_data, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_title('强度分布')
        ax2.set_xlabel('强度')
        ax2.set_ylabel('频次')
        ax2.axvline(x=intensity_data.mean(), color='red', linestyle='--', 
                   label=f'均值: {intensity_data.mean():.2f}')
        ax2.legend()
        
        # 3. 滚动IC图
        ax3 = axes[1, 0]
        rolling_ic = self.calculate_rolling_ic('强度', 'FutureReturn_1period', window=50)
        ax3.plot(rolling_ic.index, rolling_ic.values, linewidth=1, alpha=0.7)
        ax3.set_title('强度滚动IC (50期窗口)')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('滚动IC值')
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax3.grid(True, alpha=0.3)
        
        # 4. 散点图
        ax4 = axes[1, 1]
        valid_data = self.data[['强度', 'FutureReturn_1period']].dropna()
        ax4.scatter(valid_data['强度'], valid_data['FutureReturn_1period'], 
                   alpha=0.6, s=20, color='blue')
        ax4.set_title('强度 vs 1期收益率')
        ax4.set_xlabel('强度')
        ax4.set_ylabel('1期收益率')
        ax4.grid(True, alpha=0.3)
        
        # 添加趋势线
        z = np.polyfit(valid_data['强度'], valid_data['FutureReturn_1period'], 1)
        p = np.poly1d(z)
        ax4.plot(valid_data['强度'], p(valid_data['强度']), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig('ic_analysis_plot/intensity_ic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()  # 关闭图表，不显示
    
    def generate_report(self):
        """生成分析报告"""
        print("\n" + "="*50)
        print("强度因子IC分析报告")
        print("="*50)
        
        print(f"\n数据概览:")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        print(f"数据总行数: {len(self.data)}")
        print(f"强度统计:")
        intensity_stats = self.data['强度'].describe()
        print(intensity_stats)
        
        # 强度分布分析
        intensity_data = self.data['强度'].dropna()
        high_intensity_count = (intensity_data > intensity_data.quantile(0.75)).sum()
        low_intensity_count = (intensity_data < intensity_data.quantile(0.25)).sum()
        medium_intensity_count = len(intensity_data) - high_intensity_count - low_intensity_count
        
        print(f"\n强度分布:")
        print(f"高强度 (>75%分位数): {high_intensity_count} ({high_intensity_count/len(intensity_data)*100:.1f}%)")
        print(f"中等强度 (25%-75%分位数): {medium_intensity_count} ({medium_intensity_count/len(intensity_data)*100:.1f}%)")
        print(f"低强度 (<25%分位数): {low_intensity_count} ({low_intensity_count/len(intensity_data)*100:.1f}%)")
        
        print(f"\nIC分析结果:")
        for factor_return, ic in self.ic_results.items():
            print(f"{factor_return}: {ic:.4f}")
        
        print(f"\n建议:")
        best_ic = max(self.ic_results.values(), key=lambda x: abs(x) if not np.isnan(x) else 0)
        best_factor = [k for k, v in self.ic_results.items() if v == best_ic][0]
        print(f"最佳IC: {best_factor} (IC = {best_ic:.4f})")
        
        if abs(best_ic) > 0.1:
            print("该因子显示出较强的预测能力")
        elif abs(best_ic) > 0.05:
            print("该因子显示出中等预测能力")
        else:
            print("该因子预测能力较弱，建议进一步优化")

def main():
    """主函数"""
    analyzer = IntensityICAnalyzer('futures_emo_combined_data/sc2210_with_emotion_lag15min.xlsx')
    analyzer.load_data()
    analyzer.analyze_intensity()
    analyzer.plot_intensity_analysis()
    analyzer.generate_report()

if __name__ == "__main__":
    main() 