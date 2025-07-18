import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
import os
from tqdm import tqdm

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 使用支持中文的字体
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 创建输出目录
output_dir = './analysis_plot'
os.makedirs(output_dir, exist_ok=True)

# 加载数据
print("Loading data...")
df = pd.read_excel("./futures_emo_combined_data/sc2210_with_emotion_lag15min.xlsx")
print("Data loaded, shape:", df.shape)

# 将时间列转换为datetime格式
df['DateTime'] = pd.to_datetime(df['DateTime'])
df['date'] = df['DateTime'].dt.date

# 待分析因子列表
factors = ['极性', '强度', '支配维度', '信号量', '信号量_等级']
target = 'FutureReturn_1period'  # 目标变量

def preprocess_data(data):
    """
    数据预处理函数
    
    1. 处理异常值
    2. 标准化因子值
    3. 处理缺失值
    """
    processed_data = data.copy()
    
    # 对每个因子进行预处理
    for factor in factors:
        # 处理异常值 (3σ法则)
        mean = processed_data[factor].mean()
        std = processed_data[factor].std()
        processed_data[factor] = processed_data[factor].clip(
            lower=mean - 3*std,
            upper=mean + 3*std
        )
        
        # 标准化
        processed_data[factor] = (processed_data[factor] - processed_data[factor].mean()) / processed_data[factor].std()
    
    # 处理目标变量异常值
    mean_return = processed_data[target].mean()
    std_return = processed_data[target].std()
    processed_data[target] = processed_data[target].clip(
        lower=mean_return - 3*std_return,
        upper=mean_return + 3*std_return
    )
    
    return processed_data

def filter_signal_data(data):
    """
    对信号量和信号等级进行分段过滤
    
    Returns:
    --------
    dict : 包含不同区间的数据
    """
    filtered_data = {}
    
    # 复制原始数据
    data = data.copy()
    
    # 信号量分段
    filtered_data['信号量_强'] = data[abs(data['信号量']) > 50].copy()
    filtered_data['信号量_中强'] = data[(abs(data['信号量']) > 30) & (abs(data['信号量']) <= 50)].copy()
    filtered_data['信号量_中弱'] = data[(abs(data['信号量']) > 10) & (abs(data['信号量']) <= 30)].copy()
    
    # 信号等级分段（排除中性区间4-6）
    filtered_data['信号量_等级_强空'] = data[data['信号量_等级'] < 4].copy()
    filtered_data['信号量_等级_强多'] = data[data['信号量_等级'] > 6].copy()
    
    return filtered_data

