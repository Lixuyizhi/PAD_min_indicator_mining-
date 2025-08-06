# 新策略说明

本项目已更新为三个新的交易策略，替换了原有的情绪指标策略。

## 策略概览

### 1. 布林带策略 (BollingerBandsStrategy)

**策略原理：**
- 基于布林带技术指标进行交易
- 当价格触及布林带下轨时买入
- 当价格触及布林带上轨或回到中轨时卖出
- 包含止损和止盈机制

**主要参数：**
- `bb_period`: 布林带周期 (默认: 20)
- `bb_dev`: 布林带标准差倍数 (默认: 2.0)
- `position_size`: 仓位大小 (默认: 0.1)
- `stop_loss`: 止损比例 (默认: 0.02)
- `take_profit`: 止盈比例 (默认: 0.04)

**交易逻辑：**
- 买入条件：价格 ≤ 布林带下轨
- 卖出条件：
  - 止损：价格 < 买入价格 × (1 - 止损比例)
  - 止盈：价格 > 买入价格 × (1 + 止盈比例)
  - 布林带卖出：价格 ≥ 布林带上轨
  - 中轨卖出：价格 ≥ 布林带中轨 × 0.99

### 2. 海龟交易策略 (TurtleTradingStrategy)

**策略原理：**
- 基于经典的海龟交易系统
- 突破20日高点时买入
- 突破10日低点时卖出
- 使用ATR进行动态止损

**主要参数：**
- `entry_period`: 入场突破周期 (默认: 20)
- `exit_period`: 出场突破周期 (默认: 10)
- `atr_period`: ATR周期 (默认: 20)
- `position_size`: 仓位大小 (默认: 0.1)
- `risk_percent`: 风险百分比 (默认: 0.02)

**交易逻辑：**
- 买入条件：当前最高价 > 20日最高价
- 卖出条件：
  - 海龟出场：当前最低价 < 10日最低价
  - ATR止损：价格 < 买入价格 - 2 × ATR

### 3. 信号量等级反向策略 (SignalLevelReverseStrategy)

**策略原理：**
- 基于IC检验结果：信号量等级和5期收益率成反比
- 当信号量等级高时买入（预期未来收益率会下降）
- 当信号量等级降低或5期收益率为负时卖出

**主要参数：**
- `signal_level_threshold`: 信号量等级阈值 (默认: 6)
- `position_size`: 仓位大小 (默认: 0.1)
- `stop_loss`: 止损比例 (默认: 0.02)
- `take_profit`: 止盈比例 (默认: 0.04)
- `lookback_period`: 回看期数 (默认: 5)

**交易逻辑：**
- 买入条件：信号量等级 ≥ 阈值
- 卖出条件：
  - 止损：价格 < 买入价格 × (1 - 止损比例)
  - 止盈：价格 > 买入价格 × (1 + 止盈比例)
  - 信号量等级降低：当前等级 < 阈值 × 0.8
  - 5期收益率反转：5期收益率 < -0.01

## 使用方法

### 运行单个策略回测

```python
# 在main.py中修改配置
STRATEGY_TYPE = "bollinger_bands"  # 可选: "bollinger_bands", "turtle_trading", "signal_level_reverse"
RUN_MODE = "backtest"

# 运行
python main.py
```

### 运行策略对比

```python
# 在main.py中修改配置
RUN_MODE = "compare"

# 运行
python main.py
```

### 运行参数优化

```python
# 在main.py中修改配置
RUN_MODE = "optimize"
STRATEGY_TYPE = "bollinger_bands"  # 选择要优化的策略

# 运行
python main.py
```

### 测试策略

```python
# 运行测试脚本
python test_strategies.py
```

## 文件结构

- `emotion_strategy.py`: 包含三个新策略的实现
- `main.py`: 主程序，支持回测、优化、对比功能
- `backtest_engine.py`: 回测引擎，负责运行回测和生成图表
- `optimizer.py`: 参数优化器，支持三个策略的参数优化
- `test_strategies.py`: 策略测试脚本
- `data_loader.py`: 数据加载器

## 注意事项

1. 确保数据文件包含必要的列：
   - 对于信号量等级反向策略，需要包含 `信号量_等级` 列
   - 其他策略只需要标准的OHLCV数据

2. 策略参数可以根据实际情况进行调整

3. 建议在实盘交易前进行充分的回测验证

4. 所有策略都包含风险控制机制（止损、止盈） 