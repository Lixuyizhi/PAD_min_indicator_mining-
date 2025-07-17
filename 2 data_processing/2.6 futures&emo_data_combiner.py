import pandas as pd
import os

# 可配置参数
LAG_MINUTES = 1  # 滞后时间（分钟）
OUTPUT_PATH = f"../futures_emo_combined_data/sc2210_with_emotion_lag{LAG_MINUTES}min.xlsx"
EMOTION_COLUMNS = ['极性', '强度', '支配维度', '信号量', '信号量_等级']  # 选择需要合并的情绪特征列

# 确保输出目录存在
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def merge_data_with_lag(futures_path, emotion_path, lag_minutes=LAG_MINUTES):
    """
    核心合并函数：期货数据 + 滞后情绪数据
    """
    # 1. 读取期货数据
    print(f"正在读取期货数据: {futures_path}...")
    try:
        if futures_path.endswith('.parquet'):
            df_futures = pd.read_parquet(futures_path)
        else:
            df_futures = pd.read_excel(futures_path)
        df_futures['DateTime'] = pd.to_datetime(df_futures['DateTime'])
        print(f"期货数据读取完成: {len(df_futures)}行")
    except Exception as e:
        print(f"读取期货数据时出错: {str(e)}")
        return None
    
    # 2. 读取情绪数据
    print(f"正在读取情绪数据: {emotion_path}...")
    try:
        df_emotion = pd.read_excel(emotion_path)
        df_emotion['DateTime'] = pd.to_datetime(df_emotion['时间点'])  # 使用原时间点列
        print(f"情绪数据读取完成: {len(df_emotion)}行")
    except Exception as e:
        print(f"读取情绪数据时出错: {str(e)}")
        return None
    
    # 3. 应用滞后处理
    print(f"应用 {lag_minutes} 分钟滞后处理...")
    df_emotion_lagged = df_emotion.copy()
    df_emotion_lagged['DateTime_lagged'] = df_emotion_lagged['DateTime'] + pd.Timedelta(minutes=lag_minutes)
    
    # 4. 合并数据
    merged_df = pd.merge(
        df_futures,
        df_emotion_lagged[['DateTime_lagged'] + EMOTION_COLUMNS],
        left_on='DateTime',
        right_on='DateTime_lagged',
        how='left'
    )
    
    # 移除辅助列
    merged_df.drop(columns=['DateTime_lagged'], inplace=True, errors='ignore')
    
    # 5. 处理结果
    print("\n合并结果统计:")
    print(f"合并后总行数: {len(merged_df)}")
    
    # 检查情绪列的缺失情况
    for col in EMOTION_COLUMNS:
        na_count = merged_df[col].isna().sum()
        print(f"{col}缺失值: {na_count}行 ({na_count/len(merged_df):.2%})")
    
    print(f"最早时间: {merged_df['DateTime'].min()}")
    print(f"最晚时间: {merged_df['DateTime'].max()}")
    
    return merged_df

if __name__ == "__main__":
    # 文件路径
    FUTURES_PATH = "../futures_data/sc2210_major_contracts_2024_min.xlsx"
    EMOTION_PATH = "../emo_data/emo_signals/SC_combined_情绪信号.xlsx"
    
    # 执行合并
    result_df = merge_data_with_lag(FUTURES_PATH, EMOTION_PATH, LAG_MINUTES)
    
    if result_df is not None:
        # 保存结果
        print(f"\n保存合并数据到: {OUTPUT_PATH}")
        try:
            result_df.to_excel(OUTPUT_PATH, index=False)
            print("保存成功！")
            
            # 简要分析结果
            print("\n最终数据集统计摘要:")
            print(f"行数: {len(result_df)}")
            print(f"列数: {len(result_df.columns)}")
            print(f"包含的情绪列: {', '.join([col for col in EMOTION_COLUMNS if col in result_df.columns])}")
            
            # 检查特定时间点的合并情况（可选）
            sample_time = result_df['DateTime'].iloc[0]  # 取第一个时间点
            sample_row = result_df[result_df['DateTime'] == sample_time].iloc[0]
            print("\n示例时间点合并结果:")
            print(f"时间点: {sample_time}")
            for col in EMOTION_COLUMNS:
                if col in sample_row:
                    print(f"{col}: {sample_row[col]}")
        except Exception as e:
            print(f"保存数据时出错: {str(e)}")
    else:
        print("数据处理失败，请检查输入文件和错误信息。")