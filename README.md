# EduBrain AI - 计算机学科智能辅导Agent

组员：

23336193 彭怡萱

23336216 谈栩言

23336036    陈海裕
 
## 项目结构

```
大作业/
├── backend/                  # Python 后端（核心）
│   ├── agent/
│   │   ├── qwen_inference.py    # Qwen 模型推理
│   │   ├── embedding.py         # 文本/图像嵌入
│   │   ├── retriever.py         # FAISS 向量检索
│   │   ├── rag.py               # RAG 引擎（核心）
│   │   ├── multimodal.py        # 多模态处理（PDF/图片/代码）
│   │   └── dialog_manager.py    # 对话管理
│   ├── web/
│   │   └── app.py              # Flask API 服务
│   ├── tools/
│   │   ├── build_index.py      # 构建知识库索引
│   │   └── prepare_sample_data.py  # 准备示例数据
│   ├── data/
│   │   └── faiss_index/        # 向量索引存储
│   ├── config.py               # 全局配置
│   ├── requirements.txt        # Python 依赖
│   └── README.md              # 详细文档
│
├── UI/                        # React 前端
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── pages/            # 页面
│   │   └── lib/
│   │       └── api.ts        # 后端 API 客户端
│   ├── package.json
│   └── run_ui.py
│
├── dataset/                   # 教学数据集
└── 开题/                      # 课题文档
```

## 核心功能

### 1. 多模态输入支持

系统接受以下输入类型：

| 类型 | 说明 | 处理方式 |
|------|------|---------|
| 📝 纯文本 | 用户直接输入问题 | 直接进行语义检索 |
| 🖼️ 图片 | 截图、照片等 | 调用 Qwen 多模态模型直接分析图像 |
| 📄 PDF 文档 | 上传教材、讲义 | PyMuPDF 自动提取文本并入知识库 |
| 💻 代码文件 | .py / .java / .cpp 等 | 自动识别代码内容并检索 |

实现代码：`backend/agent/multimodal.py`

### 2. 自动学科归类

用户输入问题时，系统会**自动识别**该问题属于哪个学科，无需手动切换：

- **关键词规则打分**：命中"链表""TCP""进程"等领域术语时提高对应学科分数
- **各学科 FAISS 索引独立检索**：用语义相似度补充模糊场景
- **融合策略**：规则得分 × 0.6 + 检索得分 × 0.4，取最高分学科

支持学科：
- 数据结构
- 计算机组成原理
- 计算机网络
- 操作系统
- 全部学科（跨学科检索）

实现代码：`backend/agent/rag.py` 中的 `detect_subject()` 方法（约 396-479 行）

### 3. 知识库管理

提供完整的知识库生命周期管理：

- **上传文档**：通过前端或 API 上传 PDF/TXT/JSON 文档，自动按学科分类入索引
- **查看文档**：列出知识库中的文档摘要（来源、页码、预览）
- **清空索引**：按学科清空或全局清空

实现代码：`backend/agent/retriever.py` 中的 `add_documents()` / `list_documents()` / `clear_subject()`

### 4. 置信度评估与知识源查看

每条 AI 回答都附带：

- **置信度评分**：由 Qwen 模型基于「回答内容是否与检索文档一致」「是否完整覆盖问题」等维度打分（0-1.0）
- **置信度等级**：高 / 中 / 低
- **评分摘要**：一句话说明评分理由
- **知识源列表**：每条检索文档包含标题、来源、页码、相关性百分比、内容摘要

当置信度较低时，提示用户"该回答基于通用学科知识，请注意核对"。

实现代码：`backend/agent/rag.py` 中的 `evaluate_confidence()` 方法（约 251-393 行）

### 5. 对话记忆

每个会话维护独立的对话历史：

- 自动生成唯一 Session ID
- 支持查看最近 N 条消息
- 支持清空历史
- 可导出/加载为 JSON 文件

实现代码：`backend/agent/dialog_manager.py`

---

## 技术选型

### 后端技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 编程语言 | Python 3.10+ | |
| Web 框架 | Flask | 轻量级 HTTP 服务 |
| 大语言模型 | Qwen 3.7-plus | 通过阿里云 DashScope API 调用 |
| 文本嵌入 | m3e-base（本地） | 中文语义向量模型，768 维，sentence-transformers 格式 |
| 向量检索 | FAISS | Facebook 开源向量索引库，支持高性能相似度检索 |
| PDF 解析 | PyMuPDF (fitz) | 提取 PDF 文本内容 |
| 图像处理 | Pillow | 图片格式处理 |

### 前端技术栈

| 组件 | 选型 | 
|------|------|
| 框架 | React 18 | 
| 语言 | TypeScript | 
| 样式 | TailwindCSS + Radix UI | 
| 构建工具 | Vite | 

### 关键设计决策

1. **学科独立索引**：每个学科维护一个独立的 FAISS 索引文件，便于按学科检索、按需加载与清理。
2. **本地嵌入优先**：采用本地 m3e-base 模型完成文本向量化，避免频繁调用云端 API，兼顾隐私与成本。
3. **API 调用大模型**：Qwen 通过 DashScope API 调用，降低本地显存压力（无需 24GB+ 显卡）。
4. **ASCII 文件名策略**：FAISS 的 C++ fopen() 在 Windows 上无法处理中文路径，通过 `subject_to_filename()` 将学科名映射为 ASCII。

