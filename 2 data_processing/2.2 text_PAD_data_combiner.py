import os
import pandas as pd
from pathlib import Path
import numpy as np

def process_selected_files(input_folder, selected_files=None, resample_rule='15min'):
    """
    处理用户选择的多个Excel文件，按指定时间粒度合并情绪数据
    采用加权方案处理同一时间窗口内的多个情绪值
    
    Args:
        input_folder: 输入文件夹路径
        selected_files: 要处理的文件列表，None表示处理所有符合条件的文件
        resample_rule: 时间粒度，如'1min', '5min', '15min', '30min', '1H'等
    """
    # 配置输出路径
    output_folder = input_folder
    output_file = output_folder / f'AG_combined_评论分析结果_{resample_rule}.xlsx'

    # 确保输出文件夹存在
    output_folder.mkdir(parents=True, exist_ok=True)

    # 存储所有数据内容的列表
    all_data = []

    print(f"开始处理文件夹: {input_folder}")
    print("-" * 50)

    file_count = 0
    total_rows = 0
    error_files = []
    processed_files = []

    # 精确指定数据类型
    dtypes = {
        '时间点': str,
        '极性': float,
        '强度': float,
        '支配维度': float
    }

    # 获取要处理的文件列表
    if selected_files is None:
        files_to_process = list(input_folder.glob('*评论分析结果.xlsx'))
        print("将处理文件夹中的所有符合条件的文件")
    else:
        files_to_process = [input_folder / f for f in selected_files]
        print(f"将处理用户指定的 {len(files_to_process)} 个文件")

    # 遍历选择的文件
    for file_path in files_to_process:
        try:
            if not file_path.exists():
                print(f"文件不存在: {file_path.name}，跳过处理")
                error_files.append((file_path.name, "文件不存在"))
                continue

            future_name = file_path.stem.replace('_评论分析结果', '')
            df = pd.read_excel(file_path, dtype=dtypes)
            
            
            
            # 计算情绪强度（用于加权）
            df['情绪强度'] = np.abs(df['极性']) * df['强度']
            
            file_row_count = len(df)
            print(f"成功读取: {file_path.name} (数据行: {file_row_count})")
            all_data.append(df)
            file_count += 1
            total_rows += file_row_count
            processed_files.append(file_path.name)

        except Exception as e:
            error_message = str(e)
            print(f"读取失败: {file_path.name} | 错误: {error_message}")
            error_files.append((file_path.name, error_message))

    if not all_data:
        print("错误: 未找到任何有效Excel文件！")
        return

    print("-" * 50)
    print(f"找到 {file_count} 个有效文件，总共 {total_rows} 行数据，正在合并...")

    # 合并所有数据
    combined_df = pd.concat(all_data, ignore_index=True)

    # 转换时间列为datetime类型
    combined_df['时间点'] = pd.to_datetime(combined_df['时间点'])
    
    # 将时间规整到指定粒度
    combined_df['时间窗口'] = combined_df['时间点'].dt.floor(resample_rule)

    print(f"\n正在处理相同{resample_rule}时间窗口的数据...")
    
    # 定义加权聚合函数
    def weighted_emotion_agg(group):
        """
        加权聚合函数
        极性范围: [-100, 100]
        强度范围: [0, 100]
        支配维度范围: [-100, 100]
        """
        # 使用情绪强度作为权重
        weights = np.abs(group['极性']) * group['强度']
        
        # 确保权重非负
        weights = np.where(weights < 0, 0, weights)
        weights = np.where(np.isnan(weights), 0, weights)
        
        # 如果所有权重为0，使用等权重
        if weights.sum() == 0:
            weights = np.ones_like(weights)
            
        # 计算加权平均
        weighted_polarity = np.average(group['极性'], weights=weights)
        weighted_intensity = np.average(group['强度'], weights=weights)
        weighted_dominance = np.average(group['支配维度'], weights=weights)
        
        # 确保值在指定范围内
        weighted_polarity = np.clip(weighted_polarity, -100, 100)
        weighted_intensity = np.clip(weighted_intensity, 0, 100)
        weighted_dominance = np.clip(weighted_dominance, -100, 100)
        
        return pd.Series({
            '极性': weighted_polarity,
            '强度': weighted_intensity,
            '支配维度': weighted_dominance
        })

    # 按时间窗口分组并应用加权聚合
    combined_df = combined_df.groupby('时间窗口').apply(weighted_emotion_agg).reset_index()
    
    # 重命名时间列并格式化
    combined_df = combined_df.rename(columns={'时间窗口': '时间点'})
    combined_df['时间点'] = combined_df['时间点'].dt.strftime('%Y/%m/%d %H:%M')
    
    # 重新排列列顺序
    columns_order = ['时间点', '极性', '强度', '支配维度']
    combined_df = combined_df[columns_order]

    # 保存结果
    try:
        combined_df.to_excel(output_file, index=False)
        print(f"数据已保存到: {output_file}")
        print(f"使用的时间粒度: {resample_rule}")
        
        # 验证PAD值范围
        print("\nPAD值范围验证:")
        for col in ['极性', '强度', '支配维度']:
            min_val = combined_df[col].min()
            max_val = combined_df[col].max()
            print(f"- {col}: [{min_val:.2f}, {max_val:.2f}]")
            
    except Exception as e:
        print(f"保存文件失败: {e}")

    return combined_df

if __name__ == "__main__":
    input_folder = Path('./emo_data/emo_PAD')
    selected_files = [
        "AG_评论分析结果.xlsx",
        # 添加更多需要处理的文件名...
    ]
    
    # 可以根据需要修改时间粒度
    # 常用选项: '1min', '5min', '15min', '30min', '1H', '2H', '4H'
    resample_rule = '1h'  # 默认1分钟，可以根据需要修改

    process_selected_files(input_folder, selected_files, resample_rule)