def calculate_ic(data, factor, target, is_signal_analysis=False):
    """
    计算因子与目标变量的相关系数
    
    Parameters:
    -----------
    data : DataFrame
        包含因子和目标变量的数据
    factor : str
        因子名称
    target : str
        目标变量名称
    is_signal_analysis : bool
        是否进行信号分段分析
    
    Returns:
    --------
    dict : 包含各种IC指标的字典
    """
    if is_signal_analysis and factor in ['信号量', '信号量_等级']:
        # 对信号量和信号等级进行分段分析
        filtered_data = filter_signal_data(data)
        results = {}
        
        for segment_name, segment_data in filtered_data.items():
            if len(segment_data) >= 2:
                # 确保数据对齐
                valid_data = segment_data[[factor, target]].dropna()
                
                # 计算相关系数
                pearson_corr, pearson_p = stats.pearsonr(valid_data[factor], valid_data[target])
                spearman_corr, spearman_p = stats.spearmanr(valid_data[factor], valid_data[target])
                kendall_corr, kendall_p = stats.kendalltau(valid_data[factor], valid_data[target])
                
                # 多重检验校正
                p_values = [pearson_p, spearman_p, kendall_p]
                p_adjusted = multipletests(p_values, method='fdr_bh')[1]
                
                results[segment_name] = {
                    'pearson_ic': pearson_corr,
                    'pearson_p': pearson_p,
                    'pearson_p_adj': p_adjusted[0],
                    'spearman_ic': spearman_corr,
                    'spearman_p': spearman_p,
                    'spearman_p_adj': p_adjusted[1],
                    'kendall_ic': kendall_corr,
                    'kendall_p': kendall_p,
                    'kendall_p_adj': p_adjusted[2],
                    'sample_size': len(valid_data)
                }
            else:
                results[segment_name] = {
                    'pearson_ic': np.nan,
                    'pearson_p': np.nan,
                    'pearson_p_adj': np.nan,
                    'spearman_ic': np.nan,
                    'spearman_p': np.nan,
                    'spearman_p_adj': np.nan,
                    'kendall_ic': np.nan,
                    'kendall_p': np.nan,
                    'kendall_p_adj': np.nan,
                    'sample_size': 0
                }
        
        return results
    
    # 常规因子分析
    valid_data = data[[factor, target]].dropna()
    
    if len(valid_data) < 2:
        return {
            'factor': factor,
            'pearson_ic': np.nan,
            'pearson_p': np.nan,
            'pearson_p_adj': np.nan,
            'spearman_ic': np.nan,
            'spearman_p': np.nan,
            'spearman_p_adj': np.nan,
            'kendall_ic': np.nan,
            'kendall_p': np.nan,
            'kendall_p_adj': np.nan,
            'sample_size': 0
        }
    
    # 计算相关系数
    pearson_corr, pearson_p = stats.pearsonr(valid_data[factor], valid_data[target])
    spearman_corr, spearman_p = stats.spearmanr(valid_data[factor], valid_data[target])
    kendall_corr, kendall_p = stats.kendalltau(valid_data[factor], valid_data[target])
    
    # 多重检验校正
    p_values = [pearson_p, spearman_p, kendall_p]
    p_adjusted = multipletests(p_values, method='fdr_bh')[1]
    
    return {
        'factor': factor,
        'pearson_ic': pearson_corr,
        'pearson_p': pearson_p,
        'pearson_p_adj': p_adjusted[0],
        'spearman_ic': spearman_corr,
        'spearman_p': spearman_p,
        'spearman_p_adj': p_adjusted[1],
        'kendall_ic': kendall_corr,
        'kendall_p': kendall_p,
        'kendall_p_adj': p_adjusted[2],
        'sample_size': len(valid_data)
    }

def daily_ic_analysis(data, factor, target):
    """
    按天计算因子IC并分析稳定性
    """
    daily_results = []
    
    for date, group in tqdm(data.groupby('date'), desc=f"Calculating daily IC for {factor}"):
        if len(group) > 30:  # 确保每天有足够的样本
            ic_result = calculate_ic(group, factor, target)
            daily_results.append({
                'date': date,
                'pearson_ic': ic_result['pearson_ic'],
                'spearman_ic': ic_result['spearman_ic'],
                'kendall_ic': ic_result['kendall_ic']
            })
    
    daily_df = pd.DataFrame(daily_results)
    if len(daily_df) == 0:
        return None, {}
    
    # 计算IC序列的统计特征
    stats_dict = {}
    for ic_type in ['pearson_ic', 'spearman_ic', 'kendall_ic']:
        stats_dict[f'mean_{ic_type}'] = daily_df[ic_type].mean()
        stats_dict[f'std_{ic_type}'] = daily_df[ic_type].std()
        stats_dict[f'ir_{ic_type}'] = (
            daily_df[ic_type].mean() / daily_df[ic_type].std() 
            if daily_df[ic_type].std() != 0 else 0
        )
        stats_dict[f'positive_ratio_{ic_type}'] = (daily_df[ic_type] > 0).mean()
        stats_dict[f't_stat_{ic_type}'] = (
            stats_dict[f'mean_{ic_type}'] * np.sqrt(len(daily_df)) / 
            stats_dict[f'std_{ic_type}'] if stats_dict[f'std_{ic_type}'] != 0 else 0
        )
        stats_dict[f'p_value_{ic_type}'] = 2 * (1 - stats.t.cdf(
            abs(stats_dict[f't_stat_{ic_type}']), 
            len(daily_df) - 1
        )) if stats_dict[f'std_{ic_type}'] != 0 else 1
    
    # 绘制IC时间序列图
    plt.figure(figsize=(15, 10))
    
    # 创建三个子图
    for i, ic_type in enumerate(['pearson_ic', 'spearman_ic', 'kendall_ic']):
        plt.subplot(3, 1, i+1)
        plt.plot(daily_df['date'], daily_df[ic_type], label=f'Daily {ic_type.split("_")[0]} IC')
        plt.axhline(y=stats_dict[f'mean_{ic_type}'], color='r', linestyle='--', 
                   label=f'Mean: {stats_dict[f"mean_{ic_type}"]:.4f}')
        plt.axhline(y=0, color='k', linestyle='-')
        plt.fill_between(
            daily_df['date'],
            stats_dict[f'mean_{ic_type}'] - stats_dict[f'std_{ic_type}'],
            stats_dict[f'mean_{ic_type}'] + stats_dict[f'std_{ic_type}'],
            color='gray', alpha=0.2, label=f'±1 std dev'
        )
        plt.title(f'{ic_type.split("_")[0]} IC Time Series for {factor}')
        plt.xlabel('Date')
        plt.ylabel('IC Value')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'IC_stability_{factor}.png'), dpi=300)
    plt.close()
    
    return daily_df, stats_dict

