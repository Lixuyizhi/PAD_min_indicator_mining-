import pandas as pd
import numpy as np
from pathlib import Path
import backtrader as bt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class EmotionDataLoader:
    """情绪数据加载器"""
    
    def __init__(self, data_dir="./futures_emo_combined_data"):
        self.data_dir = Path(data_dir)
        
    def load_data(self, filename):
        """加载指定的数据文件"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 确保DateTime列是datetime类型
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        
        # 设置DateTime为索引
        df.set_index('DateTime', inplace=True)
        
        # 按时间排序
        df.sort_index(inplace=True)
        
        return df
    
    def get_available_files(self):
        """获取所有可用的数据文件"""
        excel_files = list(self.data_dir.glob("*.xlsx"))
        return [f.name for f in excel_files]
    
    def get_file_info(self, filename):
        """获取文件信息"""
        df = self.load_data(filename)
        info = {
            'filename': filename,
            'shape': df.shape,
            'date_range': (df.index.min(), df.index.max()),
            'columns': list(df.columns),
            'sample_data': df.head(3)
        }
        return info

class BacktraderDataAdapter:
    """将pandas数据适配为backtrader格式"""
    
    @staticmethod
    def create_data_feed(df, name="emotion_data"):
        """创建backtrader数据源"""
        # 创建数据源
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 使用索引作为时间
            open='Open',
            high='High', 
            low='Low',
            close='Close',
            volume='Volume',
            openinterest='OpenInterest',
            name=name
        )
        
        # 添加情绪指标作为数据属性
        if '极性' in df.columns:
            data.极性 = df['极性'].values
        if '强度' in df.columns:
            data.强度 = df['强度'].values
        if '支配维度' in df.columns:
            data.支配维度 = df['支配维度'].values
        if '信号量' in df.columns:
            data.信号量 = df['信号量'].values
        if '信号量_等级' in df.columns:
            data.信号量_等级 = df['信号量_等级'].values
            
        return data
    
    @staticmethod
    def add_emotion_indicators(df):
        """添加情绪指标到数据中"""
        # 确保所有情绪指标列存在
        emotion_cols = ['极性', '强度', '支配维度', '信号量', '信号量_等级']
        
        for col in emotion_cols:
            if col not in df.columns:
                df[col] = 0.0
        
        return df

def load_and_prepare_data(filename, data_dir="./futures_emo_combined_data"):
    """加载并准备数据用于回测"""
    loader = EmotionDataLoader(data_dir)
    df = loader.load_data(filename)
    
    # 添加情绪指标
    df = BacktraderDataAdapter.add_emotion_indicators(df)
    
    # 创建backtrader数据源
    data_feed = BacktraderDataAdapter.create_data_feed(df)
    
    return df, data_feed

if __name__ == "__main__":
    # 测试数据加载
    loader = EmotionDataLoader()
    
    print("可用的数据文件:")
    files = loader.get_available_files()
    for i, file in enumerate(files[:5]):  # 只显示前5个
        print(f"{i+1}. {file}")
    
    if files:
        print(f"\n分析第一个文件: {files[0]}")
        info = loader.get_file_info(files[0])
        print(f"数据形状: {info['shape']}")
        print(f"时间范围: {info['date_range']}")
        print(f"列名: {info['columns']}") 