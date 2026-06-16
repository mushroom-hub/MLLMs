"""
构建知识库索引脚本
从本地文档构建 FAISS 向量索引
"""
import json
import logging
from pathlib import Path
from typing import List, Dict
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SUBJECTS
from agent.embedding import EmbeddingManager
from agent.retriever import FAISSRetriever
from agent.multimodal import MultimodalProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_documents(json_file: str) -> List[Dict]:
    """从 JSON 文件加载文档"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        
        # 处理 dataset.json 格式
        if isinstance(data, list):
            for item in data:
                doc = {
                    'text': item.get('content', item.get('description', '')),
                    'metadata': {
                        'source': 'dataset.json',
                        'id': item.get('id'),
                        'title': item.get('title', '')
                    }
                }
                if 'subject' in item:
                    doc['subject'] = item['subject']
                documents.append(doc)
        
        # 处理其他 JSON 格式
        elif isinstance(data, dict):
            if 'documents' in data:
                for doc in data['documents']:
                    documents.append({
                        'text': doc.get('text', ''),
                        'metadata': doc.get('metadata', {}),
                        'subject': doc.get('subject', '全部学科')
                    })
            elif 'content' in data:
                documents.append({
                    'text': data['content'],
                    'metadata': {'source': json_file},
                    'subject': data.get('subject', '全部学科')
                })
        
        logger.info(f"从 {json_file} 加载了 {len(documents)} 个文档")
        return documents
    except Exception as e:
        logger.error(f"加载 JSON 文档失败: {e}")
        return []


def build_index_from_dataset():
    """从 dataset 文件夹构建索引"""
    logger.info("开始构建知识库索引...")
    
    # 初始化模块
    embedding_manager = EmbeddingManager()
    retriever = FAISSRetriever()
    multimodal_processor = MultimodalProcessor()
    
    dataset_dir = Path(__file__).parent.parent / "dataset"
    all_documents = []
    
    # 扫描数据集文件
    for subject in SUBJECTS:
        if subject == "全部学科":
            continue
        
        subject_dir = dataset_dir / "dataset_output"
        json_files = list(subject_dir.glob("*.json"))
        
        for json_file in json_files:
            logger.info(f"处理文件: {json_file.name}")
            docs = load_json_documents(str(json_file))
            
            for doc in docs:
                if 'subject' not in doc:
                    doc['subject'] = subject
                all_documents.append(doc)
    
    if not all_documents:
        logger.warning("未找到任何文档，请检查数据集路径")
        return False
    
    logger.info(f"总共加载了 {len(all_documents)} 个文档")
    
    # 嵌入文档
    logger.info("开始文本嵌入...")
    texts = [doc['text'] for doc in all_documents]
    embeddings = embedding_manager.embed_text(texts)
    
    # 添加到索引
    logger.info("添加文档到 FAISS 索引...")
    retriever.add_documents(embeddings, all_documents)
    
    logger.info("知识库索引构建完成！")
    
    # 打印统计信息
    stats = retriever.get_stats()
    logger.info(f"索引统计: {stats}")
    
    return True


def build_index_from_custom_docs(docs_list: List[Dict]):
    """从自定义文档列表构建索引"""
    logger.info("开始构建自定义知识库索引...")
    
    # 初始化模块
    embedding_manager = EmbeddingManager()
    retriever = FAISSRetriever()
    
    if not docs_list:
        logger.warning("文档列表为空")
        return False
    
    logger.info(f"加载了 {len(docs_list)} 个文档")
    
    # 嵌入文档
    logger.info("开始文本嵌入...")
    texts = [doc['text'] for doc in docs_list]
    embeddings = embedding_manager.embed_text(texts)
    
    # 添加到索引
    logger.info("添加文档到 FAISS 索引...")
    retriever.add_documents(embeddings, docs_list)
    
    logger.info("自定义知识库索引构建完成！")
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='构建知识库索引')
    parser.add_argument(
        '--source',
        type=str,
        choices=['dataset', 'custom'],
        default='dataset',
        help='数据来源'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='自定义 JSON 文件路径'
    )
    
    args = parser.parse_args()
    
    if args.source == 'dataset':
        success = build_index_from_dataset()
    elif args.source == 'custom' and args.file:
        docs = load_json_documents(args.file)
        success = build_index_from_custom_docs(docs)
    else:
        logger.error("参数错误")
        success = False
    
    exit(0 if success else 1)
