import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import os
import warnings

# 过滤警告
warnings.filterwarnings('ignore')

def is_trading_day(dt):
    """
    判断是否为交易日
    
    规则：
    1. 周末（周六、周日）为非交易日
    2. 后续可以添加法定节假日的判断
    """
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    # 周末为非交易日
    if dt.weekday() >= 5:  # 5是周六，6是周日
        return False
    # TODO: 这里可以添加法定节假日的判断逻辑
    return True

def get_period_type(dt):
    """
    获取时间段类型，根据不同时段特点划分
    
    时段划分依据：
    1. 开盘前 (pre_open): 8:30-9:00，为开盘做准备
    2. 早盘 (morning): 9:00-11:30，早盘交易时段
    3. 午休 (break): 11:30-13:30，市场休市
    4. 午盘 (afternoon): 13:30-15:00，午盘交易时段
    5. 收盘后 (post_close): 15:00-21:00，日盘收盘到夜盘开盘
    6. 夜盘 (night): 21:00-23:00，夜盘交易时段
    7. 隔夜 (overnight): 23:00-次日8:30，夜盘收盘到次日开盘
    8. 非交易日 (non_trading): 非交易日的所有时段
    """
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    
    # 首先判断是否为交易日
    if not is_trading_day(dt):
        return 'non_trading'
        
    current_time = dt.time()
    
    if time(8, 30) <= current_time < time(9, 0):
        return 'pre_open'
    elif time(9, 0) <= current_time <= time(11, 30):
        return 'morning'
    elif time(11, 30) < current_time < time(13, 30):
        return 'break'
    elif time(13, 30) <= current_time <= time(15, 0):
        return 'afternoon'
    elif time(15, 0) < current_time < time(21, 0):
        return 'post_close'
    elif time(21, 0) <= current_time <= time(23, 0):
        return 'night'
    elif time(23, 0) < current_time < time(0, 0) or time(0, 0) <= current_time < time(8, 30):
        return 'overnight'
    else:
        return 'other'

def calculate_emotion_decay(prev_value, current_value, minutes, period_type):
    """
    计算情绪衰减值
    
    衰减策略：
    1. 使用指数衰减模型: value = prev_value * exp(-decay_rate * minutes)
    2. 不同时段采用不同衰减率，反映市场活跃度
    3. 新旧情绪融合采用动态权重
    4. 非交易日衰减更慢
    """
    decay_rates = {
        'pre_open': 0.0015,    # 开盘前情绪较为稳定
        'morning': 0.0025,     # 早盘情绪衰减较快
        'break': 0.0008,       # 午休期间情绪衰减缓慢
        'afternoon': 0.0020,   # 午盘情绪衰减适中
        'post_close': 0.0015,  # 收盘后情绪衰减适中（调整为与pre_open相同）
        'night': 0.0015,       # 夜盘情绪衰减中等
        'overnight': 0.0003,   # 隔夜情绪衰减最慢
        'non_trading': 0.0002, # 非交易日情绪衰减最慢
        'other': 0.0004        # 其他时段保守处理
    }
    
    decay_rate = decay_rates.get(period_type, 0.001)
    
    # 非交易日的情绪衰减更慢
    if period_type == 'non_trading':
        decay_rate *= 0.5
    
    # 添加平滑过渡机制，避免时段切换时的骤变
    # 对于短时间间隔（如15分钟），使用更保守的衰减率
    if minutes <= 30:  # 30分钟内的短时间间隔
        decay_rate *= 0.7  # 降低衰减率，使过渡更平滑
        
    decayed_value = prev_value * np.exp(-decay_rate * minutes)
    
    if pd.notna(current_value):
        # 动态权重：时间间隔越长，新情绪权重越大
        decay_weight = np.exp(-0.05 * minutes)  # 基础衰减权重
        time_factor = min(0.8, 0.2 * np.log1p(minutes))  # 时间因子，限制最大值
        
        # 非交易日的新情绪权重调整
        if period_type == 'non_trading':
            time_factor *= 1.2  # 非交易日新情绪影响略微增加
            
        combined_value = (decayed_value * decay_weight + 
                        current_value * (1 - decay_weight + time_factor))
        return combined_value
    else:
        return decayed_value