def factor_decay_analysis(data, factor, target, max_lag=20):
    """分析因子IC随时间衰减情况"""
    decay_results = []
    
    # 计算不同滞后期的IC
    for lag in tqdm(range(1, max_lag+1), desc=f"Factor decay analysis for {factor}"):
        # 创建滞后收益率
        lagged_return = data.groupby('date')[target].shift(-lag)
        temp_data = data.copy()
        temp_data[target] = lagged_return
        
        # 计算当前滞后期的IC
        ic_result = calculate_ic(temp_data, factor, target)
        decay_results.append({
            'lag': lag,
            'pearson_ic': ic_result['pearson_ic'],
            'spearman_ic': ic_result['spearman_ic'],
            'kendall_ic': ic_result['kendall_ic']
        })
    
    decay_df = pd.DataFrame(decay_results)
    
    # 绘制衰减曲线
    plt.figure(figsize=(12, 8))
    for ic_type in ['pearson_ic', 'spearman_ic', 'kendall_ic']:
        plt.plot(decay_df['lag'], decay_df[ic_type], 
                marker='o', label=f'{ic_type.split("_")[0]} IC')
    
    plt.axhline(y=0, color='k', linestyle='-')
    plt.title(f'Factor IC Decay Analysis: {factor}')
    plt.xlabel('Time Lag (minutes)')
    plt.ylabel('Information Coefficient (IC)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'IC_decay_{factor}.png'), dpi=300)
    plt.close()
    
    # 计算衰减指标
    decay_metrics = {}
    for ic_type in ['pearson_ic', 'spearman_ic', 'kendall_ic']:
        initial_ic = decay_df[ic_type].iloc[0]
        half_ic = initial_ic / 2
        
        # 计算半衰期
        if initial_ic != 0:
            half_life = decay_df[abs(decay_df[ic_type]) <= abs(half_ic)]['lag'].iloc[0] \
                if any(abs(decay_df[ic_type]) <= abs(half_ic)) else max_lag
        else:
            half_life = np.nan
            
        decay_metrics[f'{ic_type}_half_life'] = half_life
        decay_metrics[f'{ic_type}_initial'] = initial_ic
        
    return decay_df, decay_metrics

def factor_autocorrelation(data, factor, max_lag=10):
    """分析因子自相关性"""
    # 按天计算自相关系数
    daily_autocorr = []
    
    for date, group in data.groupby('date'):
        if len(group) > max_lag + 10:  # 确保有足够的数据点
            series = group[factor].values
            autocorr = []
            for lag in range(1, max_lag + 1):
                corr = np.corrcoef(series[lag:], series[:-lag])[0, 1]
                autocorr.append(corr)
            daily_autocorr.append(autocorr)
    
    # 计算平均自相关系数
    if daily_autocorr:
        mean_autocorr = np.mean(daily_autocorr, axis=0)
        std_autocorr = np.std(daily_autocorr, axis=0)
    else:
        mean_autocorr = np.zeros(max_lag)
        std_autocorr = np.zeros(max_lag)
    
    # 绘制自相关图
    plt.figure(figsize=(12, 6))
    plt.errorbar(range(1, max_lag+1), mean_autocorr, yerr=std_autocorr,
                fmt='o-', capsize=5, label='Mean ± Std')
    plt.axhline(y=0, color='k', linestyle='-')
    plt.axhline(y=0.5, color='r', linestyle='--', label='0.5 threshold')
    plt.axhline(y=-0.5, color='r', linestyle='--')
    plt.title(f'Factor Autocorrelation: {factor}')
    plt.xlabel('Time Lag (minutes)')
    plt.ylabel('Autocorrelation Coefficient')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'autocorrelation_{factor}.png'), dpi=300)
    plt.close()
    
    # 计算持续性指标
    persistence = sum(abs(mean_autocorr) > 0.5)
    first_below_half = np.where(abs(mean_autocorr) <= 0.5)[0]
    decay_time = first_below_half[0] + 1 if len(first_below_half) > 0 else max_lag
    
    return {
        'mean_autocorr': mean_autocorr,
        'std_autocorr': std_autocorr,
        'persistence': persistence,
        'decay_time': decay_time
    }

