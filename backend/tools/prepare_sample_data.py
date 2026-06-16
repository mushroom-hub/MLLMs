"""
数据准备脚本
将现有的 dataset 转换为可用于知识库的格式
"""
import json
from pathlib import Path
from typing import List, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent))


def prepare_sample_documents() -> List[Dict]:
    """准备样本文档"""
    documents = [
        {
            "text": """B树和B+树的区别

1. 定义和结构
- B树：每个节点可以存储多个键值对，既存储索引又存储数据
- B+树：只在叶子节点存储数据，中间节点只存储索引

2. 查询性能
- B树：查询时可能提前返回
- B+树：必须遍历到叶子节点才能获得数据，但能提供更好的范围查询性能

3. 缓存性能
- B树：由于数据分散在各层，缓存效率较低
- B+树：由于数据集中在叶子层，缓存效率高

4. 应用场景
- B树：数据库索引
- B+树：文件系统和数据库索引（更常见）
""",
            "metadata": {
                "source": "teaching_material",
                "chapter": "数据结构高级",
                "difficulty": "intermediate"
            },
            "subject": "数据结构"
        },
        {
            "text": """计算机组成原理 - CPU 流水线

1. 流水线的基本概念
流水线是一种技术，将处理分解为多个独立的步骤，每个步骤由专用的硬件模块处理。

2. 经典 5 级流水线
- 取指 (IF): 从内存中取出指令
- 译码 (ID): 解码指令，获取寄存器值
- 执行 (EX): 执行 ALU 运算
- 访存 (MEM): 访问内存
- 写回 (WB): 将结果写回寄存器

3. 流水线冒险
- 结构冒险：硬件资源争用
- 数据冒险：指令间数据依赖
- 控制冒险：分支指令导致的问题

4. 性能分析
理想吞吐量 = 1 指令/时钟周期
实际吞吐量 = 1 / (1 + 平均停滞周期)
""",
            "metadata": {
                "source": "teaching_material",
                "chapter": "CPU设计",
                "difficulty": "advanced"
            },
            "subject": "计算机组成原理"
        },
        {
            "text": """计算机网络基础 - 神经网络

1. 神经元模型
一个人工神经元包含：
- 输入权重 (w_i)
- 偏置项 (b)
- 激活函数 (f)
输出 = f(∑w_i*x_i + b)

2. 常见激活函数
- ReLU: max(0, x)，稀疏性好，计算快
- Sigmoid: 1/(1+e^(-x))，输出范围 (0,1)
- Tanh: 输出范围 (-1,1)
- Softmax: 多分类输出

3. 反向传播算法
用链式法则计算梯度，实现高效的参数优化

4. 深度学习框架
- PyTorch：动态计算图
- TensorFlow：静态计算图
- JAX：函数式编程风格
""",
            "metadata": {
                "source": "teaching_material",
                "chapter": "深度学习",
                "difficulty": "advanced"
            },
            "subject": "计算机网络"
        }
    ]
    
    return documents


def save_sample_index():
    """保存样本索引数据"""
    from agent.embedding import EmbeddingManager
    from agent.retriever import FAISSRetriever
    
    documents = prepare_sample_documents()
    
    print(f"准备了 {len(documents)} 个样本文档")
    print("开始嵌入...")
    
    # 嵌入
    embedding_manager = EmbeddingManager()
    texts = [doc['text'] for doc in documents]
    embeddings = embedding_manager.embed_text(texts)
    
    # 保存到索引
    retriever = FAISSRetriever()
    retriever.add_documents(embeddings, documents)
    
    print("样本索引创建完成！")
    return True


if __name__ == '__main__':
    try:
        save_sample_index()
        print("\n样本数据已准备完毕，可以开始测试了！")
    except Exception as e:
        print(f"准备失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