def calculate_emotion_accumulation(prev_value, current_value, minutes, period_type):
    """
    计算情绪积累值
    
    积累策略：
    1. 使用对数增长模型，体现边际递减效应
    2. 不同时段有不同积累系数
    3. 考虑新情绪的影响
    4. 非交易日积累更慢但更持久
    """
    accumulation_factors = {
        'pre_open': 0.012,     # 开盘前积累适中（降低）
        'overnight': 0.006,    # 隔夜积累最慢
        'break': 0.010,        # 午休期间积累适中（降低）
        'non_trading': 0.008,  # 非交易日积累缓慢但持久
        'other': 0.004         # 其他时段保守积累
    }
    
    factor = accumulation_factors.get(period_type, 0.01)
    
    # 非交易日的积累更持久
    if period_type == 'non_trading':
        factor *= 0.8  # 降低积累速度
        minutes = minutes * 0.7  # 降低时间影响
    
    # 添加平滑机制，避免短时间内的过度积累
    if minutes <= 30:  # 30分钟内的短时间间隔
        factor *= 0.6  # 降低积累因子，使过渡更平滑
        
    base_accumulation = prev_value * (1 + factor * np.log1p(minutes))
    
    if pd.notna(current_value):
        # 积累权重随时间增加但有上限
        accumulation_weight = min(0.6, 0.15 * np.log1p(minutes))
        
        # 非交易日的新情绪权重调整
        if period_type == 'non_trading':
            accumulation_weight = min(0.7, accumulation_weight * 1.2)  # 增加新情绪影响
            
        combined_value = (base_accumulation * (1 - accumulation_weight) + 
                        current_value * accumulation_weight)
    else:
        combined_value = base_accumulation
    
    return combined_value

def is_accumulation_period(period_type):
    """判断是否为情绪积累时段"""
    return period_type in ['pre_open', 'overnight', 'break', 'non_trading', 'other']

