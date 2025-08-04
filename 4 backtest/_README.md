# 统一回测系统

基于backtrader的统一回测系统，支持多种策略：原始信号量策略、情绪极值策略、情绪动量策略、情绪分层策略。

## 系统架构

系统采用模块化设计，包含以下核心模块：

### 1. 策略模块
- **SignalLevelStrategy** (`strategy.py`): 原始信号量等级策略
- **EmotionExtremeStrategy** (`emotion_extreme_strategy.py`): 情绪极值策略
- **EmotionMomentumStrategy** (`emotion_momentum_strategy.py`): 情绪动量策略
- **EmotionLayeredStrategy** (`emotion_layered_strategy.py`): 情绪分层策略

### 2. 统一回测运行器 (`run_backtest.py`)
- **UnifiedBacktestRunner**: 统一回测运行器
- 支持多种策略选择和参数配置
- 自动比较不同策略的表现

### 3. 辅助模块
- **DataLoader** (`data_loader.py`): 数据加载和预处理
- **BacktestAnalyzer** (`analyzer.py`): 回测结果分析
- **ParameterOptimizer** (`optimizer.py`): 参数优化
- **BacktestPlatform** (`backtest_platform.py`): 原有回测平台

## 策略说明

### 1. 原始信号量策略 (original)
- **描述**: 基于信号量等级的传统策略，使用布林带等技术指标过滤
- **适用场景**: 信号量等级与收益率有明确相关关系
- **核心逻辑**: 信号量等级高于阈值做空，低于阈值做多

### 2. 情绪极值策略 (extreme)
- **描述**: 在情绪极值处进行反向交易
- **适用场景**: 情绪信号有明显的极值分布
- **核心逻辑**: 
  - 极低情绪(1-2.5)：做多（恐慌时买入）
  - 极高情绪(7.5-10)：做空（亢奋时卖出）
  - 中性情绪(2.5-7.5)：不交易

### 3. 情绪动量策略 (momentum)
- **描述**: 基于情绪变化趋势进行交易
- **适用场景**: 情绪信号变化较为频繁，有明显的趋势性
- **核心逻辑**:
  - 情绪从低向高转变：做多
  - 情绪从高向低转变：做空
  - 避免在极值情绪时交易

### 4. 情绪分层策略 (layered)
- **描述**: 将情绪分为5个层次，不同层次采用不同策略
- **适用场景**: 情绪信号分布较为均匀，需要精细化管理
- **核心逻辑**:
  - 极低情绪(1-2)：做多
  - 低情绪(2-4)：情绪改善时做多
  - 中性情绪(4-6)：不交易或小仓位
  - 高情绪(6-8)：情绪恶化时做空
  - 极高情绪(8-10)：做空

## 使用方法

### 1. 命令行使用

```bash
# 显示策略信息
python run_backtest.py --info

# 运行所有策略
python run_backtest.py --strategy all

# 运行指定策略
python run_backtest.py --strategy extreme

# 指定数据文件
python run_backtest.py --data_path "your_data_file.xlsx" --strategy momentum

# 指定输出目录
python run_backtest.py --strategy layered --output_dir "my_results"
```

### 2. Python代码使用

```python
from run_backtest import UnifiedBacktestRunner

# 创建回测运行器
runner = UnifiedBacktestRunner('your_data_file.xlsx')

# 显示策略信息
runner.show_strategy_info()

# 运行单个策略
cerebro, results = runner.run_strategy('extreme')

# 运行所有策略
results = runner.run_all_strategies()

# 自定义参数运行策略
custom_params = {
    'low_threshold': 2.0,
    'high_threshold': 8.0,
    'position_size': 0.15
}
cerebro, results = runner.run_strategy('extreme', custom_params)
```

### 3. 策略选择建议

根据您的数据特点选择策略：

1. **如果情绪信号经常出现极值（1-2或8-9）**：
   - 推荐使用：情绪极值策略 (`extreme`)
   - 优势：简单直接，容易理解

2. **如果情绪信号变化频繁，有明显趋势**：
   - 推荐使用：情绪动量策略 (`momentum`)
   - 优势：能捕捉情绪反转点