def factor_target_relationship(data, factor, target):
    """分析因子与目标变量的非线性关系"""
    # 因子分组分析
    n_groups = 10
    try:
        # 尝试使用qcut，允许重复的边界值
        data['factor_quantile'] = pd.qcut(data[factor], n_groups, labels=False, duplicates='drop')
    except ValueError:
        # 如果还是失败，使用等距分组
        data['factor_quantile'] = pd.cut(data[factor], n_groups, labels=False)
    
    # 计算每组的统计量
    group_stats = data.groupby('factor_quantile').agg({
        target: ['mean', 'std', 'count'],
        factor: ['mean', 'min', 'max']
    }).round(4)
    
    # 计算单调性指标
    returns = group_stats[target]['mean'].values
    monotonicity = np.sum(np.diff(returns) > 0) / (len(returns) - 1)
    
    # 绘制分组收益图
    plt.figure(figsize=(15, 10))
    
    # 上图：分组平均收益
    plt.subplot(2, 1, 1)
    plt.errorbar(range(len(group_stats)), group_stats[target]['mean'], 
                yerr=group_stats[target]['std']/np.sqrt(group_stats[target]['count']),
                fmt='o-', capsize=5)
    plt.title(f'Factor Quantile Analysis: {factor}')
    plt.xlabel('Factor Quantile')
    plt.ylabel(f'Mean {target}')
    plt.grid(True, alpha=0.3)
    
    # 下图：因子值分布
    plt.subplot(2, 1, 2)
    sns.histplot(data=data, x=factor, bins=50, kde=True)
    plt.title(f'Factor Distribution: {factor}')
    plt.xlabel(factor)
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'factor_analysis_{factor}.png'))
    plt.close()
    
    return {
        'group_stats': group_stats,
        'monotonicity': monotonicity
    }

def analyze_factor_turnover(data, factor, window=30):
    """
    分析因子换手率
    """
    # 计算因子排序变化
    factor_rank = data.groupby('date')[factor].rank(pct=True)
    factor_rank_shift = factor_rank.shift(1)
    
    # 计算换手率
    turnover = abs(factor_rank - factor_rank_shift).mean()
    
    # 计算滚动换手率
    rolling_turnover = abs(factor_rank - factor_rank_shift).rolling(window).mean()
    
    # 绘制换手率时间序列
    plt.figure(figsize=(12, 6))
    plt.plot(data['DateTime'], rolling_turnover)
    plt.title(f'{factor}因子换手率')
    plt.xlabel('时间')
    plt.ylabel('换手率')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f'turnover_{factor}.png'))
    plt.close()
    
    return turnover

def analyze_factor_stability(data, factor, window=30):
    """
    分析因子稳定性
    """
    # 计算因子自相关系数
    lag_corrs = []
    for lag in range(1, window+1):
        corr = data[factor].corr(data[factor].shift(lag))
        lag_corrs.append(corr)
    
    # 绘制自相关衰减曲线
    plt.figure(figsize=(12, 6))
    plt.plot(range(1, window+1), lag_corrs)
    plt.title(f'{factor}因子稳定性分析')
    plt.xlabel('时间间隔（分钟）')
    plt.ylabel('自相关系数')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f'stability_{factor}.png'))
    plt.close()
    
    return lag_corrs

