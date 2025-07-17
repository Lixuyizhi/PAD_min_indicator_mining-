import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import os
from tqdm import tqdm

class EmotionSignalOptimizer:
    def __init__(self, data_path, output_dir='./analysis_plot/signal_optimization'):
        """
        情绪信号优化器
        """
        print("加载数据...")
        self.data = pd.read_excel(data_path)
        self.data['DateTime'] = pd.to_datetime(self.data['DateTime'])
        self.data = self.data.set_index('DateTime')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 基础情绪因子
        self.emotion_factors = ['极性', '强度', '支配维度']
        
    def calculate_weighted_emotion(self, weights=None):
        """
        计算加权情绪指标
        """
        if weights is None:
            weights = {'极性': 0.4, '强度': 0.3, '支配维度': 0.3}
            
        # 标准化各个情绪维度
        scaler = StandardScaler()
        normalized_emotions = pd.DataFrame()
        
        for factor in self.emotion_factors:
            normalized_emotions[factor] = scaler.fit_transform(
                self.data[factor].values.reshape(-1, 1)
            ).flatten()
        
        # 计算加权情绪
        weighted_emotion = sum(normalized_emotions[factor] * weight 
                             for factor, weight in weights.items())
        
        return weighted_emotion
    
    def apply_exponential_decay(self, signal, half_life=5):
        """
        应用指数衰减
        
        Parameters:
        -----------
        signal : pd.Series
            输入信号
        half_life : int
            半衰期（分钟）
        
        Returns:
        --------
        pd.Series
            衰减后的信号
        """
        # 计算衰减因子
        decay_factor = np.exp(-np.log(2)/half_life)
        
        # 初始化结果序列
        decayed_signal = pd.Series(index=signal.index, dtype=float)
        
        # 使用expanding window计算衰减加权平均
        for i in range(len(signal)):
            if i < half_life:
                # 对于前half_life个点，使用可用的所有历史数据
                weights = decay_factor ** np.arange(i+1)[::-1]
                decayed_signal.iloc[i] = np.sum(signal.iloc[:i+1] * weights) / np.sum(weights)
            else:
                # 对于之后的点，使用固定长度的历史数据
                weights = decay_factor ** np.arange(half_life)[::-1]
                decayed_signal.iloc[i] = np.sum(signal.iloc[i-half_life+1:i+1] * weights) / np.sum(weights)
        
        return decayed_signal
    
    def calculate_adaptive_threshold(self, signal, window=30, std_multiplier=2):
        """
        计算自适应阈值
        """
        # 确保信号是pd.Series类型
        if not isinstance(signal, pd.Series):
            signal = pd.Series(signal, index=self.data.index)
        
        # 计算滚动统计量
        rolling_mean = signal.rolling(window=window, min_periods=1).mean()
        rolling_std = signal.rolling(window=window, min_periods=1).std()
        
        upper_threshold = rolling_mean + std_multiplier * rolling_std
        lower_threshold = rolling_mean - std_multiplier * rolling_std
        
        return upper_threshold, lower_threshold
    
    def generate_signal_with_confidence(self, emotion_signal, price_col='Close'):
        """
        生成带置信度的信号
        """
        # 计算自适应阈值
        upper_threshold, lower_threshold = self.calculate_adaptive_threshold(
            emotion_signal
        )
        
        # 生成信号
        signals = pd.DataFrame(index=emotion_signal.index)
        signals['emotion'] = emotion_signal
        signals['upper_threshold'] = upper_threshold
        signals['lower_threshold'] = lower_threshold
        
        # 计算信号强度（与阈值的距离）
        signals['signal_strength'] = abs(
            (emotion_signal - emotion_signal.rolling(30).mean()) / 
            emotion_signal.rolling(30).std()
        )
        
        # 生成交易信号
        signals['trade_signal'] = 0
        signals.loc[emotion_signal > upper_threshold, 'trade_signal'] = 1
        signals.loc[emotion_signal < lower_threshold, 'trade_signal'] = -1
        
        # 计算价格变动
        signals['price_change'] = self.data[price_col].pct_change()
        
        return signals
    
    def analyze_signal_effectiveness(self, signals, min_strength=1.5):
        """
        分析信号有效性
        """
        # 仅分析强信号
        strong_signals = signals[signals['signal_strength'] > min_strength].copy()
        
        # 计算信号准确率
        accuracy = {}
        for signal in [-1, 1]:
            signal_cases = strong_signals[strong_signals['trade_signal'] == signal]
            if len(signal_cases) > 0:
                # 对于做多信号，价格上涨算正确；对于做空信号，价格下跌算正确
                correct_predictions = np.sum(
                    signal_cases['price_change'] * signal > 0
                )
                accuracy[signal] = correct_predictions / len(signal_cases)
        
        return accuracy
    
    def optimize_parameters(self, price_col='Close'):
        """
        优化参数
        """
        results = []
        
        # 测试不同的参数组合
        half_lives = [3, 5, 8, 10, 15]
        weight_combinations = [
            {'极性': 0.4, '强度': 0.3, '支配维度': 0.3},
            {'极性': 0.5, '强度': 0.3, '支配维度': 0.2},
            {'极性': 0.3, '强度': 0.4, '支配维度': 0.3},
        ]
        
        print("\n开始参数优化...")
        total_combinations = len(half_lives) * len(weight_combinations)
        
        with tqdm(total=total_combinations) as pbar:
            for weights in weight_combinations:
                for half_life in half_lives:
                    try:
                        # 计算加权情绪
                        emotion = self.calculate_weighted_emotion(weights)
                        
                        # 应用指数衰减
                        decayed_emotion = self.apply_exponential_decay(
                            emotion, half_life=half_life
                        )
                        
                        # 生成信号
                        signals = self.generate_signal_with_confidence(
                            decayed_emotion, price_col
                        )
                        
                        # 分析效果
                        accuracy = self.analyze_signal_effectiveness(signals)
                        
                        results.append({
                            'weights': weights,
                            'half_life': half_life,
                            'accuracy': accuracy,
                            'mean_accuracy': np.mean(list(accuracy.values())) if accuracy else 0
                        })
                        
                    except Exception as e:
                        print(f"\n参数组合出错 (weights={weights}, half_life={half_life}): {str(e)}")
                        continue
                    finally:
                        pbar.update(1)
        
        # 转换为DataFrame并排序
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('mean_accuracy', ascending=False)
        
        return results_df
    
    def plot_signal_analysis(self, signals, title='情绪信号分析'):
        """
        绘制信号分析图
        """
        plt.figure(figsize=(15, 10))
        
        # 绘制情绪信号和阈值
        plt.subplot(2, 1, 1)
        plt.plot(signals.index, signals['emotion'], label='情绪信号')
        plt.plot(signals.index, signals['upper_threshold'], 'r--', 
                label='上阈值')
        plt.plot(signals.index, signals['lower_threshold'], 'g--', 
                label='下阈值')
        plt.title(title)
        plt.legend()
        plt.grid(True)
        
        # 绘制信号强度
        plt.subplot(2, 1, 2)
        plt.plot(signals.index, signals['signal_strength'], label='信号强度')
        plt.axhline(y=1.5, color='r', linestyle='--', label='强信号阈值')
        plt.title('信号强度')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'signal_analysis.png'))
        plt.close()

if __name__ == "__main__":
    optimizer = EmotionSignalOptimizer(
        "./futures_emo_combined_data/sc2210_with_emotion_lag1min.xlsx"
    )
    
    # 优化参数
    results = optimizer.optimize_parameters()
    print("\n参数优化结果:")
    print(results)
    
    # 使用最优参数生成信号
    best_weights = results.iloc[
        results['mean_accuracy'].apply(
            lambda x: x
        ).argmax()
    ]['weights']
    
    emotion = optimizer.calculate_weighted_emotion(best_weights)
    decayed_emotion = optimizer.apply_exponential_decay(emotion)
    signals = optimizer.generate_signal_with_confidence(decayed_emotion)
    
    # 绘制分析图
    optimizer.plot_signal_analysis(signals)
    
    print("\n信号分析完成！") 