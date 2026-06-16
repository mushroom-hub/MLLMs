"""
Flask API 后端服务
为前端提供 HTTP 接口
"""

# ==================== 紧急修复：绕过 Windows 损坏的系统证书 ====================
import os
import ssl

# 1. 禁用全局 HTTPS 证书验证，防止 Python 读取系统损坏的证书引发 ASN1 错误
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['PYTHONHTTPSVERIFY'] = '0'

# 2. 强行对 aiohttp 的 ClientSession 进行猴子补丁（Monkey Patch），默认关闭 ssl 校验
try:
    import aiohttp
    orig_init = aiohttp.ClientSession.__init__
    def patched_init(self, *args, **kwargs):
        if 'connector' not in kwargs:
            kwargs['connector'] = aiohttp.TCPConnector(ssl=False)
        orig_init(self, *args, **kwargs)
    aiohttp.ClientSession.__init__ = patched_init
except Exception:
    pass
# ==============================================================================

# ========== 第一步：优先加载环境变量 ==========
from dotenv import load_dotenv
# 当前文件在 backend/web，backend文件夹下有.env，直接读取同级backend/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

# ========== 再执行你原来所有导入代码 ==========
import logging
import sys
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from typing import Dict, Any
from pathlib import Path
import traceback

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_CONFIG, SUBJECTS
# 所有agent导入全部在load_dotenv之后！
from agent.rag import RAGEngine
from agent.dialog_manager import DialogManager
from agent.multimodal import MultimodalProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)

# ============ 安全 JSON 序列化 ============
# Flask 默认 jsonify 不识别 numpy.float32 / numpy.int64 等类型
# 这里全局注入自定义编码器，并提供 safe_jsonify 作为统一入口
import json
import numpy as np


class NumpySafeEncoder(json.JSONEncoder):
    """自动把 numpy 类型 -> Python 原生类型。"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (bytes, bytearray)):
            try:
                return obj.decode('utf-8')
            except Exception:
                return str(obj)
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


app.json_encoder = NumpySafeEncoder


def _to_native(obj):
    """递归地把 dict/list 中的 numpy 类型/bytes 转换为 Python 原生类型。"""
    try:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return [_to_native(x) for x in obj.tolist()]
    except Exception:
        pass
    if isinstance(obj, (bytes, bytearray)):
        try:
            return obj.decode('utf-8')
        except Exception:
            return str(obj)
    if isinstance(obj, dict):
        return {str(k): _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(x) for x in obj]
    return obj


def safe_jsonify(data: dict):
    """替代 Flask jsonify：自动清洗 numpy 类型后输出 JSON。"""
    from flask import Response
    native = _to_native(data)
    body = json.dumps(native, ensure_ascii=False, default=str)
    return Response(body, status=200, mimetype='application/json; charset=utf-8')


# ⭐ 覆盖 Flask 原生 jsonify：所有 return jsonify(...) 自动走安全版本
jsonify = safe_jsonify

# 配置 CORS
CORS(app, resources={
    r"/*": {
        "origins": API_CONFIG["cors_origins"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 初始化核心模块
try:
    rag_engine = RAGEngine()
    logger.info("RAG 引擎初始化成功")
except Exception as e:
    logger.error(f"RAG 引擎初始化失败: {e}")
    rag_engine = None

# 多模态处理器
multimodal_processor = MultimodalProcessor()

# 会话管理（简化版，实际应该使用 Redis）
sessions: Dict[str, DialogManager] = {}

# 上传文件配置
UPLOAD_FOLDER = Path("./uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'java', 'cpp', 'js', 'ts'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 限制


def allowed_file(filename: str) -> bool:
    """检查文件类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_or_create_session(session_id: str = None) -> DialogManager:
    """获取或创建会话"""
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    new_session = DialogManager(session_id)
    sessions[new_session.session_id] = new_session
    return new_session


# ==================== API 路由 ====================

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'EduBrain AI 服务正常'
    }), 200


