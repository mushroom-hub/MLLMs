"""
对话管理模块
维护会话历史和上下文
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DialogManager:
    """对话管理器"""
    
    def __init__(self, session_id: str = None):
        """
        初始化对话管理器
        
        Args:
            session_id: 会话 ID
        """
        self.session_id = session_id or self._generate_session_id()
        self.history: List[Dict] = []
        self.current_subject = "全部学科"
    
    def _generate_session_id(self) -> str:
        """生成唯一的会话 ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def add_message(
        self,
        role: str,
        content: str,
        subject: str = "全部学科",
        attachments: List[Dict] = None,
        reasoning_steps: List[str] = None,
        retrieved_documents: List[Dict] = None,
        answer_confidence: Dict = None,
        knowledge_sources: List[Dict] = None
    ) -> Dict:
        """
        添加消息到对话历史

        Args:
            role: 消息角色（'user' 或 'ai'）
            content: 消息内容
            subject: 学科分类
            attachments: 附件列表（可选）
            reasoning_steps: 推理步骤（可选，AI 消息）
            retrieved_documents: 检索到的文档（可选，AI 消息）
            answer_confidence: Qwen 评估的置信度 {score, level, summary}（可选，AI 消息）
            knowledge_sources: 规范化的知识源列表 {id, title, source, page, relevance, excerpt, ...}（可选）

        Returns:
            消息对象
        """
        message = {
            'id': self._generate_message_id(),
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'attachments': attachments or []
        }

        if role == 'ai':
            message['reasoning_steps'] = reasoning_steps or []
            message['retrieved_documents'] = retrieved_documents or []
            message['answer_confidence'] = answer_confidence or {}
            message['knowledge_sources'] = knowledge_sources or []
        
        self.history.append(message)
        self.current_subject = subject
        
        logger.info(f"添加消息: {role} - {subject}")
        return message
    
    def _generate_message_id(self) -> str:
        """生成唯一的消息 ID"""
        import time
        return str(int(time.time() * 1000))
    
    def get_history(self, limit: int = None) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            limit: 返回最近 N 条消息（None 表示全部）
            
        Returns:
            消息列表
        """
        if limit is None:
            return self.history
        return self.history[-limit:]
    
    def get_context_for_rag(self, window_size: int = 3) -> str:
        """
        生成 RAG 的上下文窗口
        
        Args:
            window_size: 上下文窗口大小（最近 N 条消息）
            
        Returns:
            上下文字符串
        """
        recent_messages = self.history[-window_size:]
        
        context_lines = []
        for msg in recent_messages:
            prefix = "用户:" if msg['role'] == 'user' else "助手:"
            context_lines.append(f"{prefix} {msg['content'][:100]}...")
        
        return "\n".join(context_lines)
    
    def clear_history(self):
        """清空对话历史"""
        self.history = []
        logger.info(f"清空会话历史: {self.session_id}")
    
    def get_session_info(self) -> Dict:
        """获取会话信息"""
        return {
            'session_id': self.session_id,
            'message_count': len(self.history),
            'current_subject': self.current_subject,
            'created_at': self.history[0]['timestamp'] if self.history else None,
            'last_message_at': self.history[-1]['timestamp'] if self.history else None
        }
    
    def save_to_file(self, file_path: str):
        """
        将对话历史保存到文件
        
        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': self.session_id,
                    'history': self.history,
                    'subject': self.current_subject
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"对话历史已保存到 {file_path}")
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")
    
    def load_from_file(self, file_path: str):
        """
        从文件加载对话历史
        
        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.session_id = data.get('session_id', self.session_id)
                self.history = data.get('history', [])
                self.current_subject = data.get('subject', '全部学科')
            logger.info(f"对话历史已加载，共 {len(self.history)} 条消息")
        except Exception as e:
            logger.error(f"加载对话历史失败: {e}")