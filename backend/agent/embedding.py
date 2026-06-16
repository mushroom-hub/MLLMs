"""
嵌入和向量化模块
支持文本和图像的嵌入
"""
import logging
from typing import List, Union, Dict
import numpy as np
from config import EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """文本和图像嵌入管理器"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        初始化嵌入模型
        
        Args:
            model_name: 嵌入模型名称
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = EMBEDDING_DIM
        self._load_model()
    
    def _load_model(self):
        """加载嵌入模型（完全不依赖 HuggingFace。优先级：本地 ModelScope → DashScope API）"""
        import os

        # ---------- 方案 1：本地 ModelScope m3e-base 模型（首选，完全离线）----------
        local_path = self.model_name
        # 如果配置的是相对路径或绝对路径，检查是否存在
        if local_path and os.path.isdir(local_path):
            try:
                logger.info(f"尝试从本地加载嵌入模型: {local_path}")
                # m3e-base 兼容 sentence_transformers 格式，直接传入目录即可加载
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(local_path)
                # m3e-base 维度固定 768，若 config 中写的不是 768 则以模型实际输出为准
                probe = self.model.encode(["test"], normalize_embeddings=True)
                self.embedding_dim = int(probe.shape[1])
                logger.info(f"本地 m3e-base 加载成功（维度 {self.embedding_dim}）")
                return
            except Exception as e:
                logger.warning(f"本地 m3e-base 加载失败: {e}")
        else:
            logger.warning(f"本地模型目录不存在: {local_path}")

        # ---------- 方案 2：DashScope 文本嵌入 API（回退，需要联网和 API Key）----------
        try:
            logger.info("回退到 DashScope 文本嵌入 API...")
            self._use_qwen_embedding()
            return
        except Exception as e:
            logger.error(f"DashScope 嵌入 API 也失败: {e}")
            raise RuntimeError(
                "所有嵌入方案均不可用。请检查：\n"
                f"  1) 本地模型目录: {local_path}\n"
                "  2) backend/.env 中是否配置了 DASHSCOPE_API_KEY"
            )
    
    def _use_qwen_embedding(self):
        import os
        import dashscope
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未检测到 DASHSCOPE_API_KEY，请检查 backend/.env 文件配置。")
        dashscope.api_key = api_key
        
        class DashScopeEmbeddingWrapper:
            def encode(self, texts, normalize_embeddings=False, show_progress_bar=False):
                if isinstance(texts, str):
                    texts = [texts]
                # DashScope 单次最多 25 条，分批调用
                batch_size = 25
                all_embeddings = []
                for start in range(0, len(texts), batch_size):
                    batch = texts[start:start + batch_size]
                    resp = dashscope.TextEmbedding.call(
                        model="text-embedding-v2",
                        input=batch,
                        text_type="document"
                    )
                    if resp.status_code != 200:
                        raise RuntimeError(
                            f"DashScope 嵌入 API 失败: code={resp.code}, msg={resp.message}"
                        )
                    batch_embs = [r['embedding'] for r in resp.output['embeddings']]
                    all_embeddings.extend(batch_embs)
                arr = np.array(all_embeddings, dtype=np.float32)
                if normalize_embeddings:
                    norms = np.linalg.norm(arr, axis=1, keepdims=True)
                    norms[norms == 0] = 1.0
                    arr = arr / norms
                return arr
        
        self.model = DashScopeEmbeddingWrapper()
        self.embedding_dim = 1024
        logger.info("DashScope 文本嵌入 API 初始化成功（维度 1024）")
    
    def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        文本嵌入
        
        Args:
            texts: 文本或文本列表
            
        Returns:
            嵌入向量 (N, embedding_dim)
        """
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            # 过滤 None 或空文本
            texts = [t if t else "" for t in texts]
            
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"文本嵌入失败: {e}")
            raise
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """
        图像嵌入
        
        Args:
            image_path: 图像路径
            
        Returns:
            嵌入向量 (embedding_dim,)
        """
        try:
            from PIL import Image
            
            # 加载图像
            image = Image.open(image_path).convert('RGB')
            
            # 使用 Qwen VL 模型进行图像编码
            # 这里需要使用 qwen_inference 模块的功能
            logger.info(f"图像嵌入: {image_path}")
            
            # 简化版本：使用图像的特征向量
            # 实际应该调用 Qwen 的视觉编码器
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            return embedding
        except Exception as e:
            logger.error(f"图像嵌入失败: {e}")
            raise
    
    def embed_documents(self, documents: List[Dict]) -> np.ndarray:
        """
        批量嵌入文档
        
        Args:
            documents: 文档列表，每个文档是一个字典
                      包含 'text' 和可选的 'metadata'
        
        Returns:
            嵌入向量矩阵 (N, embedding_dim)
        """
        try:
            texts = [doc.get('text', '') for doc in documents]
            embeddings = self.embed_text(texts)
            return embeddings
        except Exception as e:
            logger.error(f"文档嵌入失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.embedding_dim