def analyze_factor_extremes(data, factor):
    """
    分析因子极值
    """
    # 计算因子分位数
    quantiles = np.percentile(data[factor].dropna(), 
                            [1, 5, 25, 50, 75, 95, 99])
    
    # 绘制箱线图
    plt.figure(figsize=(10, 6))
    plt.boxplot(data[factor].dropna())
    plt.title(f'{factor}因子分布')
    plt.ylabel('因子值')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f'distribution_{factor}.png'))
    plt.close()
    
    return {
        'quantiles': dict(zip(['1%', '5%', '25%', '50%', '75%', '95%', '99%'], 
                            quantiles))
    }

def analyze_factor_returns(data, factor, n_groups=5):
    """
    分析因子收益特征
    """
    # 按因子值分组，处理重复值
    try:
        data['factor_quantile'] = pd.qcut(data[factor], n_groups, 
                                        labels=False, duplicates='drop')
    except ValueError:
        data['factor_quantile'] = pd.cut(data[factor], n_groups, 
                                       labels=False)
    
    # 计算各组收益率
    group_returns = data.groupby('factor_quantile')['FutureReturn_1period'].mean()
    
    # 计算多空组合收益
    long_short_return = group_returns.iloc[-1] - group_returns.iloc[0]
    
    # 绘制分组收益图
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(group_returns)), group_returns)
    plt.title(f'{factor}因子分组收益分析')
    plt.xlabel('分组')
    plt.ylabel('平均收益率')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f'group_returns_{factor}.png'))
    plt.close()
    
    return {
        'group_returns': group_returns,
        'long_short_return': long_short_return
    }

def run_comprehensive_analysis(data, factors, target):
    """
    运行综合分析
    """
    results = {}
    
    for factor in factors:
        print(f"\n分析因子: {factor}")
        factor_results = {}
        
        # 1. 基础IC分析
        ic_result = calculate_ic(data, factor, target)
        factor_results['ic'] = ic_result
        
        # 2. 因子稳定性分析
        stability = analyze_factor_stability(data, factor)
        factor_results['stability'] = stability
        
        # 3. 因子换手率分析
        turnover = analyze_factor_turnover(data, factor)
        factor_results['turnover'] = turnover
        
        # 4. 因子极值分析
        extremes = analyze_factor_extremes(data, factor)
        factor_results['extremes'] = extremes
        
        # 5. 因子收益分析
        returns = analyze_factor_returns(data, factor)
        factor_results['returns'] = returns
        
        # 6. 衰减分析
        decay_df, decay_metrics = factor_decay_analysis(data, factor, 
                                                      target)
        factor_results['decay'] = decay_metrics
        
        results[factor] = factor_results
    
    return results

# 主分析流程
print("\n开始因子分析...")

# 数据预处理
processed_df = preprocess_data(df)

# 分析结果存储
all_results = []

