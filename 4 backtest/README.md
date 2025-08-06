# 情绪指标回测框架

## 框架概述

这是一个基于backtrader构建的期货情绪指标回测框架，支持多种策略类型，允许用户直接在代码中指定数据文件路径和策略类型。

## 支持的策略

### 1. SignalLevelStrategy (信号量等级策略)
- **类型**: 单因子策略
- **指标**: 信号量_等级
- **逻辑**: 当信号量_等级 >= 买入阈值时买入，<= 卖出阈值时卖出
- **参数**: buy_level, sell_level, position_size, stop_loss, take_profit

### 2. EmotionSignalStrategy (情绪信号策略)
- **类型**: 多因子策略
- **指标**: 信号量、极性、强度、支配维度、情绪等级
- **逻辑**: 综合多个情绪指标和技术指标
- **参数**: signal_threshold, position_size, stop_loss, take_profit, use_volume, use_emotion_level

### 3. EmotionMomentumStrategy (情绪动量策略)
- **类型**: 动量策略
- **指标**: 情绪动量、价格动量、成交量动量
- **逻辑**: 基于动量的趋势跟踪
- **参数**: momentum_period, signal_period, position_size, stop_loss

## 使用方法

### 方法1: 直接修改main.py中的配置

在 `main.py` 文件的配置区域直接指定参数：

```python
def main():
    # ==================== 配置区域 ====================
    # 在这里直接指定数据文件路径
    DATA_FILE_PATH = "sc2210_with_emotion_lag1min.xlsx"  # 修改为您的数据文件路径
    
    # 在这里直接指定策略类型
    STRATEGY_TYPE = "signal_level"  # 可选: "signal_level", "signal", "momentum"
    
    # 在这里指定运行模式
    RUN_MODE = "backtest"  # 可选: "backtest", "optimize", "compare"
    
    # 是否显示图表
    SHOW_PLOT = True
    # ================================================
```

然后运行：
```bash
python main.py
```

### 方法2: 使用示例文件

运行 `example_usage.py` 查看各种使用示例：

```bash
python example_usage.py
```

### 方法3: 直接调用函数

```python
from main import run_backtest, run_optimization, run_strategy_comparison

# 运行回测
result = run_backtest("sc2210_with_emotion_lag1min.xlsx", "signal_level", plot=True)

# 运行参数优化
results = run_optimization("sc2210_with_emotion_lag1min.xlsx", "signal_level")

# 运行策略对比
signal_level_result, emotion_result = run_strategy_comparison("sc2210_with_emotion_lag1min.xlsx")
```

## 配置参数说明

### 数据文件路径
- 格式: Excel文件 (.xlsx)
- 位置: 数据文件应放在数据目录中
- 示例: "sc2210_with_emotion_lag1min.xlsx"

### 策略类型
- `"signal_level"`: 信号量等级策略 (推荐用于单因子分析)
- `"signal"`: 情绪信号策略 (多因子策略)
- `"momentum"`: 情绪动量策略 (动量策略)

### 运行模式
- `"backtest"`: 运行回测
- `"optimize"`: 参数优化
- `"compare"`: 策略对比

## 输出结果

### 回测结果
- 初始资金和最终资金
- 总收益率
- 夏普比率
- 最大回撤
- 交易统计
- 策略胜率

### 图表输出
- 资金曲线图
- 情绪指标走势图
- 买入/卖出信号标记

### 参数优化结果
- 按收益率排序的参数组合
- 统计信息 (平均值、标准差等)
- 最佳参数组合

## 文件结构

```
4 backtest/
├── main.py                    # 主程序 (配置区域)
├── example_usage.py           # 使用示例
├── backtest_engine.py         # 回测引擎
├── emotion_strategy.py        # 策略定义
├── data_loader.py             # 数据加载器
├── optimizer.py               # 参数优化器
└── README_NEW_FRAMEWORK.md   # 说明文档
```

## 快速开始

1. **查看可用数据文件**:
   ```python
   from data_loader import EmotionDataLoader
   loader = EmotionDataLoader()
   files = loader.get_available_files()
   print(files)
   ```

2. **运行基本回测**:
   ```python
   from main import run_backtest
   result = run_backtest("sc2210_with_emotion_lag1min.xlsx", "signal_level")
   ```

3. **运行参数优化**:
   ```python
   from main import run_optimization
   results = run_optimization("sc2210_with_emotion_lag1min.xlsx", "signal_level")
   ```

## 注意事项

1. **数据文件**: 确保数据文件存在且格式正确
2. **策略选择**: 根据研究需求选择合适的策略类型
3. **参数调优**: 使用参数优化功能找到最佳参数组合
4. **结果分析**: 关注收益率、夏普比率、最大回撤等关键指标

## 扩展功能

1. **添加新策略**: 在 `emotion_strategy.py` 中定义新的策略类
2. **自定义参数**: 在 `main.py` 的配置区域修改策略参数
3. **数据预处理**: 在 `data_loader.py` 中添加数据预处理功能
4. **结果导出**: 添加结果保存和导出功能 