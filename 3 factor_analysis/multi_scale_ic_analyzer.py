import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os
from tqdm import tqdm

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class MultiScaleICAnalyzer:
    def __init__(self, data_path, output_dir='../analysis_plot/multi_scale'):
        """
        初始化多尺度IC分析器
        
        Parameters:
        -----------
        data_path: str, 数据文件路径
        output_dir: str, 输出目录
        """
        print("加载数据...")
        self.data = pd.read_excel(data_path)
        print(f"数据加载完成，形状: {self.data.shape}")
        
        # 数据预处理
        self.data['DateTime'] = pd.to_datetime(self.data['DateTime'])
        self.data['date'] = self.data['DateTime'].dt.date
        self.data = self.data.set_index('DateTime')
        
        # 创建输出目录
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 待分析的因子列表
        self.factors = ['极性', '强度', '支配维度', '信号量', '信号量_等级']
        
        # 数据预处理
        self._preprocess_data()
        
    def _preprocess_data(self):
        """
        数据预处理
        """
        # 处理缺失值
        for factor in self.factors:
            if factor in self.data.columns:
                # 使用前值填充缺失值
                self.data[factor] = self.data[factor].fillna(method='ffill')
                
                # 处理异常值（3倍标准差法）
                mean = self.data[factor].mean()
                std = self.data[factor].std()
                self.data[factor] = self.data[factor].clip(
                    lower=mean - 3*std,
                    upper=mean + 3*std
                )
        
        print("数据预处理完成")
        
    def calculate_returns(self, price_col='Close', periods=[1, 5, 15, 30, 60]):
        """
        计算多个时间尺度的收益率
        """
        if price_col not in self.data.columns:
            raise ValueError(f"价格列 {price_col} 不存在于数据中")
            
        print("计算各时间尺度收益率...")
        for period in periods:
            # 计算算术收益率
            self.data[f'Return_{period}min'] = self.data[price_col].pct_change(period)
            
            # 计算对数收益率
            self.data[f'LogReturn_{period}min'] = np.log(self.data[price_col]).diff(period)
            
            # 计算波动率
            self.data[f'Volatility_{period}min'] = self.data[f'Return_{period}min'].rolling(period).std()
            
            # 计算绝对收益
            self.data[f'AbsReturn_{period}min'] = self.data[price_col].diff(period)
            
        print("收益率计算完成")

    def calculate_rolling_ic(self, factor, target, window=30):
        """
        计算滚动窗口IC
        """
        # 确保数据对齐
        data = pd.DataFrame({
            'factor': self.data[factor],
            'target': self.data[target]
        }).dropna()
        
        if len(data) < window:
            print(f"警告: 数据长度({len(data)})小于窗口大小({window})")
            return pd.DataFrame()
        
        rolling_ic = []
        for i in range(window, len(data)):
            window_data = data.iloc[i-window:i]
            try:
                pearson_ic = stats.pearsonr(window_data['factor'], 
                                          window_data['target'])[0]
                spearman_ic = stats.spearmanr(window_data['factor'], 
                                            window_data['target'])[0]
                rolling_ic.append({
                    'DateTime': data.index[i],
                    'pearson_ic': pearson_ic,
                    'spearman_ic': spearman_ic
                })
            except Exception as e:
                print(f"计算IC时出错: {e}")
                continue
        
        return pd.DataFrame(rolling_ic)

    def calculate_grouped_ic(self, factor, target, group_by='hour'):
        """
        按不同维度分组计算IC
        """
        # 添加时间特征
        self.data['hour'] = self.data.index.hour
        self.data['minute'] = self.data.index.minute
        self.data['day_of_week'] = self.data.index.dayofweek
        
        grouped_ic = {}
        for group in sorted(self.data[group_by].unique()):
            group_data = self.data[self.data[group_by] == group]
            
            # 确保数据对齐
            valid_data = pd.DataFrame({
                'factor': group_data[factor],
                'target': group_data[target]
            }).dropna()
            
            if len(valid_data) < 30:  # 确保每组至少有30个样本
                print(f"警告: 组 {group} 样本量不足({len(valid_data)})")
                continue
                
            try:
                pearson_ic = stats.pearsonr(valid_data['factor'], 
                                          valid_data['target'])[0]
                spearman_ic = stats.spearmanr(valid_data['factor'], 
                                            valid_data['target'])[0]
                grouped_ic[group] = {
                    'pearson_ic': pearson_ic,
                    'spearman_ic': spearman_ic,
                    'sample_size': len(valid_data)
                }
            except Exception as e:
                print(f"组 {group} 计算IC时出错: {e}")
                continue
        
        return pd.DataFrame(grouped_ic).T

    def plot_multi_scale_ic(self, factor, periods=[1, 5, 15, 30, 60]):
        """
        绘制多尺度IC对比图
        """
        ic_results = []
        for period in periods:
            for return_type in ['Return', 'LogReturn', 'AbsReturn', 'Volatility']:
                target = f'{return_type}_{period}min'
                if target in self.data.columns:
                    # 确保数据对齐
                    valid_data = pd.DataFrame({
                        'factor': self.data[factor],
                        'target': self.data[target]
                    }).dropna()
                    
                    if len(valid_data) < 30:
                        print(f"警告: {target} 样本量不足({len(valid_data)})")
                        continue
                        
                    try:
                        pearson_ic = stats.pearsonr(valid_data['factor'], 
                                                  valid_data['target'])[0]
                        ic_results.append({
                            'period': period,
                            'return_type': return_type,
                            'ic': pearson_ic
                        })
                    except Exception as e:
                        print(f"计算 {target} 的IC时出错: {e}")
                        continue
        
        if not ic_results:
            print("警告: 没有有效的IC结果可供绘图")
            return
            
        ic_df = pd.DataFrame(ic_results)
        
        plt.figure(figsize=(12, 8))
        for return_type in ['Return', 'LogReturn', 'AbsReturn', 'Volatility']:
            data = ic_df[ic_df['return_type'] == return_type]
            if not data.empty:
                plt.plot(data['period'], data['ic'], 
                        marker='o', label=return_type)
        
        plt.title(f'多尺度IC分析: {factor}')
        plt.xlabel('时间尺度（分钟）')
        plt.ylabel('信息系数（IC）')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(self.output_dir, f'multi_scale_ic_{factor}.png'))
        plt.close()
        
        # 打印IC值
        print(f"\n{factor}的多尺度IC值:")
        for _, row in ic_df.iterrows():
            print(f"周期: {row['period']}分钟, "
                  f"收益类型: {row['return_type']}, "
                  f"IC: {row['ic']:.4f}")

    def analyze_all_factors(self, periods=[1, 5, 15, 30, 60]):
        """
        对所有因子进行多尺度分析
        """
        # 计算各种收益率
        self.calculate_returns(periods=periods)
        
        results = []
        for factor in self.factors:
            print(f"\n{'='*50}")
            print(f"分析因子: {factor}")
            print(f"{'='*50}")
            
            try:
                # 1. 多尺度IC分析
                self.plot_multi_scale_ic(factor, periods)
                
                # 2. 分时段IC分析
                hour_ic = self.calculate_grouped_ic(factor, 'Return_1min', 'hour')
                print("\n按小时分组的IC:")
                print(hour_ic)
                
                # 3. 滚动窗口IC分析
                rolling_ic = self.calculate_rolling_ic(factor, 'Return_1min')
                if not rolling_ic.empty:
                    print("\n滚动窗口IC统计:")
                    print(rolling_ic.describe())
                
                # 保存结果
                results.append({
                    'factor': factor,
                    'hour_ic': hour_ic,
                    'rolling_ic': rolling_ic
                })
            except Exception as e:
                print(f"分析因子 {factor} 时出错: {e}")
                continue
            
        return results

if __name__ == "__main__":
    try:
        analyzer = MultiScaleICAnalyzer(
            "../futures_emo_combined_data/sc2210_with_emotion_lag1min.xlsx"
        )
        results = analyzer.analyze_all_factors()
        print("\n多尺度分析完成！")
    except Exception as e:
        print(f"程序运行出错: {e}") 