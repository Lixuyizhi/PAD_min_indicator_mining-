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
START_YEAR = 2017
END_YEAR = 2025  # 设置为同一个年份表示只需要一年数据
RESAMPLE_RULE = '30min'  # 新增：聚合粒度，可选'1min'、'15min'、'30min'等


# ======================== 核心函数 ========================
def process_trading_day_time(df, resample_rule='1min'):
    """
    安全处理TradingDay(整数)和UpdateTime(字符串)的组合时间
    将时间处理到指定粒度
    """
    # 转换TradingDay为格式化的日期字符串
    df['TradingDayStr'] = df['TradingDay'].astype(str).apply(
        lambda x: f"{x[:4]}-{x[4:6]}-{x[6:8]}"
    )

    # 组合日期和时间，并将精度控制在指定粒度
    df['DateTime'] = pd.to_datetime(
        df['TradingDayStr'] + ' ' + df['UpdateTime'],
        format='%Y-%m-%d %H:%M:%S'
    ).dt.floor(resample_rule)  # 按指定粒度对齐

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


def process_tick_data(df, resample_rule='1min'):
    """
    将tick数据转换为指定粒度的数据
    优化后的逻辑：
    1. 确保时间连续性
    2. 正确处理成交量
    3. 计算关键价格指标
    """
    # 创建指定粒度的时间索引（不需要额外创建MinuteDT，因为DateTime已经是对齐后的）
    groups = df.groupby('DateTime')
    ohlc_data = []
    
    # 记录上一周期的最后成交量，用于计算真实周期成交量
    last_volume = None
    
    for period, group in tqdm(groups, desc=f"生成{resample_rule}数据"):
        if len(group) == 0:
            continue
            
        # 计算OHLCV
        current_volume = group['Volume'].iloc[-1]
        if last_volume is not None:
            period_volume = current_volume - last_volume
        else:
            period_volume = group['Volume'].iloc[-1] - group['Volume'].iloc[0]
        
        # 确保成交量非负
        period_volume = max(0, period_volume)
        
        # 计算加权平均价格（VWAP）
        if period_volume > 0:
            vwap = (group['LastPrice'] * group['Volume'].diff().fillna(0)).sum() / period_volume
        else:
            vwap = group['LastPrice'].mean()
            
        ohlc = {
            'DateTime': period,
            'Open': group['LastPrice'].iloc[0],
            'High': group['LastPrice'].max(),
            'Low': group['LastPrice'].min(),
            'Close': group['LastPrice'].iloc[-1],
            'VWAP': vwap,
            'Volume': period_volume,
            'OpenInterest': group['OpenInterest'].iloc[-1],
            'AskPrice1': group['AskPrice1'].iloc[-1],
            'AskVolume1': group['AskVolume1'].iloc[-1],
            'BidPrice1': group['BidPrice1'].iloc[-1],
            'BidVolume1': group['BidVolume1'].iloc[-1],
        }
        ohlc_data.append(ohlc)
        last_volume = current_volume
        
    period_df = pd.DataFrame(ohlc_data)
    
    # 计算关键价格指标
    period_df['MidPrice'] = (period_df['AskPrice1'] + period_df['BidPrice1']) / 2
    period_df['Spread'] = period_df['AskPrice1'] - period_df['BidPrice1']
    period_df['SpreadPct'] = period_df['Spread'] / period_df['MidPrice']
    
    # 计算买卖压力指标
    total_volume = period_df['AskVolume1'] + period_df['BidVolume1']
    period_df['BuyPressure'] = np.where(
        total_volume > 0,
        period_df['BidVolume1'] / total_volume,
        0.5
    )
    
    return period_df


def calculate_core_indicators(df):
    """
    只保留IC检验所需的核心行情指标
    """
    df = df.sort_values('DateTime').reset_index(drop=True)
    # 只保留Close、Volume等基础行情字段
    # 未来收益率在主函数中添加
    return df


# ======================== 主处理函数 ========================
def generate_features(input_file, output_file=None, resample_rule='1min'):
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
    df = process_trading_day_time(raw_df, resample_rule)  # 这里已经将时间处理到指定粒度
    df = enforce_numeric(df)
    df = filter_by_year(df, START_YEAR, END_YEAR)
    
    # 生成指定粒度数据
    period_df = process_tick_data(df, resample_rule)
    
    # 添加时间特征
    period_df['Hour'] = period_df['DateTime'].dt.hour
    period_df['Minute'] = period_df['DateTime'].dt.minute
    
    # 精简后的行情指标，
    final_df = calculate_core_indicators(period_df)
    
    # 只保留核心字段
    keep_cols = ['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest',
                 ]
    final_df = final_df[keep_cols]
    
    # 添加未来收益率（用于后续IC分析）
    final_df['FutureReturn_1period'] = final_df['Close'].shift(-1) / final_df['Close'] - 1
    final_df['FutureReturn_5period'] = final_df['Close'].shift(-5) / final_df['Close'] - 1
    
    # 保存结果
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 将DateTime列格式化为字符串
        final_df['DateTime'] = final_df['DateTime'].dt.strftime('%Y/%m/%d %H:%M')
        
        # 根据文件扩展名选择保存格式
        if output_file.endswith('.xlsx'):
            print(f"正在保存为Excel格式: {output_file}")
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name=f'{resample_rule}数据')
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
    output_file = f"./futures_data/sc2210_major_contracts_{START_YEAR}_{RESAMPLE_RULE}.xlsx"
    
    print("=" * 70)
    print(f"开始处理 {START_YEAR} 年数据并生成技术指标特征（{RESAMPLE_RULE} 粒度）")
    print("=" * 70)
    
    result_df = generate_features(input_file, output_file, resample_rule=RESAMPLE_RULE)