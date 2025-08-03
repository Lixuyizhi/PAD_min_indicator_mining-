# 信号量等级因子回测系统

基于IC分析结果构建的backtrader回测系统，专门用于信号量等级因子的回测分析。

## 系统架构

系统采用模块化设计，包含以下核心模块：

### 1. 策略模块 (`strategy.py`)
- **SignalLevelStrategy**: 基于信号量等级的交易策略
- 根据IC分析结果，信号量等级与5期收益率有负相关关系
- 支持多空双向交易，包含止损止盈机制

### 2. 数据加载模块 (`data_loader.py`)
- **DataLoader**: 数据加载和预处理
- **SignalLevelData**: backtrader自定义数据源
- 自动从文件名提取数据粒度和滞后时间信息

### 3. 分析器模块 (`analyzer.py`)
- **BacktestAnalyzer**: 回测结果分析和可视化
- 生成综合回测报告和图表
- 支持多种性能指标分析

### 4. 参数优化模块 (`optimizer.py`)
- **ParameterOptimizer**: 策略参数优化
- 支持网格搜索和参数组合测试
- 提供默认和扩展参数范围

### 5. 主平台模块 (`backtest_platform.py`)
- **BacktestPlatform**: 回测平台主类
- 整合所有模块功能
- 提供简洁的API接口

## 使用方法

### 基础回测

```python
from backtest_platform import BacktestPlatform

# 创建回测平台
platform = BacktestPlatform(
    data_path='futures_emo_combined_data/sc2210_with_emotion_1h_lag180min.xlsx',
    output_dir='backtest_results'
)

# 运行回测
cerebro, results = platform.run_backtest()
```

### 自定义参数回测

```python
# 自定义策略参数
custom_params = {
    'signal_threshold': 5.5,  # 信号阈值
    'position_size': 0.15,    # 仓位大小
    'stop_loss': 0.025,       # 止损比例
    'take_profit': 0.05,      # 止盈比例
    'max_holding_periods': 3  # 最大持仓期数
}

# 运行回测
cerebro, results = platform.run_backtest(strategy_params=custom_params)
```

### 参数优化

```python
# 运行参数优化回测
cerebro, results = platform.run_optimized_backtest()

# 或者仅进行参数优化
best_params, results_df = platform.optimize_parameters()
```

### 命令行使用

```bash
# 基础回测
python backtest_platform.py --data_path "your_data_file.xlsx"

# 参数优化
python backtest_platform.py --optimize

# 扩展参数优化
python backtest_platform.py --extended_optimize
```

## 策略参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| signal_threshold | 5.0 | 信号阈值，高于此值做空，低于此值做多 |
| position_size | 0.1 | 仓位大小 |
| stop_loss | 0.02 | 止损比例 |
| take_profit | 0.04 | 止盈比例 |
| max_holding_periods | 5 | 最大持仓期数 |
| use_volume_filter | True | 是否使用成交量过滤 |
| volume_threshold | 1.5 | 成交量阈值倍数 |

## 输出结果

### 控制台输出
- 回测进度和状态信息
- 策略统计指标
- 参数优化结果

### 图表输出
- 价格走势图
- 信号量等级分布图
- 交易盈亏分布图
- 回撤曲线图

### 文件输出
- 回测结果图表 (PNG格式)
- 参数优化结果 (CSV格式)

## 性能指标

系统提供以下性能指标：

- **总收益率**: 回测期间的总收益
- **夏普比率**: 风险调整后收益
- **最大回撤**: 最大资金回撤比例
- **胜率**: 盈利交易占比
- **交易次数**: 总交易次数
- **年化收益率**: 年化收益率

## 示例脚本

`run_backtest.py` 提供了多种使用示例：

1. **基础回测**: 使用默认参数运行回测
2. **参数优化回测**: 自动优化参数后运行回测
3. **自定义参数回测**: 使用自定义参数运行回测
4. **仅参数优化**: 只进行参数优化，不运行回测

## 注意事项

1. 确保数据文件包含必要的列：`Open`, `High`, `Low`, `Close`, `Volume`, `信号量_等级`
2. 数据文件命名格式：`*_粒度_lag滞后时间min.xlsx`
3. 参数优化可能需要较长时间，建议先用小范围参数测试
4. 回测结果仅供参考，实际交易需要考虑更多因素

## 依赖库

- backtrader
- pandas
- numpy
- matplotlib
- scipy

## 文件结构

```
4 backtest/
├── backtest_platform.py    # 主回测平台
├── strategy.py             # 策略模块
├── data_loader.py          # 数据加载模块
├── analyzer.py             # 分析器模块
├── optimizer.py            # 参数优化模块
├── run_backtest.py         # 示例脚本
├── README.md              # 说明文档
└── backtest_results/      # 结果输出目录
``` 