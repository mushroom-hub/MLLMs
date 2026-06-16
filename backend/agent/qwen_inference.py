"""
Qwen 模型推理模块（API 版本）
严格按照 DashScope MultiModalConversation 官方示例重构
"""
import os
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv

# 读取环境变量
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_file)

# 导入官方SDK
import dashscope
# 全局设置基础API根地址与密钥
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

from config import QWEN_API_CONFIG

# 初始化日志
logger = logging.getLogger(__name__)


class QwenInference:
    """Qwen API 推理类（基于官方 MultiModalConversation SDK 重构）"""
    
    def __init__(self):
        """初始化 Qwen API 客户端"""
        self.api_type = QWEN_API_CONFIG["api_type"]
        self.model_id = QWEN_API_CONFIG["model"]  # 确保配置中是 'qwen3.7-plus' 或支持多模态的模型
        self.timeout = QWEN_API_CONFIG["timeout"]
        self.temperature = QWEN_API_CONFIG["temperature"]
        self.max_tokens = QWEN_API_CONFIG["max_tokens"]
        
        if self.api_type != "dashscope":
            raise ValueError(f"不支持的 API 类型: {self.api_type}")
        
        logger.info(f"初始化 Qwen API 客户端: {self.api_type}, 模型: {self.model_id}")
    
    def generate(
        self,
        text: str,
        image_url: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        单轮生成（支持纯文本或图文输入）
        """
        try:
            max_tokens = max_new_tokens or self.max_tokens
            temp = temperature or self.temperature
            
            # 严格按照官方构建 content 列表
            content_list = []
            if image_url:
                content_list.append({"image": image_url})
            content_list.append({"text": text})
            
            messages = [{"role": "user", "content": content_list}]
            return self._call_sdk(messages, max_tokens, temp)
        except Exception as e:
            logger.error(f"单轮生成回复失败: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        多轮对话生成（兼容纯文本历史和多模态标准格式）
        """
        try:
            max_tokens = max_new_tokens or self.max_tokens
            temp = temperature or self.temperature
            
            formatted_messages = []
            
            # 1. 注入系统提示词（MultiModalConversation 的系统词也推荐使用规范格式）
            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": [{"text": system_prompt}]
                })
            
            # 2. 转换传入的历史消息为官方标准的多模态列表格式
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                # 如果已经是列表形式则保持，如果是纯文本字符串则转换为标准列表
                if isinstance(content, str):
                    formatted_content = [{"text": content}]
                elif isinstance(content, list):
                    formatted_content = content
                else:
                    formatted_content = [{"text": str(content)}]
                    
                formatted_messages.append({
                    "role": role,
                    "content": formatted_content
                })
            
            return self._call_sdk(formatted_messages, max_tokens, temp)
        except Exception as e:
            logger.error(f"多轮对话生成失败: {e}")
            raise

    def _call_sdk(
        self,
        messages: List[Dict],
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        底层封装官方SDK MultiModalConversation.call
        """
        logger.info(f"调用多模态 API: {self.model_id}")
        
        # 1. 动态获取最新的 key，防止全局赋值失败
        current_api_key = os.getenv("DASHSCOPE_API_KEY") or dashscope.api_key
        if not current_api_key:
            raise ValueError("未检测到 DASHSCOPE_API_KEY，请检查 backend/.env 文件配置。")

        # 2. 显式在 call 方法里传入 api_key
        response = dashscope.MultiModalConversation.call(
            api_key=current_api_key,  # 确保这里绝对有值
            model=self.model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 检查响应状态
        if response.status_code != 200:
            error_msg = f"API 调用异常 code:{response.code}, message:{response.message}, request_id:{response.request_id}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            reply = response.output.choices[0].message.content[0]["text"]
            logger.info("API 调用成功")
            return reply
        except (AttributeError, IndexError, KeyError) as e:
            error_msg = f"解析返回数据结构失败: {e}, 原始响应: {response}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
    def extract_reasoning_steps(self, response: str) -> List[str]:
        """从模型响应中提取推理步骤"""
        try:
            import re
            steps = []
            pattern = r'^\d+\.\s+(.+?)(?=^\d+\.|$)'
            matches = re.findall(pattern, response, re.MULTILINE)
            
            if matches:
                steps = [match.strip() for match in matches]
            else:
                sentences = response.split("。")
                steps = [s.strip() for s in sentences if s.strip()]
            
            return steps[:5]
        except Exception as e:
            logger.warning(f"提取推理步骤失败: {e}")
            return [response]
    
    def get_stats(self) -> Dict:
        """获取推理引擎统计信息"""
        return {
            "engine": "Qwen DashScope Official MultiModal SDK",
            "api_type": self.api_type,
            "model": self.model_id,
            "status": "ready"
        }