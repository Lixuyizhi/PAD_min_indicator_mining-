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

class PleasureICAnalyzer:
    """
    极性因子IC分析器
    专门分析极性（Pleasure）与未来收益率的相关性
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
    
    def analyze_pleasure(self):
        """分析极性因子"""
        print("开始分析极性因子...")
        
        returns = ['FutureReturn_1period', 'FutureReturn_5period']
        
        for return_col in returns:
            ic = self.calculate_ic('极性', return_col)
            self.ic_results[f"极性_vs_{return_col}"] = ic
            print(f"极性 vs {return_col}: IC = {ic:.4f}")
        
        return self.ic_results
    
    def plot_pleasure_analysis(self):
        """绘制极性分析图表"""
        if not self.ic_results:
            print("请先运行 analyze_pleasure()")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('极性因子IC分析', fontsize=16, fontweight='bold')
        
        # 1. IC值对比
        ax1 = axes[0, 0]
        ic_values = list(self.ic_results.values())
        ic_names = list(self.ic_results.keys())
        
        bars = ax1.bar(range(len(ic_values)), ic_values, 
                      color=['skyblue' if x > 0 else 'lightcoral' for x in ic_values])
        ax1.set_title('极性IC值')
        ax1.set_ylabel('IC值')
        ax1.set_xticks(range(len(ic_names)))
        ax1.set_xticklabels(ic_names, rotation=45, ha='right')
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height > 0 else -0.01),
                    f'{height:.3f}', ha='center', va='bottom' if height > 0 else 'top')
        
        # 2. 极性分布
        ax2 = axes[0, 1]
        pleasure_data = self.data['极性'].dropna()
        ax2.hist(pleasure_data, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_title('极性分布')
        ax2.set_xlabel('极性')
        ax2.set_ylabel('频次')
        ax2.axvline(x=pleasure_data.mean(), color='red', linestyle='--', 
                   label=f'均值: {pleasure_data.mean():.2f}')
        ax2.axvline(x=0, color='blue', linestyle='--', alpha=0.5, label='中性线')
        ax2.legend()
        
        # 3. 滚动IC图
        ax3 = axes[1, 0]
        rolling_ic = self.calculate_rolling_ic('极性', 'FutureReturn_1period', window=50)
        ax3.plot(rolling_ic.index, rolling_ic.values, linewidth=1, alpha=0.7)
        ax3.set_title('极性滚动IC (50期窗口)')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('滚动IC值')
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax3.grid(True, alpha=0.3)
        
        # 4. 散点图
        ax4 = axes[1, 1]
        valid_data = self.data[['极性', 'FutureReturn_1period']].dropna()
        ax4.scatter(valid_data['极性'], valid_data['FutureReturn_1period'], 
                   alpha=0.6, s=20, color='blue')
        ax4.set_title('极性 vs 1期收益率')
        ax4.set_xlabel('极性')
        ax4.set_ylabel('1期收益率')
        ax4.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='中性线')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # 添加趋势线
        z = np.polyfit(valid_data['极性'], valid_data['FutureReturn_1period'], 1)
        p = np.poly1d(z)
        ax4.plot(valid_data['极性'], p(valid_data['极性']), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig('ic_analysis_plot/pleasure_ic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()  # 关闭图表，不显示
    
    def generate_report(self):
        """生成分析报告"""
        print("\n" + "="*50)
        print("极性因子IC分析报告")
        print("="*50)
        
        print(f"\n数据概览:")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        print(f"数据总行数: {len(self.data)}")
        print(f"极性统计:")
        pleasure_stats = self.data['极性'].describe()
        print(pleasure_stats)
        
        # 极性分布分析
        pleasure_data = self.data['极性'].dropna()
        positive_count = (pleasure_data > 0).sum()
        negative_count = (pleasure_data < 0).sum()
        neutral_count = (pleasure_data == 0).sum()
        
        print(f"\n极性分布:")
        print(f"积极情绪 (>0): {positive_count} ({positive_count/len(pleasure_data)*100:.1f}%)")
        print(f"消极情绪 (<0): {negative_count} ({negative_count/len(pleasure_data)*100:.1f}%)")
        print(f"中性情绪 (=0): {neutral_count} ({neutral_count/len(pleasure_data)*100:.1f}%)")
        
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
    analyzer = PleasureICAnalyzer('futures_emo_combined_data/sc2210_with_emotion_lag15min.xlsx')
    analyzer.load_data()
    analyzer.analyze_pleasure()
    analyzer.plot_pleasure_analysis()
    analyzer.generate_report()

if __name__ == "__main__":
    main() 