3. **如果情绪信号分布相对均匀**：
   - 推荐使用：情绪分层策略 (`layered`)
   - 优势：精细化管理，适应性强

4. **如果信号量等级与收益率有明确相关关系**：
   - 推荐使用：原始信号量策略 (`original`)
   - 优势：基于IC分析结果，逻辑清晰

## 数据要求

您的数据需要包含以下列：
- `datetime`: 时间戳
- `open`, `high`, `low`, `close`: 价格数据
- `volume`: 成交量
- `signal_level`: 情绪信号等级（0-10）

系统会自动识别以下列名：
- `信号量_等级` → `signal_level`
- `Signal_Level` → `signal_level`
- `signal_level` → `signal_level`

## 输出结果

### 控制台输出
- 数据加载信息
- 策略运行进度
- 策略统计指标
- 策略结果比较

### 文件输出
- 每个策略的结果保存在独立目录
- 参数配置文件 (`parameters.txt`)
- 策略比较结果 (`strategy_comparison.txt`)

### 结果分析
系统会自动比较不同策略的表现：
- 总收益率
- 最终资金
- 交易次数
- 胜率

## 参数配置

### 原始信号量策略参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| signal_threshold | 5.0 | 信号阈值 |
| position_size | 0.1 | 仓位大小 |
| stop_loss | 0.02 | 止损比例 |
| take_profit | 0.04 | 止盈比例 |
| max_holding_periods | 5 | 最大持仓期数 |

### 情绪极值策略参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| low_threshold | 2.5 | 低情绪阈值 |
| high_threshold | 7.5 | 高情绪阈值 |
| min_extreme_duration | 2 | 极值持续最小期数 |
| use_volume_confirmation | True | 是否使用成交量确认 |

### 情绪动量策略参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| momentum_period | 5 | 动量计算周期 |
| signal_change_threshold | 0.5 | 信号变化阈值 |
| min_signal_level | 3.0 | 最小信号等级 |
| max_signal_level | 7.0 | 最大信号等级 |

### 情绪分层策略参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| extreme_low_threshold | 2.0 | 极低情绪阈值 |
| low_threshold | 4.0 | 低情绪阈值 |
| high_threshold | 6.0 | 高情绪阈值 |
| extreme_high_threshold | 8.0 | 极高情绪阈值 |

## 注意事项

1. **数据质量**: 确保情绪信号数据的质量和连续性
2. **策略选择**: 根据数据特点选择合适的策略
3. **参数调优**: 可以通过自定义参数优化策略表现
4. **风险控制**: 合理设置止损止盈，控制单次交易风险
5. **过拟合风险**: 避免过度优化参数，建议使用样本外测试

## 依赖库

- backtrader
- pandas
- numpy
- matplotlib
- scipy

## 文件结构

```
4 backtest/
├── run_backtest.py                    # 统一回测运行脚本
├── strategy.py                        # 原始信号量策略
├── emotion_extreme_strategy.py        # 情绪极值策略
├── emotion_momentum_strategy.py       # 情绪动量策略
├── emotion_layered_strategy.py        # 情绪分层策略
├── data_loader.py                     # 数据加载模块
├── analyzer.py                        # 分析器模块
├── optimizer.py                       # 参数优化模块
├── backtest_platform.py               # 原有回测平台
├── test_multiple_strategies.py        # 多策略测试脚本
├── _README.md                         # 说明文档
└── backtest_results/                  # 结果输出目录
```

## 示例用法

```bash
# 1. 查看所有可用策略
python run_backtest.py --info

# 2. 运行所有策略并比较结果
python run_backtest.py --strategy all

# 3. 只运行情绪极值策略
python run_backtest.py --strategy extreme

# 4. 使用自定义数据文件
python run_backtest.py --data_path "my_data.xlsx" --strategy momentum

# 5. 指定输出目录
python run_backtest.py --strategy layered --output_dir "my_results"
```

通过这个统一的回测系统，您可以方便地比较不同策略的表现，选择最适合您数据特点的策略进行交易。 