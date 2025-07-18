import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
from tqdm import tqdm

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class ConditionalICAnalyzer:
    def __init__(self, data_path, output_dir='./analysis_plot/conditional'):
        """
        初始化条件IC分析器
        
        Parameters:
        -----------
        data_path: str, 数据文件路径
        output_dir: str, 输出目录
        """
        self.data = pd.read_excel(data_path)
        self.data['DateTime'] = pd.to_datetime(self.data['DateTime'])
        self.data['date'] = self.data['DateTime'].dt.date
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 待分析的因子列表
        self.factors = ['极性', '强度', '支配维度', '信号量', '信号量_等级']
        
    def calculate_market_state(self, price_col='Close', vol_col='Volume', 
                             ret_window=30, vol_window=30):
        """
        计算市场状态指标
        """
        # 计算收益率
        self.data['return'] = self.data[price_col].pct_change()
        
        # 计算波动率状态
        self.data['volatility'] = self.data['return'].rolling(ret_window).std()
        self.data['vol_state'] = pd.qcut(self.data['volatility'], 3, 
                                       labels=['低波动', '中波动', '高波动'])
        
        # 计算成交量状态
        self.data['volume_ma'] = self.data[vol_col].rolling(vol_window).mean()
        self.data['vol_ratio'] = self.data[vol_col] / self.data['volume_ma']
        self.data['volume_state'] = pd.qcut(self.data['vol_ratio'], 3,
                                          labels=['低成交', '中成交', '高成交'])
        
        # 计算趋势状态
        self.data['price_ma'] = self.data[price_col].rolling(ret_window).mean()
        self.data['trend'] = np.where(self.data[price_col] > self.data['price_ma'], 
                                    '上涨', '下跌')
        
    def calculate_conditional_ic(self, factor, target, condition_col):
        """
        计算条件IC
        """
        results = {}
        for condition in self.data[condition_col].unique():
            condition_data = self.data[self.data[condition_col] == condition]
            if len(condition_data) > 30:  # 确保样本量足够
                pearson_ic = stats.pearsonr(condition_data[factor], 
                                          condition_data[target])[0]
                spearman_ic = stats.spearmanr(condition_data[factor], 
                                            condition_data[target])[0]
                results[condition] = {
                    'pearson_ic': pearson_ic,
                    'spearman_ic': spearman_ic,
                    'sample_size': len(condition_data)
                }
        return results
    
    def plot_conditional_ic(self, factor, condition_results, condition_type):
        """
        绘制条件IC对比图
        """
        conditions = list(condition_results.keys())
        pearson_ics = [result['pearson_ic'] for result in condition_results.values()]
        spearman_ics = [result['spearman_ic'] for result in condition_results.values()]
        
        plt.figure(figsize=(10, 6))
        x = np.arange(len(conditions))
        width = 0.35
        
        plt.bar(x - width/2, pearson_ics, width, label='Pearson IC')
        plt.bar(x + width/2, spearman_ics, width, label='Spearman IC')
        
        plt.title(f'{factor} - {condition_type}条件IC分析')
        plt.xlabel('市场状态')
        plt.ylabel('Information Coefficient')
        plt.xticks(x, conditions)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(os.path.join(self.output_dir, 
                                f'conditional_ic_{factor}_{condition_type}.png'))
        plt.close()
    
    def analyze_factor_conditions(self, factor, target='FutureReturn_1min'):
        """
        分析因子在不同条件下的表现
        """
        results = {}
        
        # 波动率条件
        vol_results = self.calculate_conditional_ic(factor, target, 'vol_state')
        self.plot_conditional_ic(factor, vol_results, '波动率')
        results['volatility'] = vol_results
        
        # 成交量条件
        volume_results = self.calculate_conditional_ic(factor, target, 'volume_state')
        self.plot_conditional_ic(factor, volume_results, '成交量')
        results['volume'] = volume_results
        
        # 趋势条件
        trend_results = self.calculate_conditional_ic(factor, target, 'trend')
        self.plot_conditional_ic(factor, trend_results, '趋势')
        results['trend'] = trend_results
        
        return results
    
    def analyze_all_factors(self):
        """
        分析所有因子
        """
        # 计算市场状态
        self.calculate_market_state()
        
        all_results = {}
        for factor in self.factors:
            print(f"\n分析因子: {factor}")
            factor_results = self.analyze_factor_conditions(factor)
            all_results[factor] = factor_results
            
        return all_results

if __name__ == "__main__":
    analyzer = ConditionalICAnalyzer(
        "./futures_emo_combined_data/sc2210_with_emotion_lag1min.xlsx"
    )
    results = analyzer.analyze_all_factors()
    print("条件IC分析完成！") 