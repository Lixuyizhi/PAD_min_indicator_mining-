import os
import pandas as pd
import jieba
from tqdm import tqdm
from datetime import datetime
import calendar

# 加载停用词
def load_stopwords(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f.readlines())

# 加载词典文件
def load_word_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]

# 计算极性分数
def calculate_polarity(sentence, positive_words, negative_words, stopwords):
    # 确保输入是字符串类型
    if not isinstance(sentence, str):
        sentence = str(sentence)
    words = jieba.lcut(sentence)
    words = [word for word in words if word not in stopwords]
    total_score = 0
    positive_set = set(positive_words)
    negative_set = set(negative_words)

    for word in words:
        if word in positive_set:
            total_score += 1
        if word in negative_set:
            total_score -= 1

    word_count = len(words)
    average_score = total_score / word_count if word_count > 0 else 0
    return average_score * 100

# 计算强度分数
def calculate_strength(comment, intensity_dicts, stopwords):
    # 确保输入是字符串类型
    if not isinstance(comment, str):
        comment = str(comment)
    strength_score = 0
    words = [word for word in jieba.lcut(comment) if word not in stopwords]
    for i, words_dict in enumerate(intensity_dicts):
        for word in words_dict:
            if word in words:
                strength_score += i
    word_count = len(words)
    average_score = strength_score / word_count if word_count > 0 else 0
    return average_score * 100

# 计算支配维度分数
def calculate_dominance(comment, confidence_words, lack_confidence_words, stopwords):
    # 确保输入是字符串类型
    if not isinstance(comment, str):
        comment = str(comment)
    words = jieba.lcut(comment)
    words = [word for word in words if word not in stopwords]
    total_score = 0
    positive_set = set(confidence_words)
    negative_set = set(lack_confidence_words)

    for word in words:
        if word in positive_set:
            total_score += 1
        if word in negative_set:
            total_score -= 1

    word_count = len(words)
    average_score = total_score / word_count if word_count > 0 else 0
    return average_score * 100

# 检查文件是否为有效的Excel文件
def is_valid_excel(file_path):
    try:
        pd.ExcelFile(file_path)
        return True
    except:
        return False

# 处理期货文件夹
def process_futures_folder(futures_folder, stopwords):
    results = {}
    # 加载词典
    positive_words = load_word_list('./dictionary/Pleasure/positive_words.txt')
    negative_words = load_word_list('./dictionary/Pleasure/negative_words.txt')
    confidence_words = load_word_list('./dictionary/Dominance/confidence_words.txt')
    lack_confidence_words = load_word_list('./dictionary/Dominance/lack_confidence_words.txt')
    intensity_dicts = [load_word_list(f'./dictionary/Arousal/Intensity_{i}.txt') for i in range(1, 6)]

    # 遍历文件夹中的Excel文件
    for root, dirs, files in os.walk(futures_folder):
        files = [f for f in files if f.endswith('.xlsx')]
        for file in tqdm(files, desc="处理期货文件"):
            file_path = os.path.join(root, file)
            try:
                df = pd.read_excel(file_path, header=0)
                df.columns = ['阅读量', '内容', '时间']

                future_name = os.path.splitext(file)[0]
                results[future_name] = []

                for index, row in df.iterrows():
                    try:
                        comment = str(row['内容'])
                        time_point = str(row['时间'])

                        current_year = 2024
                        month, day, time = time_point.split(' ')[0].split('-') + [time_point.split(' ')[1]]
                        month, day = int(month), int(day)
                        if month == 2 and day == 29 and not calendar.isleap(current_year):
                            while not calendar.isleap(current_year):
                                current_year += 1

                        time_point = pd.to_datetime(f'{current_year}-{month:02d}-{day:02d} {time}', format='%Y-%m-%d %H:%M')
                        formatted_time = time_point.strftime('%Y/%m/%d %H:%M')

                        polarity = calculate_polarity(comment, positive_words, negative_words, stopwords)
                        strength = calculate_strength(comment, intensity_dicts, stopwords)
                        dominance = calculate_dominance(comment, confidence_words, lack_confidence_words, stopwords)
                        results[future_name].append((formatted_time, polarity, strength, dominance))
                    except Exception as e:
                        print(f"处理评论时出错: {e}")
                        continue
            except Exception as e:
                print(f"处理文件 {file} 时出错: {e}")
                continue
    return results

# 主程序
if __name__ == "__main__":
    futures_folder_path = 'emo_data/emo_text'
    stopwords_path = './dictionary/stopword.txt'
    stopwords = load_stopwords(stopwords_path)
    results = process_futures_folder(futures_folder_path, stopwords)

    # 创建输出目录（如果不存在）
    os.makedirs('emo_data/emo_PAD', exist_ok=True)

    # 导出结果
    for future_name, data in results.items():
        if not data:  # 跳过空数据
            print(f"警告: {future_name} 没有有效数据")
            continue

        results_df = pd.DataFrame(data, columns=['时间点', '极性', '强度', '支配维度'])
        # 将时间点转换为datetime类型并排序
        results_df['时间点'] = pd.to_datetime(results_df['时间点'])
        results_df = results_df.sort_values('时间点')
        # 将时间点转回字符串格式
        results_df['时间点'] = results_df['时间点'].dt.strftime('%Y/%m/%d %H:%M')

        # 保存结果
        output_file = f'emo_data/emo_PAD/{future_name}_评论分析结果.xlsx'
        results_df.to_excel(output_file, index=False)
        print(f"结果已导出为 {output_file}")