import pandas as pd
import numpy as np
import re
import tqdm
from tqdm import tqdm
import warnings
import datetime
import os

warnings.filterwarnings('ignore')

# ======================== 配置参数 ========================
# 可以在这里设置时间范围
START_YEAR = 2024
END_YEAR = 2024  # 设置为同一个年份表示只需要一年数据


# ======================== 核心函数 ========================
def process_trading_day_time(df):
    """
    安全处理TradingDay(整数)和UpdateTime(字符串)的组合时间
    将时间处理到分钟级别
    """
    # 转换TradingDay为格式化的日期字符串
    df['TradingDayStr'] = df['TradingDay'].astype(str).apply(
        lambda x: f"{x[:4]}-{x[4:6]}-{x[6:8]}"
    )

    # 组合日期和时间，并将精度控制在分钟级别
    df['DateTime'] = pd.to_datetime(
        df['TradingDayStr'] + ' ' + df['UpdateTime'],
        format='%Y-%m-%d %H:%M:%S'
    ).dt.floor('min')  # 将时间向下取整到分钟

    # 添加年份列用于过滤
    df['Year'] = df['DateTime'].dt.year
    return df


def enforce_numeric(df):
    """确保所有数值列都是真正的数字类型，使用显式类型转换"""
    print("确保数据列类型正确...")

    # 数值列显式类型转换
    df['LastPrice'] = df['LastPrice'].astype(float)
    df['Volume'] = df['Volume'].astype('int64')
    df['OpenInterest'] = df['OpenInterest'].astype('int64')
    df['AskPrice1'] = df['AskPrice1'].astype(float)
    df['AskVolume1'] = df['AskVolume1'].astype('int64')
    df['BidPrice1'] = df['BidPrice1'].astype(float)
    df['BidVolume1'] = df['BidVolume1'].astype('int64')

    return df


def filter_by_year(df, start_year, end_year):
    """根据年份过滤数据"""
    print(f"筛选 {start_year}-{end_year} 年数据...")

    # 筛选指定年份范围的数据
    filtered_df = df[(df['Year'] >= start_year) & (df['Year'] <= end_year)].copy()
    filtered_df.reset_index(drop=True, inplace=True)

    print(f"筛选后数据量: {len(filtered_df)} 行 (原数据量: {len(df)} 行)")
    return filtered_df


def process_tick_data(df):
    """
    将tick数据转换为分钟级数据
    优化后的逻辑：
    1. 确保时间连续性
    2. 正确处理成交量
    3. 计算关键价格指标
    """
    # 创建分钟时间索引（不需要额外创建MinuteDT，因为DateTime已经是分钟级别）
    groups = df.groupby('DateTime')
    ohlc_data = []
    
    # 记录上一分钟的最后成交量，用于计算真实分钟成交量
    last_volume = None
    
    for minute, group in tqdm(groups, desc="生成分钟数据"):
        if len(group) == 0:
            continue
            
        # 计算OHLCV
        current_volume = group['Volume'].iloc[-1]
        if last_volume is not None:
            minute_volume = current_volume - last_volume
        else:
            minute_volume = group['Volume'].iloc[-1] - group['Volume'].iloc[0]
        
        # 确保成交量非负
        minute_volume = max(0, minute_volume)
        
        # 计算加权平均价格（VWAP）
        if minute_volume > 0:
            vwap = (group['LastPrice'] * group['Volume'].diff().fillna(0)).sum() / minute_volume
        else:
            vwap = group['LastPrice'].mean()
            
        ohlc = {
            'DateTime': minute,
            'Open': group['LastPrice'].iloc[0],
            'High': group['LastPrice'].max(),
            'Low': group['LastPrice'].min(),
            'Close': group['LastPrice'].iloc[-1],
            'VWAP': vwap,
            'Volume': minute_volume,
            'OpenInterest': group['OpenInterest'].iloc[-1],
            'AskPrice1': group['AskPrice1'].iloc[-1],
            'AskVolume1': group['AskVolume1'].iloc[-1],
            'BidPrice1': group['BidPrice1'].iloc[-1],
            'BidVolume1': group['BidVolume1'].iloc[-1],
        }
        ohlc_data.append(ohlc)
        last_volume = current_volume
        
    minute_df = pd.DataFrame(ohlc_data)
    
    # 计算关键价格指标
    minute_df['MidPrice'] = (minute_df['AskPrice1'] + minute_df['BidPrice1']) / 2
    minute_df['Spread'] = minute_df['AskPrice1'] - minute_df['BidPrice1']
    minute_df['SpreadPct'] = minute_df['Spread'] / minute_df['MidPrice']
    
    # 计算买卖压力指标
    total_volume = minute_df['AskVolume1'] + minute_df['BidVolume1']
    minute_df['BuyPressure'] = np.where(
        total_volume > 0,
        minute_df['BidVolume1'] / total_volume,
        0.5
    )
    
    return minute_df


