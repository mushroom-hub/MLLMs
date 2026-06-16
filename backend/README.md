# EduBrain AI 后端 - 基于多模态大模型与 RAG 的计算机学科智能辅导

## 项目简介

EduBrain AI 是一个基于 Qwen2.5-VL 视觉语言模型和 RAG（检索增强生成）技术的计算机学科智能教学助手。该系统支持多模态输入（文本、图片、代码、PDF），能够从知识库中检索相关内容，并生成专业的教学答案。

## 系统架构

```
frontend (React + TypeScript)
         |
         v
    Flask API (后端)
    |         |         |
    v         v         v
  RAG引擎   多模态处理  对话管理
    |         |         |
    +----+----+----+----+
         |
    Qwen2.5-VL 模型
    嵌入模型 (text2vec)
    FAISS 向量索引
```

## 核心模块

### 1. `agent/qwen_inference.py` - Qwen 推理模块
- 加载和推理 Qwen2.5-VL 模型
- 支持多轮对话生成
- 自动提取推理步骤

### 2. `agent/embedding.py` - 嵌入管理
- 文本向量化
- 图像特征提取
- 文档批量嵌入

### 3. `agent/retriever.py` - FAISS 检索
- 向量索引管理
- 相似度搜索
- 元数据存储

### 4. `agent/rag.py` - RAG 引擎
- 统筹检索和生成流程
- 上下文拼接
- 答案生成

### 5. `agent/multimodal.py` - 多模态处理
- PDF 文本提取
- 图像 OCR
- 代码识别

### 6. `agent/dialog_manager.py` - 对话管理
- 会话历史维护
- 上下文管理
- 会话持久化

### 7. `web/app.py` - Flask API
- HTTP 接口
- 文件上传处理
- CORS 支持

## 安装与配置

### 前置要求
- Python 3.10+
- CUDA 11.8+（推荐）
- 24GB+ VRAM（运行 Qwen 模型）
- Node.js 18+ (仅前端需要)

### 1. 克隆项目并安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置模型路径

编辑 `config.py`，确保 `QWEN_MODEL_PATH` 指向您下载的 Qwen 模型：

```python
QWEN_MODEL_PATH = r"C:\Users\HP\.cache\modelscope\hub\models\Qwen\Qwen2___5-VL-7B-Instruct"
```

### 3. 构建知识库索引

```bash
python tools/build_index.py --source dataset
```

这会从 `dataset/` 文件夹扫描数据并构建 FAISS 向量索引。

## 运行

### 启动后端服务

```bash
python web/app.py
```

后端会在 `http://localhost:5000` 监听。

### 启动前端（在 UI 文件夹）

```bash
cd ../UI
npm run dev
```

前端会在 `http://localhost:5173` 运行。

## API 文档

### 1. 发送消息
```http
POST /api/chat/send
Content-Type: multipart/form-data

session_id: "optional"
message: "用户问题"
subject: "数据结构" | "计算机组成原理" | "全部学科"
files: [上传的文件]
```

**响应**:
```json
{
  "status": "success",
  "session_id": "session-123",
  "user_message": {
    "id": "msg-1",
    "role": "user",
    "content": "...",
    "timestamp": "2024-06-12T10:00:00",
    "subject": "数据结构",
    "attachments": []
  },
  "ai_message": {
    "id": "msg-2",
    "role": "ai",
    "content": "...",
    "reasoning_steps": ["步骤1", "步骤2"],
    "retrieved_documents": [...]
  }
}
```

### 2. 获取对话历史
```http
GET /api/chat/history?session_id=session-123&limit=10
```

### 3. 获取消息溯源
```http
GET /api/chat/source/msg-2?session_id=session-123
```

返回该消息检索到的文档源。

### 4. 清空会话
```http
POST /api/chat/clear
Content-Type: application/json

{
  "session_id": "session-123"
}
```

### 5. 获取学科列表
```http
GET /api/subjects
```

### 6. 系统统计
```http
GET /api/stats
```

## 数据流

```
用户输入 (文本/图片/代码/PDF)
    |
    v
[多模态处理]
    |
    v
[学科分类]
    |
    v
[Embedding 嵌入]
    |
    v
[FAISS 检索] ---> 获取相关文档
    |
    v
[上下文拼接]
    |
    v
[Qwen 生成] ---> 生成答案
    |
    v
[推理步骤提取]
    |
    v
返回结果 (答案 + 推理步骤 + 溯源)
```

## 配置参数

编辑 `config.py` 调整以下参数：

```python
# RAG 配置
RAG_CONFIG = {
    "top_k": 5,              # 检索文档数
    "context_window": 4096,  # 上下文窗口大小
    "similarity_threshold": 0.5  # 相似度阈值
}

# Qwen 模型配置
QWEN_CONFIG = {
    "quantization": "4bit",  # 4-bit 量化以节省显存
    "device": "cuda"         # 使用 GPU
}

# API 配置
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "cors_origins": ["http://localhost:5173"]
}
```

