#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量IC分析脚本
对futures_emo_combined_data目录下的所有数据文件进行IC分析
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd

# 添加当前目录到Python路径
sys.path.append('3 factor_analysis')

def get_data_files():
    """
    获取所有需要分析的数据文件
    """
    data_dir = 'futures_emo_combined_data'
    data_files = []
    
    if not os.path.exists(data_dir):
        print(f"错误：数据目录 {data_dir} 不存在！")
        return []
    
    # 获取所有Excel文件
    for file in os.listdir(data_dir):
        if file.endswith('.xlsx') and 'with_emotion' in file:
            file_path = os.path.join(data_dir, file)
            data_files.append(file_path)
    
    # 按文件名排序
    data_files.sort()
    
    return data_files

def run_single_analysis(file_path):
    """
    对单个文件运行IC分析
    """
    print(f"\n{'='*80}")
    print(f"开始分析文件: {os.path.basename(file_path)}")
    print(f"{'='*80}")
    
    try:
        # 导入分析器
        import importlib.util
        spec = importlib.util.spec_from_file_location("signal_level_ic_analyzer", "3 factor_analysis/3.1 signal_level_ic_analyzer.py")
        signal_level_ic_analyzer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(signal_level_ic_analyzer)
        SignalLevelICAnalyzer = signal_level_ic_analyzer.SignalLevelICAnalyzer
        
        # 创建分析器实例
        analyzer = SignalLevelICAnalyzer(file_path)
        
        # 加载数据
        analyzer.load_data()
        
        # 1. 计算全局IC
        print(f"\n{'='*50}")
        print("全局IC分析")
        print(f"{'='*50}")
        analyzer.calculate_global_ic(method='both')
        
        # 2. 获取推荐窗口
        print(f"\n{'='*50}")
        print("滚动IC窗口推荐")
        print(f"{'='*50}")
        recommended_window = analyzer.get_recommended_window()
        
        # 3. 计算IR指标
        print(f"\n{'='*50}")
        print("IR指标分析")
        print(f"{'='*50}")
        analyzer.calculate_ir_metrics(window=recommended_window, method='both')
        
        # 4. 计算IC半衰期
        print(f"\n{'='*50}")
        print("IC半衰期分析")
        print(f"{'='*50}")
        analyzer.calculate_ic_half_life(method='both')
        
        # 5. 生成可视化图表
        print(f"\n{'='*50}")
        print("生成可视化图表")
        print(f"{'='*50}")
        analyzer.plot_global_relationship()
        analyzer.plot_rolling_ic(window=recommended_window)
        analyzer.plot_rolling_ic_stability(window=recommended_window)
        analyzer.plot_comprehensive_analysis(window=recommended_window)
        
        # 6. 生成分析报告
        analyzer.generate_report()
        
        print(f"\n✅ 文件 {os.path.basename(file_path)} 分析完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 文件 {os.path.basename(file_path)} 分析失败: {str(e)}")
        return False

def generate_summary_report(results):
    """
    生成批量分析总结报告
    """
    print(f"\n{'='*80}")
    print("批量IC分析总结报告")
    print(f"{'='*80}")
    
    successful_files = [r for r in results if r['success']]
    failed_files = [r for r in results if not r['success']]
    
    print(f"\n📊 分析统计:")
    print(f"- 总文件数: {len(results)}")
    print(f"- 成功分析: {len(successful_files)}")
    print(f"- 分析失败: {len(failed_files)}")
    print(f"- 成功率: {len(successful_files)/len(results)*100:.1f}%")
    
    if successful_files:
        print(f"\n✅ 成功分析的文件:")
        for result in successful_files:
            print(f"  - {os.path.basename(result['file'])}")
    
    if failed_files:
        print(f"\n❌ 分析失败的文件:")
        for result in failed_files:
            print(f"  - {os.path.basename(result['file'])}")
    
    print(f"\n📁 分析结果保存在: ic_analysis_plot/ 目录下")
    print(f"   每个文件都有对应的子文件夹，包含完整的分析图表")

def main():
    """
    主函数
    """
    print("🚀 开始批量IC分析")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取所有数据文件
    data_files = get_data_files()
    
    if not data_files:
        print("❌ 没有找到需要分析的数据文件！")
        return
    
    print(f"\n📋 找到 {len(data_files)} 个数据文件:")
    for i, file_path in enumerate(data_files, 1):
        print(f"  {i}. {os.path.basename(file_path)}")
    
    # 确认是否继续
    print(f"\n是否开始批量分析？(y/n): ", end="")
    try:
        user_input = input().strip().lower()
        if user_input not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return
    except KeyboardInterrupt:
        print("\n❌ 用户取消操作")
        return
    
    # 开始批量分析
    results = []
    start_time = time.time()
    
    for i, file_path in enumerate(data_files, 1):
        print(f"\n🔄 进度: {i}/{len(data_files)}")
        
        file_start_time = time.time()
        success = run_single_analysis(file_path)
        file_time = time.time() - file_start_time
        
        results.append({
            'file': file_path,
            'success': success,
            'time': file_time
        })
        
        print(f"⏱️  耗时: {file_time:.1f} 秒")
    
    # 生成总结报告
    total_time = time.time() - start_time
    print(f"\n⏱️  总耗时: {total_time:.1f} 秒")
    print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    generate_summary_report(results)

if __name__ == "__main__":
    main() 