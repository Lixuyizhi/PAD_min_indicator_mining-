import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
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
    包含IC半衰期检验、IR指标等高级分析
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
        self.ir_results = {}
        self.half_life_results = {}
        # 自动从文件名提取粒度和滞后时间
        match = re.search(r'_([0-9a-zA-Z]+)_lag(\d+)min', data_path)
        if match:
            self.resample_rule = match.group(1)
            self.lag_minutes = match.group(2)
        else:
            self.resample_rule = 'unknown'
            self.lag_minutes = 'unknown'
        # 创建子文件夹名称
        self.subfolder_name = f"{self.resample_rule}_lag{self.lag_minutes}min"
        self.fig_prefix = f"ic_analysis_plot/{self.subfolder_name}/signal_level_ic_{self.resample_rule}_lag{self.lag_minutes}min"
        
        # 确保子文件夹存在
        import os
        os.makedirs(f"ic_analysis_plot/{self.subfolder_name}", exist_ok=True)
        
    def load_data(self):
        """加载数据"""
        print("正在加载数据...")
        self.data = pd.read_excel(self.data_path)
        print(f"数据加载完成，形状: {self.data.shape}")
        print(f"数据时间范围: {self.data['DateTime'].min()} 到 {self.data['DateTime'].max()}")
        return self.data
    
    def calculate_global_ic(self, method='both'):
        """
        计算信号量_等级与未来收益率的全局IC值
        支持pearson、spearman和both两种方法
        """
        results = {}
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        
        if method in ['pearson', 'both']:
            ic_1_pearson = valid_data['信号量_等级'].corr(valid_data['FutureReturn_1period'])
            ic_5_pearson = valid_data['信号量_等级'].corr(valid_data['FutureReturn_5period'])
            results['信号量_等级_vs_FutureReturn_1period_pearson'] = ic_1_pearson
            results['信号量_等级_vs_FutureReturn_5period_pearson'] = ic_5_pearson
            print(f"信号量_等级_vs_FutureReturn_1period (Pearson): {ic_1_pearson:.4f}")
            print(f"信号量_等级_vs_FutureReturn_5period (Pearson): {ic_5_pearson:.4f}")
        
        if method in ['spearman', 'both']:
            ic_1_spearman = valid_data['信号量_等级'].corr(valid_data['FutureReturn_1period'], method='spearman')
            ic_5_spearman = valid_data['信号量_等级'].corr(valid_data['FutureReturn_5period'], method='spearman')
            results['信号量_等级_vs_FutureReturn_1period_spearman'] = ic_1_spearman
            results['信号量_等级_vs_FutureReturn_5period_spearman'] = ic_5_spearman
            print(f"信号量_等级_vs_FutureReturn_1period (Spearman): {ic_1_spearman:.4f}")
            print(f"信号量_等级_vs_FutureReturn_5period (Spearman): {ic_5_spearman:.4f}")
        
        self.ic_results = results
        return results

    def calculate_ir_metrics(self, window=100, method='both'):
        """
        计算IR (Information Ratio) 指标
        IR = IC均值 / IC标准差
        """
        print(f"计算IR指标 (窗口={window})...")
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        
        if len(valid_data) < window * 2:
            print(f"警告：数据量({len(valid_data)})不足，调整窗口大小")
            window = len(valid_data) // 3
        
        ir_results = {}
        
        if method in ['pearson', 'both']:
            rolling_ic_1 = []
            rolling_ic_5 = []
            
            for i in range(window, len(valid_data)):
                window_data = valid_data.iloc[i-window:i]
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'])
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'])
                if not np.isnan(ic1) and not np.isnan(ic5):
                    rolling_ic_1.append(ic1)
                    rolling_ic_5.append(ic5)
            
            if rolling_ic_1 and rolling_ic_5:
                ir_1 = np.mean(rolling_ic_1) / np.std(rolling_ic_1) if np.std(rolling_ic_1) > 0 else 0
                ir_5 = np.mean(rolling_ic_5) / np.std(rolling_ic_5) if np.std(rolling_ic_5) > 0 else 0
                ir_results['IR_1period_pearson'] = ir_1
                ir_results['IR_5period_pearson'] = ir_5
                print(f"IR_1period (Pearson): {ir_1:.4f}")
                print(f"IR_5period (Pearson): {ir_5:.4f}")
        
        if method in ['spearman', 'both']:
            rolling_ic_1 = []
            rolling_ic_5 = []
            
            for i in range(window, len(valid_data)):
                window_data = valid_data.iloc[i-window:i]
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'], method='spearman')
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'], method='spearman')
                if not np.isnan(ic1) and not np.isnan(ic5):
                    rolling_ic_1.append(ic1)
                    rolling_ic_5.append(ic5)
            
            if rolling_ic_1 and rolling_ic_5:
                ir_1 = np.mean(rolling_ic_1) / np.std(rolling_ic_1) if np.std(rolling_ic_1) > 0 else 0
                ir_5 = np.mean(rolling_ic_5) / np.std(rolling_ic_5) if np.std(rolling_ic_5) > 0 else 0
                ir_results['IR_1period_spearman'] = ir_1
                ir_results['IR_5period_spearman'] = ir_5
                print(f"IR_1period (Spearman): {ir_1:.4f}")
                print(f"IR_5period (Spearman): {ir_5:.4f}")
        
        self.ir_results = ir_results
        return ir_results

    def calculate_ic_half_life(self, method='both'):
        """
        计算IC半衰期
        使用指数衰减模型拟合IC衰减曲线
        """
        print("计算IC半衰期...")
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        
        def exponential_decay(x, a, b, c):
            """指数衰减函数"""
            return a * np.exp(-b * x) + c
        
        half_life_results = {}
        
        # 计算不同滞后的IC值
        max_lag = min(20, len(valid_data) // 10)  # 最大滞后20期或数据量的1/10
        
        if method in ['pearson', 'both']:
            ic_series_1 = []
            ic_series_5 = []
            lags = []
            
            for lag in range(1, max_lag + 1):
                if lag == 1:
                    ic1 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_1period'])
                    ic5 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_5period'])
                else:
                    # 对于多期滞后，需要调整数据对齐
                    temp_data = valid_data.copy()
                    temp_data['FutureReturn_1period_lag'] = temp_data['FutureReturn_1period'].shift(lag-1)
                    temp_data['FutureReturn_5period_lag'] = temp_data['FutureReturn_5period'].shift(lag-1)
                    temp_data = temp_data.dropna()
                    
                    if len(temp_data) > 10:  # 确保有足够的数据
                        ic1 = temp_data['信号量_等级'].corr(temp_data['FutureReturn_1period_lag'])
                        ic5 = temp_data['信号量_等级'].corr(temp_data['FutureReturn_5period_lag'])
                    else:
                        break
                
                if not np.isnan(ic1) and not np.isnan(ic5):
                    ic_series_1.append(abs(ic1))
                    ic_series_5.append(abs(ic5))
                    lags.append(lag)
            
            if len(lags) > 3:
                try:
                    # 拟合1期收益率IC半衰期
                    popt1, _ = curve_fit(exponential_decay, lags, ic_series_1, p0=[ic_series_1[0], 0.1, 0])
                    # 添加合理性检查
                    if popt1[1] > 0.001 and popt1[1] < 10:  # 合理的衰减率范围
                        half_life_1 = np.log(2) / popt1[1]
                        if half_life_1 < 500:  # 1小时数据合理半衰期范围：1-500期
                            half_life_results['half_life_1period_pearson'] = half_life_1
                            print(f"1期收益率IC半衰期 (Pearson): {half_life_1:.2f} 期")
                        else:
                            half_life_results['half_life_1period_pearson'] = np.nan
                            print(f"1期收益率IC半衰期 (Pearson): 拟合异常，IC衰减过慢")
                    else:
                        half_life_results['half_life_1period_pearson'] = np.nan
                        print(f"1期收益率IC半衰期 (Pearson): 拟合参数异常")
                    
                    # 拟合5期收益率IC半衰期
                    popt5, _ = curve_fit(exponential_decay, lags, ic_series_5, p0=[ic_series_5[0], 0.1, 0])
                    if popt5[1] > 0.001 and popt5[1] < 10:
                        half_life_5 = np.log(2) / popt5[1]
                        if half_life_5 < 500:
                            half_life_results['half_life_5period_pearson'] = half_life_5
                            print(f"5期收益率IC半衰期 (Pearson): {half_life_5:.2f} 期")
                        else:
                            half_life_results['half_life_5period_pearson'] = np.nan
                            print(f"5期收益率IC半衰期 (Pearson): 拟合异常，IC衰减过慢")
                    else:
                        half_life_results['half_life_5period_pearson'] = np.nan
                        print(f"5期收益率IC半衰期 (Pearson): 拟合参数异常")
                    
                except Exception as e:
                    print(f"IC半衰期拟合失败 (Pearson): {e}")
                    half_life_results['half_life_1period_pearson'] = np.nan
                    half_life_results['half_life_5period_pearson'] = np.nan
        
        if method in ['spearman', 'both']:
            ic_series_1 = []
            ic_series_5 = []
            lags = []
            
            for lag in range(1, max_lag + 1):
                if lag == 1:
                    ic1 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_1period'], method='spearman')
                    ic5 = valid_data['信号量_等级'].corr(valid_data['FutureReturn_5period'], method='spearman')
                else:
                    temp_data = valid_data.copy()
                    temp_data['FutureReturn_1period_lag'] = temp_data['FutureReturn_1period'].shift(lag-1)
                    temp_data['FutureReturn_5period_lag'] = temp_data['FutureReturn_5period'].shift(lag-1)
                    temp_data = temp_data.dropna()
                    
                    if len(temp_data) > 10:
                        ic1 = temp_data['信号量_等级'].corr(temp_data['FutureReturn_1period_lag'], method='spearman')
                        ic5 = temp_data['信号量_等级'].corr(temp_data['FutureReturn_5period_lag'], method='spearman')
                    else:
                        break
                
                if not np.isnan(ic1) and not np.isnan(ic5):
                    ic_series_1.append(abs(ic1))
                    ic_series_5.append(abs(ic5))
                    lags.append(lag)
            
            if len(lags) > 3:
                try:
                    # 拟合1期收益率IC半衰期
                    popt1, _ = curve_fit(exponential_decay, lags, ic_series_1, p0=[ic_series_1[0], 0.1, 0])
                    # 添加合理性检查
                    if popt1[1] > 0.001 and popt1[1] < 10:  # 合理的衰减率范围
                        half_life_1 = np.log(2) / popt1[1]
                        if half_life_1 < 500:  # 1小时数据合理半衰期范围：1-500期
                            half_life_results['half_life_1period_spearman'] = half_life_1
                            print(f"1期收益率IC半衰期 (Spearman): {half_life_1:.2f} 期")
                        else:
                            half_life_results['half_life_1period_spearman'] = np.nan
                            print(f"1期收益率IC半衰期 (Spearman): 拟合异常，IC衰减过慢")
                    else:
                        half_life_results['half_life_1period_spearman'] = np.nan
                        print(f"1期收益率IC半衰期 (Spearman): 拟合参数异常")
                    
                    # 拟合5期收益率IC半衰期
                    popt5, _ = curve_fit(exponential_decay, lags, ic_series_5, p0=[ic_series_5[0], 0.1, 0])
                    if popt5[1] > 0.001 and popt5[1] < 10:
                        half_life_5 = np.log(2) / popt5[1]
                        if half_life_5 < 500:
                            half_life_results['half_life_5period_spearman'] = half_life_5
                            print(f"5期收益率IC半衰期 (Spearman): {half_life_5:.2f} 期")
                        else:
                            half_life_results['half_life_5period_spearman'] = np.nan
                            print(f"5期收益率IC半衰期 (Spearman): 拟合异常，IC衰减过慢")
                    else:
                        half_life_results['half_life_5period_spearman'] = np.nan
                        print(f"5期收益率IC半衰期 (Spearman): 拟合参数异常")
                    
                except Exception as e:
                    print(f"IC半衰期拟合失败 (Spearman): {e}")
                    half_life_results['half_life_1period_spearman'] = np.nan
                    half_life_results['half_life_5period_spearman'] = np.nan
        
        self.half_life_results = half_life_results
        return half_life_results

    def get_recommended_window(self):
        """
        根据数据粒度直接推荐合适的窗口大小
        """
        print("根据数据粒度推荐窗口大小...")
        
        # 从文件名提取粒度信息
        if self.resample_rule == '1min':
            # 1分钟数据：推荐2-3小时的窗口
            recommended_window = 120
            print(f"1分钟粒度数据，推荐窗口: {recommended_window} (约4小时)")
        elif self.resample_rule == '15min':
            # 15分钟数据：推荐1-2天的窗口
            recommended_window = 144
            print(f"15分钟粒度数据，推荐窗口: {recommended_window} (约26小时)")
        elif self.resample_rule == '30min':
            # 30分钟数据：推荐2-3天的窗口
            recommended_window = 200   
            print(f"30分钟粒度数据，推荐窗口: {recommended_window} (约24小时)")
        elif self.resample_rule == '1h':
            # 1小时数据：推荐5-8天的窗口
            recommended_window = 400
            print(f"1小时粒度数据，推荐窗口: {recommended_window} (约40小时)")
        else:
            # 默认窗口
            recommended_window = 100
            print(f"未知粒度，使用默认窗口: {recommended_window}")
        
        # 检查数据量是否足够
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        if len(valid_data) < recommended_window * 2:
            # 如果数据量不足，调整窗口大小
            recommended_window = len(valid_data) // 3
            print(f"数据量不足，调整窗口为: {recommended_window}")
        
        return recommended_window

    def plot_comprehensive_analysis(self, window=100):
        """
        绘制综合分析图表，包含IC、IR、半衰期等指标
        """
        print("生成综合分析图表...")
        
        # 创建2x3的子图布局
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle(f'信号量等级因子综合分析 ({self.resample_rule}粒度, 滞后{self.lag_minutes}分钟)', 
                    fontsize=16, fontweight='bold')
        
        # 1. 全局IC对比 (左上)
        ax1 = plt.subplot(2, 3, 1)
        ic_names = list(self.ic_results.keys())
        ic_values = list(self.ic_results.values())
        colors = ['blue', 'lightblue', 'green', 'lightgreen']
        bars = ax1.bar(range(len(ic_names)), ic_values, color=colors[:len(ic_names)])
        ax1.set_title('全局IC对比')
        ax1.set_ylabel('IC值')
        ax1.set_xticks(range(len(ic_names)))
        ax1.set_xticklabels([name.replace('信号量_等级_vs_', '').replace('_pearson', '(P)').replace('_spearman', '(S)') 
                            for name in ic_names], rotation=45, ha='right')
        ax1.axhline(0, color='black', linestyle='-', alpha=0.3)
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, value in zip(bars, ic_values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.001 if height >= 0 else -0.003),
                    f'{value:.4f}', ha='center', va='bottom' if height >= 0 else 'top')
        
        # 2. IR指标对比 (中上)
        ax2 = plt.subplot(2, 3, 2)
        if self.ir_results:
            ir_names = list(self.ir_results.keys())
            ir_values = list(self.ir_results.values())
            colors = ['red', 'orange', 'purple', 'pink']
            bars = ax2.bar(range(len(ir_names)), ir_values, color=colors[:len(ir_names)])
            ax2.set_title('IR指标对比')
            ax2.set_ylabel('IR值')
            ax2.set_xticks(range(len(ir_names)))
            ax2.set_xticklabels([name.replace('IR_', '').replace('_pearson', '(P)').replace('_spearman', '(S)') 
                                for name in ir_names], rotation=45, ha='right')
            ax2.axhline(0, color='black', linestyle='-', alpha=0.3)
            ax2.grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, value in zip(bars, ir_values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height >= 0 else -0.02),
                        f'{value:.3f}', ha='center', va='bottom' if height >= 0 else 'top')
        
        # 3. IC半衰期对比 (右上)
        ax3 = plt.subplot(2, 3, 3)
        if self.half_life_results:
            hl_names = list(self.half_life_results.keys())
            hl_values = list(self.half_life_results.values())
            colors = ['brown', 'tan', 'olive', 'yellow']
            bars = ax3.bar(range(len(hl_names)), hl_values, color=colors[:len(hl_names)])
            ax3.set_title('IC半衰期对比')
            ax3.set_ylabel('半衰期 (期数)')
            ax3.set_xticks(range(len(hl_names)))
            ax3.set_xticklabels([name.replace('half_life_', '').replace('_pearson', '(P)').replace('_spearman', '(S)') 
                                for name in hl_names], rotation=45, ha='right')
            ax3.grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, value in zip(bars, hl_values):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{value:.1f}', ha='center', va='bottom')
        
        # 4. 滚动IC时间序列 (左下)
        ax4 = plt.subplot(2, 3, 4)
        self._plot_rolling_ic_on_axis(ax4, window, 'pearson')
        ax4.set_title(f'滚动IC时间序列 (Pearson, 窗口={window})')
        
        # 5. 滚动IC时间序列 (中下)
        ax5 = plt.subplot(2, 3, 5)
        self._plot_rolling_ic_on_axis(ax5, window, 'spearman')
        ax5.set_title(f'滚动IC时间序列 (Spearman, 窗口={window})')
        
        # 6. IC分布对比 (右下)
        ax6 = plt.subplot(2, 3, 6)
        self._plot_ic_distribution_on_axis(ax6, window)
        ax6.set_title(f'IC分布对比 (窗口={window})')
        
        plt.tight_layout()
        plt.savefig(f'{self.fig_prefix}_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_rolling_ic_on_axis(self, ax, window, method):
        """在指定轴上绘制滚动IC"""
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        if valid_data.empty:
            return
        
        rolling_ic_1 = []
        rolling_ic_5 = []
        idx = []
        
        for i in range(window, len(valid_data)):
            window_data = valid_data.iloc[i-window:i]
            if method == 'pearson':
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'])
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'])
            else:
                ic1 = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'], method='spearman')
                ic5 = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'], method='spearman')
            
            if not np.isnan(ic1) and not np.isnan(ic5):
                rolling_ic_1.append(ic1)
                rolling_ic_5.append(ic5)
                idx.append(i)
        
        if rolling_ic_1 and rolling_ic_5:
            ax.plot(idx, rolling_ic_1, label='1期收益率', color='blue', alpha=0.7)
            ax.plot(idx, rolling_ic_5, label='5期收益率', color='green', alpha=0.7)
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)
            ax.axhline(np.mean(rolling_ic_1), color='blue', linestyle=':', alpha=0.8, 
                      label=f'1期均值: {np.mean(rolling_ic_1):.4f}')
            ax.axhline(np.mean(rolling_ic_5), color='green', linestyle=':', alpha=0.8, 
                      label=f'5期均值: {np.mean(rolling_ic_5):.4f}')
            ax.set_xlabel('样本序号')
            ax.set_ylabel('IC值')
            ax.legend()
            ax.grid(True, alpha=0.3)

    def _plot_ic_distribution_on_axis(self, ax, window):
        """在指定轴上绘制IC分布"""
        valid_data = self.data[['信号量_等级', 'FutureReturn_1period', 'FutureReturn_5period']].dropna()
        if valid_data.empty:
            return
        
        rolling_ic_1_pearson = []
        rolling_ic_5_pearson = []
        rolling_ic_1_spearman = []
        rolling_ic_5_spearman = []
        
        for i in range(window, len(valid_data)):
            window_data = valid_data.iloc[i-window:i]
            
            # Pearson
            ic1_p = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'])
            ic5_p = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'])
            
            # Spearman
            ic1_s = window_data['信号量_等级'].corr(window_data['FutureReturn_1period'], method='spearman')
            ic5_s = window_data['信号量_等级'].corr(window_data['FutureReturn_5period'], method='spearman')
            
            if not np.isnan(ic1_p) and not np.isnan(ic5_p):
                rolling_ic_1_pearson.append(ic1_p)
                rolling_ic_5_pearson.append(ic5_p)
            if not np.isnan(ic1_s) and not np.isnan(ic5_s):
                rolling_ic_1_spearman.append(ic1_s)
                rolling_ic_5_spearman.append(ic5_s)
        
        # 绘制分布
        if rolling_ic_1_pearson:
            ax.hist(rolling_ic_1_pearson, bins=30, alpha=0.6, label='1期(Pearson)', color='blue')
            ax.hist(rolling_ic_5_pearson, bins=30, alpha=0.6, label='5期(Pearson)', color='green')
        if rolling_ic_1_spearman:
            ax.hist(rolling_ic_1_spearman, bins=30, alpha=0.4, label='1期(Spearman)', color='red')
            ax.hist(rolling_ic_5_spearman, bins=30, alpha=0.4, label='5期(Spearman)', color='orange')
        
        ax.set_xlabel('IC值')
        ax.set_ylabel('频次')
        ax.legend()
        ax.grid(True, alpha=0.3)

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
    analyzer = SignalLevelICAnalyzer('futures_emo_combined_data/ag2212_with_emotion_30min_lag90min.xlsx')
    analyzer.load_data()
    
    # 1. 计算全局IC (包含Pearson和Spearman)
    print("\n" + "="*50)
    print("全局IC分析")
    print("="*50)
    analyzer.calculate_global_ic(method='both')
    
    # 2. 根据数据粒度推荐窗口
    print("\n" + "="*50)
    print("滚动IC窗口推荐")
    print("="*50)
    recommended_window = analyzer.get_recommended_window()
    
    # 3. 计算IR指标
    print("\n" + "="*50)
    print("IR指标分析")
    print("="*50)
    analyzer.calculate_ir_metrics(window=recommended_window, method='both')
    
    # 4. 计算IC半衰期
    print("\n" + "="*50)
    print("IC半衰期分析")
    print("="*50)
    analyzer.calculate_ic_half_life(method='both')
    
    # 5. 生成可视化图表
    print("\n" + "="*50)
    print("生成可视化图表")
    print("="*50)
    analyzer.plot_global_relationship()
    analyzer.plot_rolling_ic(window=recommended_window)
    analyzer.plot_rolling_ic_stability(window=recommended_window)
    analyzer.plot_comprehensive_analysis(window=recommended_window)
    
    # 6. 生成分析报告
    analyzer.generate_report()

if __name__ == "__main__":
    main() 