def process_emotion_data(df, resample_rule='1min', debug=False):
    """
    处理情感数据，实现情绪的衰减和积累效应，支持自定义时间粒度
    
    Args:
        df: 输入数据框
        resample_rule: 时间粒度
        debug: 是否输出调试信息
    """
    # 转换时间列为datetime类型
    df['时间点'] = pd.to_datetime(df['时间点'])
    
    # 创建完整的时间序列（指定粒度）
    start_dt = df['时间点'].min()
    end_dt = df['时间点'].max()
    full_range = pd.date_range(start=start_dt, end=end_dt, freq=resample_rule)
    
    # 创建基础DataFrame
    result_df = pd.DataFrame({'时间点': full_range})
    result_df['period_type'] = result_df['时间点'].apply(get_period_type)
    result_df['is_trading_day'] = result_df['时间点'].apply(is_trading_day)
    
    # 合并原始数据
    result_df = pd.merge(result_df, df, on='时间点', how='left')
    
    if debug:
        print(f"创建了完整时间序列，总共 {len(result_df)} 个时间点")
        print(f"原始数据有 {df['极性'].notna().sum()} 个非空值")
        print(f"需要补全 {len(result_df) - df['极性'].notna().sum()} 个缺失值")
    
    # 处理每个情绪维度
    for col in ['极性', '强度', '支配维度']:
        values = []
        prev_value = 0.0
        prev_valid_value = 0.0
        last_time = result_df['时间点'].iloc[0] - pd.Timedelta(resample_rule)
        
        for idx in range(len(result_df)):
            current_time = result_df.iloc[idx]['时间点']
            current_value = result_df.iloc[idx][col]
            period_type = result_df.iloc[idx]['period_type']
            is_trading = result_df.iloc[idx]['is_trading_day']
            
            # 使用固定的时间间隔进行衰减计算（基于resample_rule）
            # 因为我们已经创建了完整的时间序列，所以每个时间点间隔都是固定的
            if resample_rule == '1min':
                minutes_diff = 1
            elif resample_rule == '5min':
                minutes_diff = 5
            elif resample_rule == '15min':
                minutes_diff = 15
            elif resample_rule == '30min':
                minutes_diff = 30
            elif resample_rule == '1H':
                minutes_diff = 60
            else:
                # 解析resample_rule，如'2H' -> 120分钟
                import re
                match = re.match(r'(\d+)([HhMm])', resample_rule)
                if match:
                    num = int(match.group(1))
                    unit = match.group(2).upper()
                    if unit == 'H':
                        minutes_diff = num * 60
                    elif unit == 'M':
                        minutes_diff = num
                    else:
                        minutes_diff = 15  # 默认15分钟
                else:
                    minutes_diff = 15  # 默认15分钟
            
            # 非交易日特殊处理
            if not is_trading:
                period_type = 'non_trading'
            
            # 调试：监控时段切换
            if debug and idx > 0:
                prev_period = result_df.iloc[idx-1]['period_type']
                if prev_period != period_type:
                    print(f"时段切换: {current_time} {prev_period} -> {period_type}")
            
            if pd.notna(current_value):
                # 有新情绪数据时的处理
                if debug:
                    print(f"处理有数据时间点: {current_time} 值={current_value:.2f} 时段={period_type}")
                
                decayed_prev = calculate_emotion_decay(
                    prev_value=prev_valid_value,
                    current_value=current_value,
                    minutes=minutes_diff,
                    period_type=period_type
                )
                
                # 新旧情绪融合权重调整
                if period_type == 'non_trading':
                    weight_new = 0.8  # 非交易日新情绪权重更大
                else:
                    weight_new = 0.7
                
                combined_value = decayed_prev * (1 - weight_new) + current_value * weight_new
                
                # 根据不同情绪维度限制取值范围
                if col == '强度':
                    combined_value = min(max(combined_value, 0), 100)
                else:  # 极性和支配度
                    combined_value = min(max(combined_value, -100), 100)
                
                if debug:
                    print(f"  衰减后: {decayed_prev:.2f} 融合后: {combined_value:.2f}")
                values.append(combined_value)
                prev_valid_value = current_value
                prev_value = combined_value
            else:
                # 无新情绪数据时的处理
                if is_accumulation_period(period_type):
                    # 非交易时段或非交易日，应用积累效应
                    if debug:
                        print(f"补全缺失时间点: {current_time} 应用积累 时段={period_type}")
                    
                    accumulated_value = calculate_emotion_accumulation(
                        prev_value=prev_value,
                        current_value=np.nan,
                        minutes=minutes_diff,
                        period_type=period_type
                    )
                    
                    # 根据不同情绪维度限制取值范围
                    if col == '强度':
                        accumulated_value = min(max(accumulated_value, 0), 100)
                    else:  # 极性和支配度
                        accumulated_value = min(max(accumulated_value, -100), 100)
                    
                    if debug:
                        print(f"  积累后: {accumulated_value:.2f}")
                    values.append(accumulated_value)
                    prev_value = accumulated_value
                else:
                    # 交易时段，应用衰减效应
                    if debug:
                        print(f"补全缺失时间点: {current_time} 应用衰减 时段={period_type}")
                    
                    decayed_value = calculate_emotion_decay(
                        prev_value=prev_valid_value,
                        current_value=np.nan,
                        minutes=minutes_diff,
                        period_type=period_type
                    )
                    
                    # 根据不同情绪维度限制取值范围
                    if col == '强度':
                        decayed_value = min(max(decayed_value, 0), 100)
                    else:  # 极性和支配度
                        decayed_value = min(max(decayed_value, -100), 100)
                    
                    if debug:
                        print(f"  衰减后: {decayed_value:.2f}")
                    values.append(decayed_value)
                    prev_value = decayed_value
            
            last_time = current_time
        
        # 分段放大极端情绪信号
        arr = np.array(values)
        if col in ['极性', '强度']:
            # 绝对值大于80的极端信号放大1.5倍，50-80之间放大1.2倍
            mask_extreme = np.abs(arr) > 80
            mask_strong = (np.abs(arr) > 50) & (np.abs(arr) <= 80)
            arr[mask_extreme] = arr[mask_extreme] * 1.5
            arr[mask_strong] = arr[mask_strong] * 1.2
            # 限制范围
            if col == '强度':
                arr = np.clip(arr, 0, 100)
            else:
                arr = np.clip(arr, -100, 100)
        result_df[col] = arr
    
    # 处理开盘时刻的情绪释放
    for col in ['极性', '强度', '支配维度']:
        for day in pd.date_range(start=result_df['时间点'].min().date(), 
                               end=result_df['时间点'].max().date()):
            # 只在交易日处理开盘时刻的情绪释放
            if is_trading_day(day):
                # 定义开盘时刻和对应的释放比例
                open_times = [
                    (day.replace(hour=9, minute=0), 0.95),    # 早盘开盘释放95%
                    (day.replace(hour=13, minute=30), 0.85),  # 午盘开盘释放85%
                    (day.replace(hour=21, minute=0), 0.75)    # 夜盘开盘释放75%
                ]
                for open_time, release_ratio in open_times:
                    mask = result_df['时间点'] == open_time
                    if mask.any():
                        idx = mask.idxmax()
                        if idx > 0:
                            prev_value = result_df.at[idx-1, col]
                            current_value = result_df.at[idx, col]
                            # 释放积累情绪，保持部分延续性
                            new_value = (current_value * (1 - release_ratio) + 
                                       prev_value * release_ratio)
                            if col == '强度':
                                new_value = min(max(new_value, 0), 100)
                            else:
                                new_value = min(max(new_value, -100), 100)
                            result_df.at[idx, col] = new_value
    # 格式化时间输出
    result_df['时间点'] = result_df['时间点'].dt.strftime('%Y/%m/%d %H:%M')
    return result_df[['时间点', '极性', '强度', '支配维度']]