def calculate_core_indicators(df):
    """
    计算核心技术指标
    保留与情绪相关的重要指标
    """
    df = df.sort_values('DateTime').reset_index(drop=True)
    
    # 1. 价格动量指标
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=10).std()
    
    # 2. 成交量指标
    df['VolumeMA5'] = df['Volume'].rolling(window=5).mean()
    df['VolumePct'] = df['Volume'] / df['VolumeMA5'] - 1
    
    # 3. 买卖压力指标
    df['PressureMA5'] = df['BuyPressure'].rolling(window=5).mean()
    df['PressureChange'] = df['BuyPressure'] - df['PressureMA5']
    
    # 4. 价差指标
    df['SpreadMA5'] = df['SpreadPct'].rolling(window=5).mean()
    df['SpreadChange'] = df['SpreadPct'] - df['SpreadMA5']
    
    # 5. 波动率指标
    df['VolatilityMA5'] = df['Volatility'].rolling(window=5).mean()
    df['VolatilityChange'] = df['Volatility'] / df['VolatilityMA5'] - 1
    
    # 填充缺失值
    df.fillna(0, inplace=True)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    
    return df


# ======================== 主处理函数 ========================
def generate_features(input_file, output_file=None):
    """特征生成主函数"""
    start_time = datetime.datetime.now()
    print(f"开始处理数据: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 读取数据
    if input_file.endswith('.parquet'):
        raw_df = pd.read_parquet(input_file)
    elif input_file.endswith('.csv'):
        raw_df = pd.read_csv(input_file)
    else:
        raise ValueError("不支持的文件格式，请提供.csv或.parquet文件")
    
    # 数据预处理
    df = process_trading_day_time(raw_df)  # 这里已经将时间处理到分钟级别
    df = enforce_numeric(df)
    df = filter_by_year(df, START_YEAR, END_YEAR)
    
    # 生成分钟数据
    minute_df = process_tick_data(df)
    
    # 添加时间特征
    minute_df['Hour'] = minute_df['DateTime'].dt.hour
    minute_df['Minute'] = minute_df['DateTime'].dt.minute
    
    # 计算技术指标
    final_df = calculate_core_indicators(minute_df)
    
    # 添加未来收益率（用于后续分析）
    final_df['FutureReturn_1min'] = final_df['Close'].shift(-1) / final_df['Close'] - 1
    final_df['FutureReturn_5min'] = final_df['Close'].shift(-5) / final_df['Close'] - 1
    
    # 保存结果
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 将DateTime列格式化为分钟级别的字符串
        final_df['DateTime'] = final_df['DateTime'].dt.strftime('%Y/%m/%d %H:%M')
        
        # 根据文件扩展名选择保存格式
        if output_file.endswith('.xlsx'):
            print(f"正在保存为Excel格式: {output_file}")
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='分钟数据')
        elif output_file.endswith('.parquet'):
            print(f"正在保存为Parquet格式: {output_file}")
            final_df.to_parquet(output_file, index=False)
        else:
            print(f"正在保存为CSV格式: {output_file}")
            final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
        print(f"数据已保存至: {output_file}")
    
    # 输出处理统计
    end_time = datetime.datetime.now()
    print(f"\n处理完成! 耗时: {end_time - start_time}")
    print(f"数据范围: {final_df['DateTime'].min()} 至 {final_df['DateTime'].max()}")
    print(f"总数据点: {len(final_df)}")
    print(f"特征数量: {len(final_df.columns)}")
    print("\n核心特征列表:")
    for col in final_df.columns:
        print(f"- {col}")
    
    return final_df


# ======================== 使用示例 ========================
if __name__ == "__main__":
    input_file = "./futures_data/sc2210_major_contracts.csv"
    output_file = f"./futures_data/sc2210_major_contracts_{START_YEAR}_min.xlsx"
    
    print("=" * 70)
    print(f"开始处理 {START_YEAR} 年数据并生成技术指标特征")
    print("=" * 70)
    
    result_df = generate_features(input_file, output_file)