@app.route('/api/chat/send', methods=['POST'])
def send_message():
    """
    发送消息接口
    
    请求体:
    {
        "session_id": "optional-session-id",
        "message": "用户问题文本",
        "subject": "数据结构|计算机组成原理|全部学科",
        "files": [file list]  # 可选的上传文件（支持图片）
    }
    """
    try:
        # 获取请求数据
        session_id = request.form.get('session_id')
        message_text = request.form.get('message', '').strip()
        subject = request.form.get('subject', '全部学科')
        files = request.files.getlist('files')
        
        # 调试日志
        logger.info(f"接收到的文件数量: {len(files)}")
        for i, f in enumerate(files):
            if f and f.filename:
                logger.info(f"文件 {i+1}: {f.filename}, 类型: {f.content_type}")
        
        # 验证输入
        if not message_text and not files:
            return jsonify({
                'status': 'error',
                'message': '消息或文件不能为空'
            }), 400
        
        if subject not in SUBJECTS:
            return jsonify({
                'status': 'error',
                'message': f'无效的学科分类: {subject}'
            }), 400
        
        # 获取或创建会话
        session = get_or_create_session(session_id)
        
        # 处理上传的文件
        attachments = []
        processed_docs = []
        image_paths = []  # 收集图片路径用于多模态问答
        
        for file in files:
            try:
                if not file or not file.filename:
                    continue
                    
                if not allowed_file(file.filename):
                    logger.warning(f"不支持的文件类型: {file.filename}")
                    continue
                    
                # 安全处理文件名，但保留扩展名
                original_filename = file.filename
                filename = secure_filename(file.filename)
                
                # 确保保留扩展名
                if '.' in original_filename:
                    ext = original_filename.rsplit('.', 1)[1].lower()
                    if '.' not in filename:
                        filename = f"{filename}.{ext}"
                        print(filename)
                    print(ext)
                
                file_path = app.config['UPLOAD_FOLDER'] / filename
                
                # 保存文件
                file.save(file_path)
                logger.info(f"文件已保存: {file_path}")
                
                attachments.append({
                    'name': filename,
                    'type': file.content_type
                })
                
                # 检查文件类型
                file_parts = filename.rsplit('.', 1)
                if len(file_parts) > 1:
                    file_ext = file_parts[1].lower()
                else:
                    file_ext = ''
                
                if file_ext and file_ext in IMAGE_EXTENSIONS:
                    # 图片文件 - 用于多模态问答
                    image_paths.append(str(file_path))
                    logger.info(f"检测到图片: {filename}")
                elif file_ext == 'pdf':
                    # PDF 文件 - 提取文本并按学科分类添加到知识库
                    logger.info(f"开始处理 PDF 文件: {filename}（学科: {subject}）")
                    docs = multimodal_processor.process_file(str(file_path))
                    processed_docs.extend(docs)
                    
                    if docs and rag_engine:
                        logger.info(f"将 PDF 内容添加到 [{subject}] 知识库，共 {len(docs)} 页")
                        success = rag_engine.add_knowledge(docs, subject=subject)
                        if success:
                            logger.info(f"PDF 内容已成功添加到 [{subject}] 知识库")
                        else:
                            logger.error("PDF 内容添加失败")
                    else:
                        logger.info(f"处理 PDF 文件: {filename}")
                else:
                    # 其他文件类型
                    docs = multimodal_processor.process_file(str(file_path))
                    processed_docs.extend(docs)
                    logger.info(f"处理文件: {filename}")
            except Exception as e:
                logger.error(f"处理文件 {file.filename if file else 'unknown'} 时出错: {e}")
        
        # 添加用户消息
        user_msg = session.add_message(
            role='user',
            content=message_text,
            subject=subject,
            attachments=attachments
        )
        
        # 判断是否需要多模态问答（有图片时）
        if image_paths:
            # 使用多模态模型直接分析图片
            from agent.qwen_inference import QwenInference
            qwen_inference = QwenInference()
            
            # 如果没有文本问题，使用默认问题
            if not message_text:
                question = "请分析这张图片的内容"
            else:
                question = message_text
            
            # 调用多模态 API
            try:
                # 使用第一张图片进行分析
                image_path = image_paths[0]
                answer = qwen_inference.generate(
                    text=question,
                    image_url=f"file://{os.path.abspath(image_path)}"
                )
                
                ai_msg = session.add_message(
                    role='ai',
                    content=answer,
                    subject=subject,
                    reasoning_steps=['分析上传图片', '理解用户问题', '生成专业回答']
                )
                
                return jsonify({
                    'status': 'success',
                    'session_id': session.session_id,
                    'user_message': user_msg,
                    'ai_message': ai_msg
                }), 200
            except Exception as e:
                logger.error(f"多模态问答失败: {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'图片分析失败: {str(e)}'
                }), 500
        
        # RAG 处理（纯文本问答）
        if not rag_engine:
            return jsonify({
                'status': 'error',
                'message': 'RAG 引擎未初始化'
            }), 500

        # ==================== 自动学科识别 ====================
        # 调用 rag_engine.detect_subject 自动判断问题属于哪个学科
        # 这样用户无需手动选择学科 AI
        detected_info = rag_engine.detect_subject(message_text)
        effective_subject = detected_info.get("detected_subject", "全部学科")
        logger.info(
            f"自动学科识别: '{message_text[:30]}...' → {effective_subject} "
            f"(置信度 {detected_info.get('confidence', 0)})"
        )

        # 调用 RAG 进行问答（用自动识别到的学科）
        result = rag_engine.answer_question(
            question=message_text,
            subject=effective_subject,
            top_k=5
        )

        # 从 result 中提取新字段，并显式转为 Python 原生类型（避免 numpy 序列化问题）
        _conf = result.get('answer_confidence', {}) or {}
        _sources = result.get('knowledge_sources', []) or []
        # 确保置信度值是标准 float（防止 numpy.float32）
        if isinstance(_conf, dict) and 'score' in _conf:
            try:
                _conf['score'] = round(float(_conf['score']), 4)
            except Exception:
                pass

        # 添加 AI 回复（消息的 subject 也用识别到的学科）—— 把置信度和知识源一起写入消息
        ai_msg = session.add_message(
            role='ai',
            content=result['answer'],
            subject=effective_subject,
            reasoning_steps=result['reasoning_steps'],
            retrieved_documents=result['retrieved_documents'],
            # 新增字段：Qwen 评估的置信度 + RAG 检索的知识源
            answer_confidence=_conf,
            knowledge_sources=_sources,
        )

        # 将 scores 值显式转为 Python float（作为额外保险）
        safe_scores = None
        if detected_info and detected_info.get('scores'):
            safe_scores = {k: round(float(v), 4) for k, v in detected_info['scores'].items()}

        return jsonify({
            'status': 'success',
            'session_id': session.session_id,
            'user_message': user_msg,
            'ai_message': ai_msg,
            'detected_subject': effective_subject,
            'confidence': float(detected_info.get('confidence', 0)),
            'answer_confidence': _conf,
            'knowledge_sources': _sources,
            'subject_scores': safe_scores,
        }), 200

    except Exception as e:
        logger.error(f"发送消息失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'处理失败: {str(e)}'
        }), 500


