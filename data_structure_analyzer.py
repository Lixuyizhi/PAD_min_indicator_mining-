import pandas as pd
import os
from pathlib import Path

def analyze_data_structure():
    """分析futures_emo_combined_data文件夹下的数据文件结构"""
    data_dir = Path("futures_emo_combined_data")
    
    if not data_dir.exists():
        print("数据文件夹不存在")
        return
    
    # 获取所有Excel文件
    excel_files = list(data_dir.glob("*.xlsx"))
    
    print(f"找到 {len(excel_files)} 个Excel文件")
    print("=" * 50)
    
    # 分析前几个文件的结构
    for i, file_path in enumerate(excel_files[:3]):  # 只分析前3个文件
        print(f"\n分析文件 {i+1}: {file_path.name}")
        print("-" * 30)
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            print(f"数据形状: {df.shape}")
            print(f"列名: {list(df.columns)}")
            print(f"数据类型:")
            print(df.dtypes)
            
            print(f"\n前5行数据:")
            print(df.head())
            
            print(f"\n数据统计信息:")
            print(df.describe())
            
        except Exception as e:
            print(f"读取文件时出错: {e}")

if __name__ == "__main__":
    analyze_data_structure() 