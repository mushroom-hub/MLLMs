"""
初始化脚本
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_backend():
    """初始化后端"""
    logger.info("初始化 EduBrain AI 后端...")
    
    try:
        # 测试模型加载
        logger.info("测试 Qwen 模型加载...")
        from agent.qwen_inference import QwenInference
        qwen = QwenInference()
        logger.info("✓ Qwen 模型加载成功")
        
        # 测试嵌入模型
        logger.info("测试嵌入模型加载...")
        from agent.embedding import EmbeddingManager
        embedding = EmbeddingManager()
        logger.info("✓ 嵌入模型加载成功")
        
        # 测试 FAISS 索引
        logger.info("初始化 FAISS 索引...")
        from agent.retriever import FAISSRetriever
        retriever = FAISSRetriever()
        logger.info("✓ FAISS 索引初始化成功")
        
        # 测试 RAG 引擎
        logger.info("初始化 RAG 引擎...")
        from agent.rag import RAGEngine
        rag = RAGEngine()
        logger.info("✓ RAG 引擎初始化成功")
        
        logger.info("\n所有模块初始化完成！")
        logger.info("后端已准备好运行。")
        
        return True
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = init_backend()
    sys.exit(0 if success else 1)
