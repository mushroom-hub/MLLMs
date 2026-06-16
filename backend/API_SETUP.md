# API 版本快速开始指南

## 1. 获取 API Key

### 阿里云 DashScope（推荐）
1. 访问 https://dashscope.console.aliyun.com/
2. 注册或登录阿里云账号
3. 创建 API Key
4. 复制 API Key

## 2. 配置环境变量

在 `backend/` 目录下创建 `.env` 文件：

```bash
DASHSCOPE_API_KEY=sk-your-api-key-here
QWEN_MODEL=qwen-plus
```

或在系统环境变量中设置：

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY = "sk-your-api-key-here"

# Linux/macOS
export DASHSCOPE_API_KEY="sk-your-api-key-here"
```

## 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 4. 启动后端服务

```bash
python web/app.py
```

服务将在 `http://localhost:5000` 启动

## 5. 启动前端

```bash
cd UI
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 配置说明

核心配置文件：`backend/config.py`

### 1. API 与模型配置

```python
# Qwen 大语言模型（通过阿里云 DashScope API 调用）
QWEN_API_TYPE = "dashscope"
QWEN_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "your-api-key-here")
QWEN_MODEL_ID = "qwen3.7-plus"  # 支持多模态

QWEN_API_CONFIG = {
    "api_type": "dashscope",
    "api_key": "...",
    "model": "qwen3.7-plus",
    "timeout": 30,
    "temperature": 0.7,       # 生成多样性：0 更确定，1 更随机
    "max_tokens": 16384,      # 单次回答最大 token 数
}
```

### 2.对话接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/send` | 发送消息（核心问答接口） |
| GET | `/api/chat/history?session_id=xxx&limit=10` | 获取对话历史 |
| GET | `/api/chat/source/{message_id}?session_id=xxx` | 获取单条消息的溯源文档 |
| POST | `/api/chat/clear` | 清空指定会话的历史 |

### 3.知识库管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/upload` | 上传文档到指定学科知识库 |
| GET | `/api/knowledge/documents?subject=xxx&limit=100` | 查看知识库文档 |
| POST | `/api/knowledge/clear` | 清空指定学科的知识库索引 |

### 4.其他接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/subjects` | 获取所有学科及文档数统计 |
| GET | `/api/stats` | 获取系统运行统计 |
| GET | `/api/health` | 健康检查 |

## API 端点

- **健康检查**: `GET /api/health`
- **发送消息**: `POST /api/chat/send`
- **获取历史**: `GET /api/chat/history?session_id=xxx`
- **获取源文档**: `GET /api/chat/source/<message_id>?session_id=xxx`
- **清空会话**: `POST /api/chat/clear`
- **获取学科**: `GET /api/subjects`
- **系统统计**: `GET /api/stats`

## 模型选择

可用的 Qwen 模型：
- `qwen-turbo`: 速度快，成本低（推荐用于简单任务）
- `qwen-plus`: 平衡性能和成本（推荐用于一般任务）
- `qwen-max`: 最强性能（用于复杂任务）
- `qwen-long`: 支持更长的上下文

在 `config.py` 中修改 `QWEN_MODEL_ID` 即可切换模型。

## 常见问题

### Q: API Key 不生效？
- 检查是否正确设置了环境变量 `DASHSCOPE_API_KEY`
- 确保 API Key 有效且未过期
- 检查网络连接

### Q: 如何查看日志？
- 启动时会输出详细日志到控制台
- 检查是否有错误信息

### Q: 如何切换不同的 Qwen 模型？
修改 `config.py` 中的 `QWEN_MODEL_ID` 字段即可。
