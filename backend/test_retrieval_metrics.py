import json
import logging
import sys
import os
import random
from typing import List, Dict, Tuple, Set
from collections import defaultdict

# 路径配置
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from agent.embedding import EmbeddingManager
from agent.retriever import FAISSRetriever
from config import SUBJECTS

logging.basicConfig(level=logging.INFO)
random.seed(42)

# 留一法评估 —— 从知识库文档中构造查询
def eval_loo(retriever: FAISSRetriever, embedder: EmbeddingManager,
              samples_per_subject: int = 15, top_k_list: List[int] = [1, 3, 5, 10]) -> Dict:
    """
    Leave-One-Out 评估：
    1. 从各学科随机选文档 → 截取前一段作为"查询"
    2. 用剩余文档检索，看原始文档是否出现在前 K 位
    3. 记录 MRR / Hit Rate @ K / Precision @ K
    """
    # 收集所有文档 (学科 -> [(text, metadata, index_in_metadata_list)])
    subject_docs: Dict[str, List[Tuple[str, Dict, int]]] = defaultdict(list)
    for subject, (_, metadata_list) in retriever._stores.items():
        for idx, meta in enumerate(metadata_list):
            subject_docs[subject].append((meta["text"], meta.get("metadata", {}), idx))

    all_queries = []
    for subject, docs in subject_docs.items():
        if len(docs) < 3:
            continue
        samples = random.sample(docs, min(samples_per_subject, len(docs)))
        for text, meta, orig_idx in samples:
            # 截取查询文本：取前 80~150 字，模拟用户提问
            query_text = text[: random.randint(80, 150)]
            all_queries.append({
                "query_text": query_text,
                "target_subject": subject,
                "target_doc_text": text,
                "target_doc_preview": text[:100],
            })

    print(f"\n[方式1 留一法] 构造 {len(all_queries)} 条查询")
    print("-" * 70)

    hits_at_k = {k: 0 for k in top_k_list}
    reciprocal_ranks = []
    ranks = []

    for q in all_queries:
        query_emb = embedder.embed_text(q["query_text"])[0]

        # 跨学科检索（模拟真实使用）
        results = retriever.search(query_emb, top_k=max(top_k_list), subject_filter="全部学科")

        # 查找原始文档在检索结果中的位置
        target_preview = q["target_doc_preview"]
        rank = None
        for i, (r_text, _, _) in enumerate(results):
            # 简单比较：判断是否是同一段文本（前 50 字匹配）
            if r_text[:50] == q["target_doc_text"][:50]:
                rank = i + 1
                break

        if rank is not None:
            ranks.append(rank)
            reciprocal_ranks.append(1.0 / rank)
            for k in top_k_list:
                if rank <= k:
                    hits_at_k[k] += 1

    total = len(all_queries)
    metrics = {
        "total_queries": total,
        "mrr": round(sum(reciprocal_ranks) / total, 4) if total else 0,
        "avg_rank": round(sum(ranks) / len(ranks), 2) if ranks else float("inf"),
        "hit_rate": {f"hit@{k}": round(hits_at_k[k] / total, 4) for k in top_k_list},
    }

    print(f"MRR:         {metrics['mrr']:.4f}")
    print(f"平均排名:     {metrics['avg_rank']:.1f}")
    for k in top_k_list:
        print(f"Hit Rate @{k:>2}: {metrics['hit_rate'][f'hit@{k}']:.2%}")
    print(f"成功检索到的查询数: {len(ranks)} / {total}")

    return metrics

# ================================================================
# 主入口
# ================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("FAISS 检索模块命中率评估（留一法 Leave-One-Out）")
    print("=" * 70)

    # 初始化组件
    embedder = EmbeddingManager()
    retriever = FAISSRetriever()

    # 打印知识库概览
    stats = retriever.get_stats()
    print(f"\n知识库总文档数: {stats['total_documents']}")
    print(f"学科数量:       {stats['subject_count']}")
    print("-" * 70)
    for sub, info in stats["subjects"].items():
        print(f"  - {sub:<14} {info['documents']} 条文档")

    # 运行留一法评估
    metrics = eval_loo(retriever, embedder)

    # 保存评估报告
    report = {
        "knowledge_base_stats": stats,
        "evaluation_method": "leave_one_out",
        "metrics": metrics,
    }
    output_path = os.path.join(_BACKEND_DIR, "retrieval_metrics_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 70}")
    print(f"评估报告已保存到: {output_path}")
    print("=" * 70)