def main(resample_rule='15min', debug=False):
    """主函数，支持自定义粒度"""
    input_file = f'./emo_data/emo_PAD/SC_combined_评论分析结果_{resample_rule}.xlsx'
    output_dir = './emo_data/emo_PAD_completed'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'SC_combined_情绪补全_{resample_rule}.xlsx')
    print(f"开始处理文件: {input_file}")
    try:
        df = pd.read_excel(input_file)
        print(f"原始数据行数: {len(df)}")
        print(f"情绪数据非空值数量: {df['极性'].notna().sum()}")
        start_time = datetime.now()
        result_df = process_emotion_data(df, resample_rule=resample_rule, debug=debug)
        processing_time = datetime.now() - start_time
        result_df.to_excel(output_file, index=False)
        print(f"\n结果已保存至: {output_file}")
        print(f"处理时间: {processing_time}")
        print("\n情绪数据统计:")
        for col in ['极性', '强度', '支配维度']:
            print(f"\n{col}:")
            print(f"- 原始非空值数量: {df[col].notna().sum()}")
            print(f"- 填充后非空值数量: {result_df[col].notna().sum()}")
            print(f"- 数值范围: [{result_df[col].min():.2f}, {result_df[col].max():.2f}]")
            print(f"- 均值: {result_df[col].mean():.2f}")
            print(f"- 标准差: {result_df[col].std():.2f}")
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始情绪数据补全处理...")
    print("="*50)
    # 这里可以自定义粒度，如'1min'、'5min'、'15min'、'30min'、'1H'、'2H'、'4H'
    # 注意：这里的粒度应该与2.2文件中的粒度保持一致
    resample_rule = '15min'  # 默认15分钟，可以根据需要修改
    debug = False  # 设置为True可以看到详细的处理过程
    main(resample_rule=resample_rule, debug=debug)
    print("\n处理完成！")