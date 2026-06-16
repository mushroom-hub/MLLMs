#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合计算机组成原理章节JSON文件脚本
将10个章节的JSON文件按照dataset.json的格式整合成一个文件
"""

import json
import os
from pathlib import Path

def merge_datasets():
    # 源目录
    source_dir = r"D:\university\大三\大三下\多模态大模型原理与应用\大作业\dataset\408\计算机组成原理"
    output_path = r"D:\university\大三\大三下\多模态大模型原理与应用\大作业\dataset\dataset_output\computer_organization_merged.json"
    
    # 收集所有数据
    merged_data = []
    
    # 定义章节文件列表
    chapter_files = [f"ch{i}.json" for i in range(1, 11)]
    
    for chapter_file in chapter_files:
        file_path = os.path.join(source_dir, chapter_file)
        
        if not os.path.exists(file_path):
            print(f"⚠️  警告：文件 {chapter_file} 不存在，跳过")
            continue
        
        print(f"📖 处理文件：{chapter_file}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)
            
            # 提取基本信息
            problem_id = chapter_data.get('problem_id', '')
            title = chapter_data.get('title', '')
            description = chapter_data.get('description', '')
            images = chapter_data.get('images', [])
            source_file = chapter_data.get('source_file', chapter_file)
            
            # 处理解答部分
            solutions = chapter_data.get('solutions', {})
            question_answers = solutions.get('question_answer', [])
            
            # 将每个问答对转换为独立的对象
            for idx, qa in enumerate(question_answers, 1):
                item = {
                    "problem_id": f"{problem_id}_{idx:02d}",
                    "title": qa.get('title', f"Problem {idx}"),
                    "type": qa.get('type', ''),
                    "description": qa.get('answer', ''),  # 答案作为description
                    "solutions": {
                        "text": qa.get('answer', '')  # 保存完整答案
                    },
                    "images": images,
                    "source_file": source_file,
                    "chapter": problem_id,
                    "original_type": qa.get('type', '')
                }
                merged_data.append(item)
            
            print(f"   ✓ 提取了 {len(question_answers)} 个问答对")
        
        except json.JSONDecodeError as e:
            print(f"   ✗ 错误：文件格式不正确 - {e}")
            continue
        except Exception as e:
            print(f"   ✗ 错误：{e}")
            continue
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 保存合并后的数据
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 成功！")
    print(f"   总共处理：{len(chapter_files)} 个章节文件")
    print(f"   整合数据：{len(merged_data)} 个问答对")
    print(f"   输出文件：{output_path}")

if __name__ == "__main__":
    merge_datasets()
