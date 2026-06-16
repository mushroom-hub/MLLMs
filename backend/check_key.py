"""
后端Qwen推理模块测试脚本
运行方式：python test_qwen.py
"""
from agent.qwen_inference import QwenInference
import os
from dotenv import load_dotenv
import dashscope

# 运行测试时，先加载当前目录下的 .env 文件
load_dotenv() 

# 显式注入
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

if __name__ == "__main__":
    # 初始化推理实例
    llm = QwenInference()
    
    print("===== 1.1 单轮纯文本 generate 测试 =====")
    ans1_text = llm.generate("简单解释RAG检索增强生成的完整工作流程")
    print("模型回答：\n", ans1_text)

    print("\n===== 1.2 单轮多模态图片 generate 测试 (严格对照官方事例) =====")
    test_img = "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
    ans1_img = llm.generate(text="图中描绘的是什么景象?", image_url=test_img)
    print("模型视觉回答：\n", ans1_img)

    print("\n===== 2. 多轮chat+系统提示词测试 =====")
    # 支持传入纯文本形式的 history，代码内部会自动包裹成符合官方规范的格式
    history = [
        {"role": "user", "content": "什么是大模型上下文窗口？"},
        {"role": "assistant", "content": "上下文窗口是大模型单次能读取处理的全部token长度。"}
    ]
    ans2 = llm.chat(
        messages=history,
        system_prompt="你是计算机专业助教，回答简洁易懂，分点说明",
        temperature=0.3
    )
    print("多轮对话回答：\n", ans2)

    print("\n===== 3. 提取推理步骤测试 =====")
    test_text = """
    RAG工作流程分为4步：
    1. 文档切片与向量化
    2. 向量库存储
    3. 用户问题检索匹配
    4. 检索结果拼接上下文送入大模型生成答案
    """
    steps = llm.extract_reasoning_steps(test_text)
    print("提取推理步骤：", steps)

    print("\n===== 4. 引擎状态测试 =====")
    print(llm.get_stats())