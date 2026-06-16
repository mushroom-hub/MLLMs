import os
from pathlib import Path

# 项目路径
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"

# 创建必要目录
FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== Qwen API 配置 ====================
# 使用阿里云 DashScope API
QWEN_API_TYPE = "dashscope"  # 支持: dashscope, openai, custom
QWEN_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "your-api-key-here")  # 从环境变量读取
QWEN_MODEL_ID = "qwen3.7-plus"  # 可选: qwen-plus, qwen-turbo, qwen-max 等
QWEN_API_CONFIG = {
    "api_type": QWEN_API_TYPE,
    "api_key": QWEN_API_KEY,
    "model": QWEN_MODEL_ID,
    "timeout": 30,
    "temperature": 0.7,
    "max_tokens": 16384,
}

# ==================== 嵌入模型配置 ====================
# 使用 ModelScope 本地下载的 m3e-base（中文语义向量模型，768 维）
# 下载命令: modelscope download --model AI-ModelScope/m3e-base --local_dir ./embedding/m3e-base
EMBEDDING_MODEL = str(BASE_DIR / "embedding" / "m3e-base")  # 本地模型目录
EMBEDDING_DIM = 768  # m3e-base 输出维度固定为 768

# ==================== FAISS 配置（按学科分类索引） ====================
# 每个学科一个独立的索引文件，便于按学科检索和管理
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"

# 索引文件路径模板（用 ASCII 文件名避免 Windows 编码问题）
# 运行时通过 subject_to_filename() 将中文转换后再 format
FAISS_INDEX_TEMPLATE = str(FAISS_INDEX_DIR / "{subject_fname}.index")
FAISS_METADATA_TEMPLATE = str(FAISS_INDEX_DIR / "{subject_fname}_metadata.json")


def subject_to_filename(subject: str) -> str:
    """将中文学科名转换为 ASCII 安全的文件代号。"""
    return SUBJECT_FILENAME.get(subject, subject.lower().replace(" ", "_"))

# 保留旧版全局索引路径（兼容旧数据自动迁移）
FAISS_INDEX_PATH = FAISS_INDEX_DIR / "knowledge_base.index"
FAISS_METADATA_PATH = FAISS_INDEX_DIR / "metadata.json"

FAISS_CONFIG = {
    "dimension": EMBEDDING_DIM,
    "metric_type": "L2",
    "nprobe": 10,  # 检索时查询的簇数
}

# ==================== RAG 配置 ====================
RAG_CONFIG = {
    "top_k": 5,  # 检索的文档数
    "context_window": 4096,  # 上下文窗口大小
    "similarity_threshold": 0.5,  # 相似度阈值
}

# ==================== 学科分类 ====================
# 重要：SUBJECT_FILENAME 将中文映射到 ASCII 安全的文件名
# （faiss 是 C++ 库，Windows 上无法读写含中文/非 ASCII 的路径）
SUBJECTS = [
    "数据结构",
    "计算机组成原理",
    "计算机网络",
    "操作系统",
    "算法与编程",
    "全部学科"
]

SUBJECT_FILENAME = {
    "数据结构": "data_structure",
    "计算机组成原理": "computer_organization",
    "计算机网络": "computer_network",
    "操作系统": "operating_system",
    "算法与编程": "algorithm",
    "全部学科": "all",
}

# ==================== 提示词模板 ====================
SYSTEM_PROMPT = """你是一个专业的计算机学科智能教学助手 EduBrain，具备以下能力：

1. **多模态理解**：能处理文本、代码、图片、截图等多种输入格式
2. **知识检索**：基于学生问题从知识库中检索相关资源
3. **深度解答**：提供结构化、层次清晰的答案，包含：
   - 核心概念解释
   - 原理深度分析
   - 实际应用示例
   - 常见误区提示
4. **教学引导**：采用启发式提问而非直接给答案，培养学生独立思考能力
5. **知识点追踪**：在答题后自动分类和沉淀知识点

当前助手设置：
- 目标学科：{subject}
- 回复语言：中文（简体）
- 教学风格：专业、清晰、耐心、富有启发性

请根据检索到的知识库内容，结合用户问题，给出专业的、符合教学逻辑的回答。"""

ANSWER_PROMPT = """基于以下检索到的知识内容，请回答用户问题：

【知识库检索结果】
{context}

【用户问题】
{question}

【回答要求】
1. 从知识库检索结果中汲取信息
2. 提供清晰、结构化的答案
3. 使用中文回答，确保学生能理解
4. 如适用，包含代码示例或图解说明
5. 指出关键知识点和常见误区

请提供专业的回答："""

# ==================== API 配置 ====================
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
    "cors_origins": ["http://localhost:5173", "http://localhost:3000"],
}

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "logs" / "app.log"