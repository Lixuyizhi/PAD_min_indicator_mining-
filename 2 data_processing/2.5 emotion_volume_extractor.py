import pandas as pd
import numpy as np
import os

def normalize_pad_values(df):
    """
    归一化PAD值到标准范围
    极性: [-100, 100] -> [-1, 1]
    强度: [0, 100] -> [0, 1]
    支配度: [-100, 100] -> [-1, 1]
    """
    df_normalized = df.copy()
    
    # 极性归一化
    df_normalized['极性'] = df['极性'] / 100
    
    # 强度归一化
    df_normalized['强度'] = df['强度'] / 100
    
    # 支配度归一化
    df_normalized['支配维度'] = df['支配维度'] / 100
    
    return df_normalized

def calculate_emotion_signal(pad_values, emotion_pad_matrix):
    """
    计算情绪信号量
    
    参数:
    pad_values: 归一化后的PAD值 [-1,1]范围
    emotion_pad_matrix: 标准情绪PAD矩阵
    
    返回:
    signal: 情绪信号量 [-100,100]范围
    """
    # 计算与每种基准情绪的相似度
    similarities = np.dot(pad_values, emotion_pad_matrix.T)
    
    # 将相似度转换为权重（使用softmax）
    def softmax(x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    weights = softmax(similarities)
    
    # 定义情绪基准值（与PAD矩阵顺序对应）
    emotion_values = np.array([
        100,   # 喜悦
        80,    # 兴奋
        60,    # 平静
        40,    # 惊讶
        20,    # 放松
        0,     # 疲倦
        -20,   # 悲伤
        -40,   # 焦虑
        -60,   # 愤怒
        -70,   # 恐惧
        -80,   # 厌恶
        -90,   # 鄙视
        -95,   # 失望
        -100   # 沮丧
    ])
    
    # 计算加权信号量
    signal = np.sum(weights * emotion_values.reshape(1, -1), axis=1)
    
    # 调整极性的影响
    pad_polarity = pad_values[:, 0]  # 极性值
    signal = signal * (1 + pad_polarity * 0.2)  # 极性对信号量有20%的调节作用
    
    # 确保信号量在[-100, 100]范围内
    signal = np.clip(signal, -100, 100)
    
    return signal

def calculate_signal_level(signal_values):
    """
    计算信号量等级（0-10）
    0表示最悲观，10表示最乐观
    
    参数:
    signal_values: 信号量数组 [-100,100]范围
    
    返回:
    levels: 信号量等级数组 [0,10]范围
    """
    # 将信号量从[-100,100]映射到[0,10]
    levels = (signal_values + 100) / 20
    # 四舍五入到整数
    levels = np.round(levels)
    # 确保范围在[0,10]
    levels = np.clip(levels, 0, 10)
    return levels.astype(int)

def process_emotion_signals(input_file, output_file):
    """处理情绪信号数据"""
    # 定义PAD矩阵（基于标准化的情绪空间）
    PAD = np.array([
        [0.85, 0.80, 0.85],    # 喜悦
        [0.75, 0.70, 0.80],    # 兴奋
        [0.65, -0.35, 0.60],   # 平静
        [0.50, 0.85, 0.20],    # 惊讶
        [0.45, -0.40, 0.25],   # 放松
        [0.20, -0.45, -0.70],  # 疲倦
        [-0.25, -0.65, -0.45], # 悲伤
        [-0.35, 0.15, -0.35],  # 焦虑
        [-0.40, 0.65, -0.30],  # 愤怒
        [-0.45, 0.20, -0.30],  # 恐惧
        [-0.70, 0.20, 0.50],   # 厌恶
        [-0.80, 0.25, 0.35],   # 鄙视
        [-0.85, 0.55, 0.30],   # 失望
        [-0.90, 0.50, 0.55]    # 沮丧
    ])

    try:
        # 读取数据
        df = pd.read_excel(input_file)
        print(f"\n处理文件: {os.path.basename(input_file)}")
        print(f"原始数据行数: {len(df)}")
        
        # 归一化PAD值
        normalized_df = normalize_pad_values(df)
        pad_values = normalized_df[['极性', '强度', '支配维度']].values
        
        # 计算信号量
        signal = calculate_emotion_signal(pad_values, PAD)
        df['信号量'] = signal
        
        # 计算信号量等级
        df['信号量_等级'] = calculate_signal_level(signal)
        
        # 格式化时间列
        if '时间点' in df.columns:
            df['时间点'] = pd.to_datetime(df['时间点']).dt.strftime('%Y/%m/%d %H:%M')
        
        # 保存结果
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_excel(output_file, index=False)
        
        # 输出统计信息
        print("\n数据统计:")
        print("\n信号量统计:")
        print(df['信号量'].describe())
        print("\n信号量等级分布:")
        print(df['信号量_等级'].value_counts().sort_index())
        
        # 保存统计信息
        stats_file = output_file.replace('.xlsx', '_统计.xlsx')
        stats_df = pd.DataFrame({
            '统计指标': ['数据行数', '信号量_最小值', '信号量_最大值', '信号量_均值', '信号量_中位数', '信号量_标准差',
                     '最常见信号等级', '信号等级_均值'],
            '数值': [
                len(df),
                df['信号量'].min(),
                df['信号量'].max(),
                df['信号量'].mean(),
                df['信号量'].median(),
                df['信号量'].std(),
                df['信号量_等级'].mode().iloc[0],
                df['信号量_等级'].mean()
            ]
        })
        stats_df.to_excel(stats_file, index=False)
        
        print(f"\n结果已保存至: {output_file}")
        print(f"统计信息已保存至: {stats_file}")
        
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    input_dir = '../emo_data/emo_PAD_completed'
    output_dir = '../emo_data/emo_signals'
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理completed文件夹下的所有xlsx文件
    for file in os.listdir(input_dir):
        if file.endswith('.xlsx') and not file.endswith('_统计.xlsx'):
            input_file = os.path.join(input_dir, file)
            output_file = os.path.join(output_dir, file.replace('情绪补全', '情绪信号'))
            process_emotion_signals(input_file, output_file)

if __name__ == "__main__":
    print("开始处理情绪信号数据...")
    print("="*50)
    main()
    print("\n处理完成！")