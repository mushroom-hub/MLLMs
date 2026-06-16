## 知识库搭建

知识库是 RAG 系统的"大脑"，搭建流程分为三步：

### 1. 数据来源

`dataset/` 目录中包含：

- **教材 PDF**：408 推荐用书（数据结构、计算机组成原理、计算机网络、操作系统等）
- **章节 JSON**：按章节切分的知识点 JSON 文档
- **编程题库**：LeetCode 等编程题的 Markdown 文件

### 2. 文档解析与分块

多模态处理器 (`MultimodalProcessor`) 负责格式转换：

- **PDF**：使用 PyMuPDF 按页提取文本，每页作为一个独立文档，记录 `{source, page, type}` 元数据
- **JSON**：按 `content/description` 字段提取文本，保留 `{id, title}` 元数据
- **代码**：保留完整代码内容，标注 `{language}`

### 3. 嵌入与建索引

核心构建流程（`backend/tools/build_index.py`）：
加载文档 → 文本嵌入（m3e-base，768维）→ 按学科写入 FAISS 索引 → 保存到 disk ↓ backend/data/faiss_index/ 

FAISS 采用 `IndexFlatL2`（L2 距离）作为基础索引类型。文档的相似度公式为：   
similarity = 1 / (1 + L2_distance)


大于 `similarity_threshold`（默认 0.5）的文档才会被视为相关。

### 4. 动态更新

除了离线批量构建，系统也支持在线添加文档：

- 通过前端上传 PDF → `POST /api/knowledge/upload` → 自动解析并加入指定学科索引
- 通过 API 动态添加 → RAG Engine 的 `add_knowledge()` 方法