## 检索与归类机制

### 1. 文本嵌入 — m3e-base

**m3e-base** 是面向中文的 sentence-transformers 格式模型，输出 768 维语义向量。

加载策略（`backend/agent/embedding.py`）：

1. **优先本地加载**：从 `backend/embedding/m3e-base/` 目录加载，完全离线运行
2. **回退方案**：若本地模型不可用，调用 DashScope `text-embedding-v2` API（1024 维）

嵌入方法：
```python
embedding = embedding_manager.embed_text("B树和B+树有什么区别？")
# 返回 shape: (1, 768) 的 float32 向量
```

### 2. FAISS 向量检索

检索流程（`backend/agent/retriever.py` 中 `search()` 方法）：
用户问题 → 嵌入为向量 → 在目标学科索引中搜索 top_k*2 条 ↓ 计算相似度 = 1/(1+L2距离) ↓ 过滤相似度 < 阈值的文档 ↓ 跨学科合并排序，返回 top_k 条

支持两种检索范围：
- **指定学科**：仅在该学科索引中检索（速度快、精准度高）
- **全部学科**：遍历所有学科索引，合并结果后统一排序（适合模糊问题）

### 3. RAG（检索增强生成）

完整问答流水线（`backend/agent/rag.py` 中 `answer_question()` 方法）：
- 第 1 步：检索相关文档 调用 retrieve_context(question, top_k=5, subject) ↓ 从 FAISS 获取 5 条最相关的教学资料

- 第 2 步：组装 Prompt SYSTEM_PROMPT（教学助手角色定义） + ANSWER_PROMPT（检索内容 + 用户问题） ↓ 传给 Qwen 模型

- 第 3 步：生成答案 调用 qwen_model.chat() 生成专业回答

- 第 4 步：提取推理步骤 从答案中解析数字编号的步骤（"1. xxx 2. yyy"） 若无法解析则按中文句号切分

- 第 5 步：置信度评估 调用 evaluate_confidence() 让 Qwen 评估答案与检索文档的一致性 返回 {score, level, summary}

- 第 6 步：组装知识源 将检索文档格式化为前端友好格式 包含 {id, title, source, page, relevance, excerpt, similarity}

### 4. 自动学科识别（detect_subject）
输入问题 → 双层打分 ↓ ├─ 关键词规则（权重 0.6） │ ├─ 命中"链表/树/图" → 数据结构高分 │ ├─ 命中"CPU/指令/寄存器" → 计算机组成原理高分 │ ├─ 命中"TCP/IP/路由" → 计算机网络高分 │ └─ 命中"进程/线程/调度" → 操作系统高分 │ └─ 各学科 FAISS 检索（权重 0.4） └─ 在每个学科索引中独立检索，取平均相似度 ↓ 得分最高的学科即为识别结果 若所有学科得分 < 0.1，标记为"全部学科"

## 常见问题

### 1. 模型加载失败
- 确认 Qwen 模型路径正确
- 检查磁盘空间（模型需要 ~30GB）
- 验证 CUDA 驱动版本

### 2. 检索无结果
- 确保运行过 `python tools/build_index.py`
- 检查 `data/faiss_index/` 文件夹是否存在索引文件

### 3. 前后端连接失败
- 确认后端运行在 `http://localhost:5000`
- 检查防火墙设置
- 验证 CORS 配置

## 测试

### 单元测试

```bash
python -m pytest tests/ -v
```

### 集成测试

```bash
# 测试 RAG 引擎
python tests/test_rag.py

# 测试 API
python tests/test_api.py
```

## 日志

日志输出到 `logs/app.log`，可在 `config.py` 中调整日志级别：

```python
LOG_LEVEL = "INFO"  # 调整为 DEBUG 获取更多信息
```

## 开发指南

### 添加新的知识源

1. 准备文档（支持 JSON、PDF、TXT 格式）
2. 放入 `data/raw/` 文件夹
3. 运行 `python tools/build_index.py`

### 自定义 Prompt

编辑 `config.py` 中的 `SYSTEM_PROMPT` 和 `ANSWER_PROMPT`：

```python
SYSTEM_PROMPT = """你是一个专业的计算机学科教学助手..."""
ANSWER_PROMPT = """基于以下知识库内容，回答用户问题..."""
```

### 扩展多模态能力

在 `agent/multimodal.py` 中添加新的处理方法：

```python
def process_custom_format(self, file_path: str) -> Dict:
    # 实现自定义格式处理
    pass
```

## 许可证

© 2026 EduBrain AI. All rights reserved.

## 支持

遇到问题？请查看：
- `docs/` 文件夹中的详细文档
- GitHub Issues
- 联系技术支持

---

**开发者**: 彭怡萱、谈栩言、陈海裕  
**最后更新**: 2026-06-12
