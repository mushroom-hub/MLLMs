"""
FAISS 向量检索模块（按学科分类版本）
每个学科维护一个独立的 FAISS 索引
支持：按学科添加、按学科检索、跨学科检索、按学科统计、清空某学科
"""
import logging
import json
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path
import faiss
from config import (
    FAISS_INDEX_DIR,
    FAISS_INDEX_TEMPLATE,
    FAISS_METADATA_TEMPLATE,
    FAISS_CONFIG,
    RAG_CONFIG,
    SUBJECTS,
    subject_to_filename,
)

logger = logging.getLogger(__name__)


class FAISSRetriever:
    """FAISS 向量检索器（按学科分类管理）"""

    def __init__(
        self,
        dimension: int = FAISS_CONFIG["dimension"],
    ):
        """初始化 FAISS 检索器。启动时为每个已在 SUBJECTS 列表中的学科加载/创建索引。"""
        self.dimension = dimension
        # key: 学科名 -> (faiss.Index, List[Dict])
        self._stores: Dict[str, Tuple[faiss.Index, List[Dict]]] = {}
        self._init_all_subjects()

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def _subject_key(self, subject: str) -> str:
        """学科名标准化为索引 key。"""
        if not subject or subject == "全部学科":
            return "全部学科"
        return subject.strip()

    def _index_path(self, subject: str) -> Path:
        """获取某学科的索引文件路径（使用 ASCII 文件名避免 Windows 编码问题）。"""
        fname = subject_to_filename(subject)
        return Path(FAISS_INDEX_TEMPLATE.format(subject_fname=fname))

    def _metadata_path(self, subject: str) -> Path:
        """获取某学科的元数据文件路径（使用 ASCII 文件名避免 Windows 编码问题）。"""
        fname = subject_to_filename(subject)
        return Path(FAISS_METADATA_TEMPLATE.format(subject_fname=fname))

    def _init_all_subjects(self):
        """初始化所有在 SUBJECTS 列表中的学科索引。"""
        FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        loaded = 0
        for subject in SUBJECTS:
            key = self._subject_key(subject)
            if key == "全部学科":
                continue  # "全部学科" 不存储独立索引，检索时跨所有学科
            self._stores[key] = self._load_or_create_index(key)
            loaded += 1
        logger.info(f"已加载 {loaded} 个学科索引")
    
    def _load_or_create_index(self, subject: str) -> Tuple[faiss.Index, List[Dict]]:
        """加载或创建某学科的索引与元数据。"""
        idx_path = self._index_path(subject)
        meta_path = self._metadata_path(subject)
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if idx_path.exists() and meta_path.exists():
                logger.info(f"加载 [{subject}] 索引: {idx_path}")
                # --- 修复：用 Python open() + serialize_index 绕过 faiss fopen() 中文路径问题 ---
                # faiss 1.7.4 在 Windows 上 fopen() 无法处理含中文的路径；且 deserialize_index 只
                # 接受 np.ndarray(uint8)，不接受原始 bytes。因此：Python 读 bytes → 转成 uint8 numpy 数组 → 反序列化。
                with open(idx_path, 'rb') as f:
                    buf = f.read()
                index = faiss.deserialize_index(np.frombuffer(buf, dtype=np.uint8))
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                logger.info(f"[{subject}] 已加载 {len(metadata)} 条记录")
                return index, metadata
            else:
                logger.info(f"创建新的 [{subject}] 索引（维度: {self.dimension}")
                return faiss.IndexFlatL2(self.dimension), []
        except Exception as e:
            logger.error(f"[{subject}] 索引加载失败: {e}，重建空索引")
            return faiss.IndexFlatL2(self.dimension), []
    
    def add_documents(
        self,
        embeddings: np.ndarray,
        documents: List[Dict],
        subject: str = "全部学科",
    ) -> None:
        """
        添加文档到指定学科的索引。
        
        Args:
            embeddings: 嵌入向量矩阵 (N, dimension)
            documents: 文档列表，每个文档包含 'text' 和 'metadata'
            subject: 学科分类；为空或 "全部学科" 时归入通用索引
        """
        try:
            key = self._subject_key(subject)
            if key not in self._stores:
                self._stores[key] = self._load_or_create_index(key)
            index, metadata = self._stores[key]

            embeddings = embeddings.astype(np.float32)
            index.add(embeddings)

            for doc in documents:
                metadata.append({
                    'text': doc.get('text', ''),
                    'metadata': doc.get('metadata', {}),
                    'subject': key,
                })

            self._save_index(key)
            logger.info(
                f"[{key}] 添加 {len(documents)} 个文档，当前 {index.ntotal} 条记录"
            )
        except Exception as e:
            logger.error(f"[{subject}] 添加文档失败: {e}")
            raise
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = RAG_CONFIG["top_k"],
        subject_filter: str = None,
    ) -> List[Tuple[str, float, Dict]]:
        """
        检索相似文档。
        
        - subject_filter == "全部学科" 或未指定：跨所有学科索引检索
        - 指定具体学科：仅在该学科索引中检索
        """
        try:
            query_embedding = query_embedding.astype(np.float32).reshape(1, -1)

            key = self._subject_key(subject_filter or "全部学科")
            if key == "全部学科":
                target_keys = list(self._stores.keys())
            else:
                if key not in self._stores:
                    self._stores[key] = self._load_or_create_index(key)
                target_keys = [key]

            # 在每个目标索引中检索 top_k*2 条，再全局合并排序
            all_results = []
            for subject_key in target_keys:
                index, metadata = self._stores[subject_key]
                if index.ntotal == 0:
                    continue
                distances, indices = index.search(query_embedding, top_k * 2)
                for idx, distance in zip(indices[0], distances[0]):
                    if idx == -1 or idx >= len(metadata):
                        continue
                    doc_meta = metadata[idx]
                    similarity = 1 / (1 + float(distance))
                    if similarity < RAG_CONFIG.get("similarity_threshold", 0):
                        continue
                    all_results.append((
                        doc_meta['text'],
                        similarity,
                        doc_meta.get('metadata', {}),
                        subject_key,
                    ))

            # 按相似度降序
            all_results.sort(key=lambda x: x[1], reverse=True)
            final = [(text, sim, meta) for text, sim, meta, _ in all_results[:top_k]]
            logger.info(
                f"检索[{subject_filter or '全部学科'}]: 命中 {len(final)} 条相关文档"
            )
            return final
        except Exception as e:
            logger.error(f"检索失败[{subject_filter}]: {e}")
            return []

    def _save_index(self, subject: str) -> None:
        """保存指定学科的索引与元数据到磁盘。"""
        try:
            if subject not in self._stores:
                return
            index, metadata = self._stores[subject]
            idx_path = self._index_path(subject)
            meta_path = self._metadata_path(subject)
            idx_path.parent.mkdir(parents=True, exist_ok=True)
            # --- 修复：用 serialize_index + Python open() 绕过 faiss fopen() 中文路径问题 ---
            # faiss 1.7.4 的 C++ fopen() 在 Windows 上按 ANSI 解析路径，含中文会失败；
            # 先在内存中序列化得到 bytes，再用 Python open() 写入（Python 用 Unicode API）。
            buf = faiss.serialize_index(index)
            with open(idx_path, 'wb') as f:
                f.write(buf)
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"[{subject}] 索引已保存（{len(metadata)} 条记录）")
        except Exception as e:
            logger.error(f"[{subject}] 保存索引失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取所有学科索引的统计信息。"""
        subject_stats = {}
        total = 0
        for subject, (index, meta) in self._stores.items():
            cnt = index.ntotal if index else 0
            subject_stats[subject] = {
                'documents': cnt,
                'metadata_records': len(meta),
                'index_file': str(self._index_path(subject)),
            }
            total += cnt
        return {
            'dimension': self.dimension,
            'total_documents': total,
            'subject_count': len(self._stores),
            'subjects': subject_stats,
        }

    def list_documents(
        self,
        subject: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        列出知识库中的文档摘要（用于前端展示）。
        
        Args:
            subject: 指定学科；None 或 "全部学科" 表示跨所有学科
            limit: 返回条数上限
        """
        results = []
        key = self._subject_key(subject or "全部学科") if subject else "全部学科"
        if key == "全部学科":
            target_keys = list(self._stores.keys())
        else:
            if key not in self._stores:
                return []
            target_keys = [key]

        for sub in target_keys:
            _, metadata = self._stores[sub]
            for m in metadata:
                results.append({
                    'subject': sub,
                    'source': m.get('metadata', {}).get('source', ''),
                    'page': m.get('metadata', {}).get('page'),
                    'preview': m.get('text', '')[:200],
                    'doc_type': m.get('metadata', {}).get('type', ''),
                })
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
        return results[:limit]

    def clear_subject(self, subject: str) -> bool:
        """
        清空指定学科的知识库索引。
        
        Returns:
            是否成功
        """
        try:
            key = self._subject_key(subject)
            if key == "全部学科":
                # 清空所有学科
                for sub in list(self._stores.keys()):
                    self.clear_subject(sub)
                return True
            if key not in self._stores:
                logger.warning(f"未找到学科索引: {key}")
                return False
            # 重建空索引
            self._stores[key] = (faiss.IndexFlatL2(self.dimension), [])
            # 删除磁盘上的旧文件
            idx_path = self._index_path(key)
            meta_path = self._metadata_path(key)
            if idx_path.exists():
                idx_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            logger.info(f"已清空 [{key}] 的知识库索引")
            return True
        except Exception as e:
            logger.error(f"清空 {subject} 索引失败: {e}")
            return False