@app.route('/api/chat/history', methods=['GET'])
def get_history():
    """
    获取对话历史
    
    查询参数:
    - session_id: 会话 ID
    - limit: 返回最近 N 条消息（可选）
    """
    try:
        session_id = request.args.get('session_id')
        limit = request.args.get('limit', type=int)
        
        if not session_id:
            return jsonify({
                'status': 'error',
                'message': 'session_id 为必填参数'
            }), 400
        
        session = get_or_create_session(session_id)
        history = session.get_history(limit)
        
        return jsonify({
            'status': 'success',
            'history': history,
            'total': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/chat/source/<message_id>', methods=['GET'])
def get_message_source(message_id: str):
    """
    获取消息的溯源信息（检索到的文档）
    
    查询参数:
    - session_id: 会话 ID
    """
    try:
        session_id = request.args.get('session_id')
        
        if not session_id or session_id not in sessions:
            return jsonify({
                'status': 'error',
                'message': '无效的会话 ID'
            }), 400
        
        session = sessions[session_id]
        
        # 查找消息
        message = None
        for msg in session.history:
            if msg['id'] == message_id:
                message = msg
                break
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': '消息不存在'
            }), 404
        
        # 返回检索到的文档
        retrieved_docs = message.get('retrieved_documents', [])
        
        return jsonify({
            'status': 'success',
            'message_id': message_id,
            'source_documents': retrieved_docs,
            'total_sources': len(retrieved_docs)
        }), 200
        
    except Exception as e:
        logger.error(f"获取溯源信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/chat/clear', methods=['POST'])
def clear_session():
    """
    清空会话历史
    
    请求体:
    {
        "session_id": "session-id"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in sessions:
            return jsonify({
                'status': 'error',
                'message': '无效的会话 ID'
            }), 400
        
        session = sessions[session_id]
        session.clear_history()
        
        return jsonify({
            'status': 'success',
            'message': '对话历史已清空'
        }), 200
        
    except Exception as e:
        logger.error(f"清空历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/upload/test', methods=['POST'])
def test_upload():
    """
    测试文件上传接口
    用于调试文件上传功能
    """
    try:
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({
                'status': 'error',
                'message': '请选择要上传的文件'
            }), 400
        
        results = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                # 保存文件
                file_path = app.config['UPLOAD_FOLDER'] / filename
                file.save(file_path)
                
                # 处理 PDF
                extracted_text = ''
                if file_ext == 'pdf':
                    docs = multimodal_processor.process_file(str(file_path))
                    if docs:
                        extracted_text = docs[0].get('text', '')[:200] + '...' if len(docs[0].get('text', '')) > 200 else docs[0].get('text', '')
                
                results.append({
                    'filename': filename,
                    'content_type': file.content_type,
                    'size': os.path.getsize(file_path),
                    'extracted_text': extracted_text
                })
        
        return jsonify({
            'status': 'success',
            'message': f'成功上传 {len(results)} 个文件',
            'files': results
        }), 200
        
    except Exception as e:
        logger.error(f"文件上传测试失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500


# ==================== 知识库管理 API ====================

@app.route('/api/knowledge/upload', methods=['POST'])
def upload_knowledge():
    """
    上传文档到指定学科的知识库。
    
    FormData 参数:
    - subject: 学科分类（必选）
    - files: 上传的文档文件列表（PDF/TXT/文本文件，可多选）
    """
    try:
        if not rag_engine:
            return jsonify({
                'status': 'error',
                'message': 'RAG 引擎未初始化'
            }), 500

        subject = request.form.get('subject', '全部学科').strip()
        files = request.files.getlist('files')

        if not files or all(not f or not f.filename for f in files):
            return jsonify({
                'status': 'error',
                'message': '请选择要上传的文件'
            }), 400

        uploaded = []
        for file in files:
            if not file or not file.filename:
                continue
            try:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                # 保存到临时目录
                file_path = app.config['UPLOAD_FOLDER'] / filename
                file.save(file_path)

                # 提取文本
                if ext == 'pdf':
                    docs = multimodal_processor.process_file(str(file_path))
                elif ext in ('txt', 'md'):
                    text = file_path.read_text(encoding='utf-8', errors='ignore')
                    docs = [{
                        'text': text,
                        'metadata': {
                            'source': filename,
                            'type': 'text',
                        },
                    }]
                else:
                    logger.warning(f"不支持的文件类型: {filename}")
                    continue

                # 按学科写入知识库
                if docs and rag_engine.add_knowledge(docs, subject=subject):
                    uploaded.append({
                        'filename': filename,
                        'pages': len(docs),
                        'subject': subject,
                    })
                    logger.info(f"知识库添加成功: {filename} -> {subject}，共 {len(docs)} 页")
                else:
                    logger.error(f"知识库添加失败: {filename}")
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")

        return jsonify({
            'status': 'success',
            'message': f'成功添加 {len(uploaded)} 个文件到 [{subject}] 知识库',
            'uploaded': uploaded,
            'total_knowledge_count': rag_engine.get_stats().get('retriever_stats', {}).get('total_documents', 0) if rag_engine else 0,
        }), 200
    except Exception as e:
        logger.error(f"知识库上传失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500


@app.route('/api/knowledge/documents', methods=['GET'])
def list_knowledge_documents():
    """
    列出知识库文档。
    
    查询参数:
    - subject: 学科过滤（可选；不传或传 "全部学科" 表示所有学科）
    - limit: 返回条数上限（可选，默认 100）
    """
    try:
        if not rag_engine:
            return jsonify({
                'status': 'error',
                'message': 'RAG 引擎未初始化'
            }), 500

        subject = request.args.get('subject', '').strip() or None
        limit = int(request.args.get('limit', 100))

        docs = rag_engine.list_knowledge(subject=subject, limit=limit)
        return jsonify({
            'status': 'success',
            'documents': docs,
            'total': len(docs),
            'filter_subject': subject or '全部学科',
        }), 200
    except Exception as e:
        logger.error(f"列出知识库失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/knowledge/clear', methods=['POST'])
def clear_knowledge():
    """
    清空指定学科的知识库索引。
    
    请求体:
    { "subject": "数据结构" }  -> 清空该学科
    { "subject": "全部学科" }  -> 清空所有学科
    """
    try:
        if not rag_engine:
            return jsonify({
                'status': 'error',
                'message': 'RAG 引擎未初始化'
            }), 500

        data = request.get_json() or {}
        subject = data.get('subject', '全部学科').strip()

        if rag_engine.clear_knowledge(subject):
            return jsonify({
                'status': 'success',
                'message': f'已清空 [{subject}] 的知识库'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'清空 [{subject}] 知识库失败'
            }), 500
    except Exception as e:
        logger.error(f"清空知识库失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """获取所有可用的学科分类及实时文档数"""
    # 从 RAG 引擎读取各学科的索引统计
    subject_counts: Dict[str, int] = {}
    if rag_engine:
        try:
            stats = rag_engine.get_stats()
            subjects_info = stats.get('retriever_stats', {}).get('subjects', {})
            for subject, info in subjects_info.items():
                subject_counts[subject] = int(info.get('documents', 0))
        except Exception as e:
            logger.warning(f"读取学科统计失败: {e}")

    # 构造带 count 的学科列表
    subjects_with_count = []
    for subject in SUBJECTS:
        # "全部学科" 汇总所有学科的总数
        if subject == "全部学科":
            total = sum(subject_counts.get(s, 0) for s in SUBJECTS if s != "全部学科")
            subjects_with_count.append({"name": subject, "count": total})
        else:
            subjects_with_count.append({"name": subject, "count": subject_counts.get(subject, 0)})

    return jsonify({
        'status': 'success',
        'subjects': subjects_with_count
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取系统统计信息"""
    try:
        stats = {
            'active_sessions': len(sessions),
            'rag_engine': rag_engine.get_stats() if rag_engine else None
        }
        
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({
        'status': 'error',
        'message': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    logger.error(f"内部错误: {error}")
    return jsonify({
        'status': 'error',
        'message': '内部服务器错误'
    }), 500


if __name__ == '__main__':
    logger.info("启动 EduBrain AI 后端服务...")
    logger.info(f"监听地址: {API_CONFIG['host']}:{API_CONFIG['port']}")
    
    app.run(
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        debug=API_CONFIG['debug']
    )