for factor in factors:
    print(f"\n{'=' * 50}")
    print(f"分析因子: {factor}")
    print(f"{'=' * 50}")
    
    # 1. 计算因子IC
    if factor in ['信号量', '信号量_等级']:
        ic_result = calculate_ic(processed_df, factor, target, is_signal_analysis=True)
        print("\n分段IC分析结果:")
        for segment, results in ic_result.items():
            print(f"\n{segment} (样本量: {results['sample_size']}):")
            print(f"Pearson IC: {results['pearson_ic']:.4f} (p={results['pearson_p']:.4e})")
            print(f"Spearman IC: {results['spearman_ic']:.4f} (p={results['spearman_p']:.4e})")
            print(f"Kendall IC: {results['kendall_ic']:.4f} (p={results['kendall_p']:.4e})")
    else:
        ic_result = calculate_ic(processed_df, factor, target)
        print("\nIC分析结果:")
        print(f"样本量: {ic_result['sample_size']}")
        print(f"Pearson IC: {ic_result['pearson_ic']:.4f} (p={ic_result['pearson_p']:.4e})")
        print(f"Spearman IC: {ic_result['spearman_ic']:.4f} (p={ic_result['spearman_p']:.4e})")
        print(f"Kendall IC: {ic_result['kendall_ic']:.4f} (p={ic_result['kendall_p']:.4e})")
    
    # 2. 因子稳定性分析
    ic_ts, stability_metrics = daily_ic_analysis(processed_df, factor, target)
    print("\n稳定性分析结果:")
    for ic_type in ['pearson_ic', 'spearman_ic', 'kendall_ic']:
        print(f"\n{ic_type.split('_')[0]} IC:")
        print(f"Mean: {stability_metrics[f'mean_{ic_type}']:.4f}")
        print(f"IR: {stability_metrics[f'ir_{ic_type}']:.4f}")
        print(f"t-stat: {stability_metrics[f't_stat_{ic_type}']:.4f}")
        print(f"p-value: {stability_metrics[f'p_value_{ic_type}']:.4e}")
    
    # 3. 因子衰减分析
    decay_df, decay_metrics = factor_decay_analysis(processed_df, factor, target)
    print("\n衰减分析结果:")
    for ic_type in ['pearson_ic', 'spearman_ic', 'kendall_ic']:
        print(f"{ic_type.split('_')[0]} IC半衰期: {decay_metrics[f'{ic_type}_half_life']} minutes")
    
    # 4. 因子自相关性分析
    autocorr_results = factor_autocorrelation(processed_df, factor)
    print("\n自相关分析结果:")
    print(f"持续性: {autocorr_results['persistence']} minutes")
    print(f"衰减时间: {autocorr_results['decay_time']} minutes")
    
    # 5. 因子与目标变量关系分析
    relationship_results = factor_target_relationship(processed_df, factor, target)
    print("\n分组分析结果:")
    print(f"单调性: {relationship_results['monotonicity']:.4f}")
    
    # 6. 因子换手率分析
    turnover = analyze_factor_turnover(processed_df, factor)
    print(f"\n因子换手率: {turnover:.4f}")

    # 7. 因子稳定性分析 (滚动)
    stability = analyze_factor_stability(processed_df, factor)
    print(f"\n因子稳定性 (滚动): {stability}")

    # 8. 因子极值分析
    extremes = analyze_factor_extremes(processed_df, factor)
    print(f"\n因子极值: {extremes}")

    # 9. 因子收益分析
    returns = analyze_factor_returns(processed_df, factor)
    print(f"\n因子收益特征: {returns}")

    # 10. 综合分析 (所有因子)
    comprehensive_results = run_comprehensive_analysis(processed_df, factors, target)
    print(f"\n综合分析结果 (所有因子): {comprehensive_results}")
    
    # 汇总结果
    result = {
        'factor': factor,
        **ic_result,
        **{f'daily_{k}': v for k, v in stability_metrics.items()},
        **{f'decay_{k}': v for k, v in decay_metrics.items()},
        'autocorr_persistence': autocorr_results['persistence'],
        'autocorr_decay_time': autocorr_results['decay_time'],
        'monotonicity': relationship_results['monotonicity'],
        'turnover': turnover,
        'stability': stability,
        'extremes': extremes,
        'returns': returns,
        'comprehensive_results': comprehensive_results
    }
    all_results.append(result)

# 保存汇总结果
results_df = pd.DataFrame(all_results)
results_df.to_csv(os.path.join(output_dir, 'factor_analysis_summary.csv'), index=False)

# 生成因子性能对比图
plt.figure(figsize=(15, 10))

# IC对比图
plt.subplot(2, 1, 1)
ic_comparison = pd.DataFrame({
    'Pearson IC': results_df['pearson_ic'],
    'Spearman IC': results_df['spearman_ic'],
    'Kendall IC': results_df['kendall_ic']
}, index=results_df['factor'])
ic_comparison.plot(kind='bar', ax=plt.gca())
plt.title('Factor IC Comparison')
plt.xlabel('Factor')
plt.ylabel('Information Coefficient')
plt.legend()
plt.grid(True, alpha=0.3)

# IR对比图
plt.subplot(2, 1, 2)
ir_comparison = pd.DataFrame({
    'Pearson IR': results_df['daily_ir_pearson_ic'],
    'Spearman IR': results_df['daily_ir_spearman_ic'],
    'Kendall IR': results_df['daily_ir_kendall_ic']
}, index=results_df['factor'])
ir_comparison.plot(kind='bar', ax=plt.gca())
plt.title('Factor IR Comparison')
plt.xlabel('Factor')
plt.ylabel('Information Ratio')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'factor_performance_comparison.png'), dpi=300)
plt.close()

print("\n分析完成！所有结果已保存至:", output_dir)