import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
from tqdm import tqdm

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class FactorCombinationOptimizer:
    def __init__(self, data_path, output_dir='./analysis_plot/combination'):
        """
        初始化因子组合优化器
        
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
        
    def calculate_factor_correlation(self):
        """
        计算因子间相关性
        """
        factor_data = self.data[self.factors]
        corr_matrix = factor_data.corr()
        
        # 绘制相关性热力图
        plt.figure(figsize=(10, 8))
        plt.imshow(corr_matrix, cmap='RdYlBu', aspect='auto')
        plt.colorbar()
        
        # 添加相关系数标签
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                plt.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                        ha='center', va='center')
        
        plt.xticks(range(len(self.factors)), self.factors, rotation=45)
        plt.yticks(range(len(self.factors)), self.factors)
        plt.title('因子相关性矩阵')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'factor_correlation.png'))
        plt.close()
        
        return corr_matrix
    
    def pca_analysis(self):
        """
        对因子进行PCA分析
        """
        # 标准化因子数据
        scaler = StandardScaler()
        factor_data = scaler.fit_transform(self.data[self.factors])
        
        # PCA分析
        pca = PCA()
        pca_result = pca.fit_transform(factor_data)
        
        # 计算解释方差比
        explained_variance_ratio = pca.explained_variance_ratio_
        cumulative_variance_ratio = np.cumsum(explained_variance_ratio)
        
        # 绘制碎石图
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(explained_variance_ratio) + 1),
                explained_variance_ratio, 'bo-')
        plt.plot(range(1, len(cumulative_variance_ratio) + 1),
                cumulative_variance_ratio, 'ro-')
        plt.xlabel('主成分数量')
        plt.ylabel('解释方差比')
        plt.title('PCA碎石图')
        plt.legend(['单个方差比', '累计方差比'])
        plt.grid(True)
        plt.savefig(os.path.join(self.output_dir, 'pca_scree_plot.png'))
        plt.close()
        
        # 计算因子载荷
        loadings = pd.DataFrame(
            pca.components_.T * np.sqrt(pca.explained_variance_),
            columns=[f'PC{i+1}' for i in range(len(self.factors))],
            index=self.factors
        )
        
        return {
            'pca_result': pca_result,
            'explained_variance_ratio': explained_variance_ratio,
            'loadings': loadings
        }
    
    def optimize_factor_weights(self, target='FutureReturn_1min', 
                              method='equal_weight'):
        """
        优化因子权重
        
        Parameters:
        -----------
        method: str, 权重优化方法
            - 'equal_weight': 等权重
            - 'ic_weight': 基于IC值的权重
            - 'pca_weight': 基于PCA的权重
        """
        if method == 'equal_weight':
            weights = np.ones(len(self.factors)) / len(self.factors)
        
        elif method == 'ic_weight':
            # 计算各因子的IC值
            ic_values = []
            for factor in self.factors:
                ic = stats.pearsonr(self.data[factor], self.data[target])[0]
                ic_values.append(abs(ic))
            
            # 归一化IC值作为权重
            weights = np.array(ic_values) / sum(ic_values)
        
        elif method == 'pca_weight':
            # 使用PCA第一主成分的载荷作为权重
            pca_results = self.pca_analysis()
            weights = abs(pca_results['loadings'].iloc[:, 0])
            weights = weights / weights.sum()
        
        # 计算组合因子
        factor_data = self.data[self.factors]
        combined_factor = np.dot(factor_data, weights)
        
        # 计算组合因子的IC
        combined_ic = stats.pearsonr(combined_factor, self.data[target])[0]
        
        return {
            'weights': dict(zip(self.factors, weights)),
            'combined_factor': combined_factor,
            'combined_ic': combined_ic
        }
    
    def analyze_factor_combinations(self):
        """
        分析不同的因子组合方法
        """
        results = {}
        
        # 1. 计算因子相关性
        correlation_matrix = self.calculate_factor_correlation()
        results['correlation'] = correlation_matrix
        
        # 2. PCA分析
        pca_results = self.pca_analysis()
        results['pca'] = pca_results
        
        # 3. 不同权重方法的组合结果
        for method in ['equal_weight', 'ic_weight', 'pca_weight']:
            combination_results = self.optimize_factor_weights(method=method)
            results[method] = combination_results
        
        # 绘制不同方法的IC对比图
        methods = ['equal_weight', 'ic_weight', 'pca_weight']
        ic_values = [results[method]['combined_ic'] for method in methods]
        
        plt.figure(figsize=(10, 6))
        plt.bar(methods, ic_values)
        plt.title('不同组合方法的IC对比')
        plt.xlabel('组合方法')
        plt.ylabel('Information Coefficient')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'combination_methods_comparison.png'))
        plt.close()
        
        return results

if __name__ == "__main__":
    optimizer = FactorCombinationOptimizer(
        "./futures_emo_combined_data/sc2210_with_emotion_lag1min.xlsx"
    )
    results = optimizer.analyze_factor_combinations()
    print("因子组合分析完成！") 