---

## 提示词模板
**系统提示词（SYSTEM_PROMPT）** — 定义 AI 角色：
```
你是一个专业的计算机学科智能教学助手 EduBrain，具备以下能力：

多模态理解：能处理文本、代码、图片、截图等多种输入格式
知识检索：基于学生问题从知识库中检索相关资源
深度解答：提供结构化、层次清晰的答案，包含：
核心概念解释
原理深度分析
实际应用示例
常见误区提示
教学引导：采用启发式提问而非直接给答案，培养学生独立思考能力
知识点追踪：在答题后自动分类和沉淀知识点
当前助手设置：

目标学科：{subject}
回复语言：中文（简体）
教学风格：专业、清晰、耐心、富有启发性
请根据检索到的知识库内容，结合用户问题，给出专业的、符合教学逻辑的回答。
```

**回答提示词（ANSWER_PROMPT）** — 组装检索内容与问题：
```
基于以下检索到的知识内容，请回答用户问题：

【知识库检索结果】 {context} ← 这里填入 FAISS 检索到的 top_k 条文档内容

【用户问题】 {question} ← 这里填入用户的原始问题

【回答要求】

从知识库检索结果中汲取信息
提供清晰、结构化的答案
使用中文回答，确保学生能理解
如适用，包含代码示例或图解说明
指出关键知识点和常见误区
请提供专业的回答：
```

## 使用示例

### 基础问答流程

1. **选择学科**：在侧边栏选择"数据结构"
2. **输入问题**：在输入框输入"B树和B+树有什么区别"
3. **上传资料**（可选）：可以上传 PDF、图片或代码
4. **查看答案**：AI 会生成答案和推理步骤
5. **查看溯源**：点击答案旁的"溯源"按钮查看检索到的文档

### 上传文件进行问答

```
支持的文件格式：
- PDF 文档（自动提取文本）
- 图片（自动 OCR 识别）
- 文本文件（.txt）
```

## 关键模块说明

### 1. Qwen 模型集成 (`agent/qwen_inference.py`)
- **功能**：加载 Qwen2.5-VL 模型并执行推理
- **特性**：
  - 4-bit 量化（降低显存占用）
  - 多轮对话支持
  - 自动提取推理步骤

### 2. RAG 引擎 (`agent/rag.py`)
- **流程**：
  1. 用户输入 → 文本嵌入
  2. FAISS 检索相关文档（top-5）
  3. 拼接上下文 + 用户问题
  4. 调用 Qwen 生成答案
  5. 提取推理步骤返回

### 3. 多模态处理 (`agent/multimodal.py`)
- 支持 PDF 文本提取
- 图像 OCR（PaddleOCR）
- 代码格式识别

## API 接口

详见 `API_SETUP.md`


### 发送消息

```http
POST /api/chat/send
Content-Type: multipart/form-data

参数：
- session_id: 会话ID（可选）
- message: 问题文本
- subject: 学科分类（数据结构|计算机组成原理|全部学科）
- files: 上传的文件（可选，多个）

响应：
{
  "status": "success",
  "session_id": "abc123",
  "user_message": {...},
  "ai_message": {
    "content": "回复文本",
    "reasoning_steps": ["步骤1", "步骤2"],
    "retrieved_documents": [...]
  }
}
```

### 获取对话历史

```http
GET /api/chat/history?session_id=abc123&limit=10
```

### 获取消息溯源

```http
GET /api/chat/source/msg-id?session_id=abc123
```

## 性能指标

| 指标 | 值 |
|------|-----|
| 显存占用 | ~8GB（4-bit 量化） |
| 首次回复时间 | 3-5 秒 |
| 平均回复长度 | 200-300 词 |
| 最大文件上传 | 50MB |
| 会话并发数 | 取决于硬件 |

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | Qwen2.5-VL 7B |
| 向量DB | FAISS |
| 后端框架 | Flask |
| 前端框架 | React 18 + TypeScript |
| UI 库 | TailwindCSS + Radix UI |
| 嵌入模型 | text2vec-large-chinese |
| OCR | PaddleOCR |

## 文件清单

### 核心后端代码
-  `backend/config.py` - 全局配置
-  `backend/agent/qwen_inference.py` - Qwen 推理
-  `backend/agent/embedding.py` - 文本嵌入
-  `backend/agent/retriever.py` - FAISS 检索
-  `backend/agent/rag.py` - RAG 核心
-  `backend/agent/multimodal.py` - 多模态处理
-  `backend/agent/dialog_manager.py` - 对话管理
-  `backend/web/app.py` - Flask API
-  `backend/tools/build_index.py` - 索引构建
-  `backend/tools/prepare_sample_data.py` - 样本数据

### 前端代码
-  `UI/src/lib/api.ts` - 后端 API 客户端

### 文档
-  `backend/README.md` - 详细说明
-  `QUICK_START.md` - 本文件

---
