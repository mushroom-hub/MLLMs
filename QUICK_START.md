<!-- 快速开始指南 -->

# 🚀 EduBrain AI - 快速开始指南

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

## 快速启动（5 分钟）

### 步骤 1：检查环境

```bash
# 检查 Python 版本（需要 3.10+）
python --version

# 检查 Node.js 版本（前端需要 18+）
node --version
```

### 步骤 2：安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

> 如果出现 CUDA 相关错误，可以安装 CPU 版本的依赖（速度会慢）

### 步骤 3：准备知识库（可选但推荐）

```bash
# 方式一：使用示例数据快速测试
python tools/prepare_sample_data.py

# 方式二：使用完整的 dataset 数据
python tools/build_index.py --source dataset
```
### 步骤 4：设置API_key
请务必根据`./backend/API_SETUP.md`指南，将API key替换为你自己的API密钥

### 步骤 5：启动后端

```bash
# Windows
run_backend.bat

# Linux/Mac
bash run_backend.sh

# 或直接运行
python web/app.py
```

后端启动后会输出：
```
* Running on http://0.0.0.0:5000
```

### 步骤 6：启动前端（新终端窗口）

```bash
cd ../UI
npm run dev
```

前端会在浏览器中自动打开 `http://localhost:5173`



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

## 常见问题

### Q：后端启动失败，提示模型路径错误
**A**：编辑 `backend/config.py`，更正 `QWEN_MODEL_PATH`：
```python
QWEN_MODEL_PATH = r"C:\Users\HP\.cache\modelscope\hub\models\Qwen\Qwen3.7-plus"
```

### Q：前端无法连接后端
**A**：检查：
1. 后端是否运行在 `http://localhost:5000`
2. 是否关闭了防火墙
3. 浏览器控制台是否有 CORS 错误

### Q：检索不到文档
**A**：
1. 确保运行了 `python tools/build_index.py`
2. 检查 `data/faiss_index/` 文件夹是否存在
3. 查看 `logs/app.log` 日志

### Q：显存不足
**A**：
- 默认使用 4-bit 量化，显存占用 ~8GB
- 如果仍然不足，在 `config.py` 中改为：
```python
QWEN_CONFIG["device"] = "cpu"  # 使用 CPU（会很慢）
```

### Q：怎样添加自己的知识库
**A**：
1. 准备 JSON 格式的文档
2. 放入或修改 `backend/data/` 目录
3. 运行 `python tools/build_index.py`


## 开发调试

### 启用调试日志

编辑 `backend/config.py`：
```python
LOG_LEVEL = "DEBUG"  # 显示详细日志
```

### 测试单个模块

```bash
# 测试 Qwen 推理
python -c "from agent.qwen_inference import QwenInference; q = QwenInference()"

# 测试嵌入
python -c "from agent.embedding import EmbeddingManager; e = EmbeddingManager(); print(e.embed_text('test'))"

# 测试 RAG
python -c "from agent.rag import RAGEngine; rag = RAGEngine(); print(rag.answer_question('什么是B树'))"
```

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


