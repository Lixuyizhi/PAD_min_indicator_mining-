#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载模块
负责加载和预处理回测数据
"""

import pandas as pd
import backtrader as bt
import re
import os

class SignalLevelData(bt.feeds.PandasData):
    """自定义数据源，包含信号量等级"""
    
    # 定义数据列
    lines = ('signal_level',)
    
    params = (
        ('datetime', None),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', None),
        ('signal_level', '信号量_等级'),
    )

class DataLoader:
    """数据加载器"""
    
    def __init__(self, data_path):
        """
        初始化数据加载器
        
        Parameters:
        data_path: str, 数据文件路径
        """
        self.data_path = data_path
        self.resample_rule = 'unknown'
        self.lag_minutes = 'unknown'
        
        # 从文件名提取信息
        self._extract_file_info()
    
    def _extract_file_info(self):
        """从文件名提取信息"""
        filename = os.path.basename(self.data_path)
        match = re.search(r'_([0-9a-zA-Z]+)_lag(\d+)min', filename)
        if match:
            self.resample_rule = match.group(1)
            self.lag_minutes = match.group(2)
    
    def load_data(self):
        """加载和预处理数据"""
        print(f"正在加载数据: {self.data_path}")
        
        # 读取数据
        df = pd.read_excel(self.data_path)
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        
        # 设置索引
        df.set_index('DateTime', inplace=True)
        
        # 确保必要的列存在
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume', '信号量_等级']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 处理缺失值
        df = df.dropna(subset=['信号量_等级', 'Close'])
        
        print(f"数据加载完成: {len(df)}行, {len(df.columns)}列")
        print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
        print(f"信号量等级范围: {df['信号量_等级'].min():.2f} - {df['信号量_等级'].max():.2f}")
        
        return df
    
    def get_backtrader_data(self):
        """获取backtrader格式的数据"""
        df = self.load_data()
        return SignalLevelData(dataname=df)
    
    def get_data_info(self):
        """获取数据基本信息"""
        return {
            'resample_rule': self.resample_rule,
            'lag_minutes': self.lag_minutes,
            'file_path': self.data_path
        } 