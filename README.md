# PAD_min_indicator_mining

## 项目简介

本项目旨在基于情绪词典和期货数据，挖掘分钟级别的情绪指标，并进行因子分析、信号优化等量化科研工作。项目涵盖了数据预处理、情绪信号计算、数据融合、因子分析、可视化等完整流程，适用于情绪与金融市场关系的量化研究。

---

## 目录结构说明

```
PAD_min_indicator_mining/
├── 1 data_preparation/           # 数据预处理脚本
│   └── futures_data_preprocessor.py
├── 2 data_processing/            # 情绪PAD计算与数据融合
│   ├── 2.1 emotion_pad_calculator.py
│   ├── 2.2 text_PAD_data_combiner.py
│   ├── 2.3 emotion_pad_completer.py
│   ├── 2.5 emotion_volume_extractor.py
│   └── 2.6 futures&emo_data_combiner.py
├── 3 factor_analysis/            # 因子分析与信号优化
│   ├── conditional_ic_analyzer.py
│   ├── emotion_signal_optimizer.py
│   ├── factor_analyzer.py
│   ├── factor_combination_optimizer.py
│   └── multi_scale_ic_analyzer.py
├── analysis_plot/                # 各类分析结果图表与可视化
│   ├── combination/
│   ├── conditional/
│   ├── multi_scale/
│   └── ...（各类png图片和csv结果）
├── dictionary/                   # 情绪词典与停用词表
│   ├── Arousal/
│   ├── Dominance/
│   ├── Pleasure/
│   └── stopword.txt
├── emo_data/                     # 原始及中间情绪数据
│   ├── emo_PAD/
│   ├── emo_PAD_completed/
│   ├── emo_signals/
│   └── emo_text/
├── futures_data/                 # 原始期货数据
├── futures_emo_combined_data/    # 融合后的期货与情绪数据
├── notebooks/                    # Jupyter Notebook 交互分析
├── pictures/                     # 逻辑结构图等图片
├── 0611问题.ipynb                # 相关问题记录或分析
└── ...
```

---

## 主要功能模块

### 1. 数据预处理（1 data_preparation/）
- 对原始期货数据进行清洗、格式转换等预处理操作。

### 2. 情绪PAD计算与数据融合（2 data_processing/）
- 利用情绪词典对文本数据进行PAD三维度（愉悦度、唤醒度、支配度）情绪分析。
- 补全缺失情绪数据，提取情绪强度、信号量等特征。
- 将情绪数据与期货数据进行分钟级别的对齐与融合。

### 3. 因子分析与信号优化（3 factor_analysis/）
- 对融合后的数据进行因子分析，计算IC、IC衰减、稳定性等指标。
- 优化情绪信号，探索多因子组合方法。

### 4. 可视化与结果分析（analysis_plot/）
- 各类因子分析、信号表现、分组收益等结果的可视化图片和汇总表格。

### 5. 词典与停用词（dictionary/）
- 包含情绪词典（愉悦度、唤醒度、支配度）及停用词表，用于文本情绪分析。

### 6. 数据存储（emo_data/、futures_data/、futures_emo_combined_data/）
- 存放原始及中间处理的情绪数据、期货数据，以及最终融合数据。

---

## 环境依赖

请根据实际代码补充 requirements.txt，常用依赖可能包括：

- pandas
- numpy
- openpyxl
- matplotlib / seaborn
- scikit-learn
- jupyter

安装依赖：
```bash
pip install -r requirements.txt
```

---

## 快速开始

1. 数据准备：将原始期货数据和文本数据放入对应文件夹。
2. 运行数据预处理和情绪分析脚本，生成融合数据。
3. 进行因子分析与信号优化，输出分析结果。
4. 查看 analysis_plot/ 下的可视化结果。

---

## 建议的 .gitignore 内容

```
/analysis_plot
/emo_data
/futures_data
/futures_emo_combined_data
/pictures

# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Jupyter
.ipynb_checkpoints/

# macOS
.DS_Store

# Windows
Thumbs.db

# IDE
.idea/
.vscode/

# 虚拟环境
venv/
.venv/
env/

# 日志和临时文件
*.log
*.tmp

# 环境变量
.env
```

---

## 贡献与反馈

如有建议或问题，欢迎提交 issue 或直接联系项目维护者。

---

如需进一步补充 requirements.txt 或详细的运行示例请告知！ 