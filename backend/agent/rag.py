# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) 核心模块
协调检索和生成流程
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from config import SYSTEM_PROMPT, ANSWER_PROMPT, RAG_CONFIG
from agent.qwen_inference import QwenInference
from agent.embedding import EmbeddingManager
from agent.retriever import FAISSRetriever

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG 引擎，融合检索和生成"""

    # ==================== 学科关键词规则 ====================
    # 出现这些关键词 → 给对应学科打高分（强信号）
    SUBJECT_KEYWORDS = {
        "数据结构": [
            "链表", "树", "图", "栈", "队列", "堆", "散列", "哈希",
            "B+", "B树", "二叉", "平衡", "排序", "查找", "红黑", "AVL",
            "字典树", "Trie", "回溯", "动态规划", "DP", "贪心",
            "冒泡", "快速排序", "归并", "堆排序", "并查集",
        ],
        "计算机组成原理": [
            "冯诺依曼", "CPU", "寄存器", "Cache", "缓存", "流水线",
            "指令集", "ALU", "存储器", "总线", "中断", "寻址", "MIPS",
            "单周期", "多周期", "组成原理", "汇编", "机器字", "主频",
            "DRAM", "SRAM", "SSD", "指令", "控制器", "运算器",
        ],
        "计算机网络": [
            "TCP", "UDP", "HTTP", "IP", "DNS", "路由", "交换机",
            "子网", "掩码", "ARP", "DHCP", "SSL", "TLS", "拥塞",
            "三次握手", "四次挥手", "OSI", "七层", "五层", "网络",
            "传输层", "网络层", "数据链路", "HTTP/2", "HTTP/3", "QUIC",
            "NAT", "端口", "Socket", "MAC", "以太网", "协议",
        ],
        "操作系统": [
            "进程", "线程", "调度", "死锁", "同步", "互斥", "信号量",
            "临界区", "虚拟内存", "分页", "分段", "页面置换", "LRU",
            "文件系统", "系统调用", "内核", "上下文切换",
            "操作系统", "并发", "锁", "调度算法", "FCFS", "SJF", "RR",
            "进程调度", "内存管理", "分时",
        ],
    }

    def __init__(self):
        """初始化 RAG 引擎"""
        logger.info("初始化 RAG 引擎...")

        try:
            self.embedding_manager = EmbeddingManager()
            self.qwen_model = QwenInference()
            self.retriever = FAISSRetriever()
            logger.info("RAG 引擎初始化成功")
        except Exception as e:
            logger.error(f"RAG 引擎初始化失败: {e}")
            raise

    def retrieve_context(
        self,
        query: str,
        top_k: int = RAG_CONFIG["top_k"],
        subject: str = "全部学科"
    ) -> Tuple[List[str], List[Dict]]:
        """
        检索相关知识库内容

        Args:
            query: 查询文本
            top_k: 返回结果数
            subject: 学科分类

        Returns:
            (检索到的文本列表, 元数据列表)
        """
        try:
            # 对查询文本进行嵌入
            query_embedding = self.embedding_manager.embed_text(query)

            # 执行检索
            results = self.retriever.search(
                query_embedding[0],
                top_k=top_k,
                subject_filter=subject
            )

            contexts = []
            metadata_list = []

            for text, similarity, metadata in results:
                contexts.append(text)
                # 强制转换为 Python float，避免 numpy 类型泄露导致 JSON 序列化失败
                metadata['similarity'] = float(similarity)
                metadata_list.append(metadata)

            logger.info(f"检索完成，获取 {len(contexts)} 个相关文档")
            return contexts, metadata_list
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return [], []

    def generate_answer(
        self,
        query: str,
        contexts: List[str],
        subject: str = "全部学科",
        temperature: float = 0.7
    ) -> str:
        """
        基于检索结果生成答案

        Args:
            query: 原始问题
            contexts: 检索到的上下文列表
            subject: 学科分类
            temperature: 温度参数

        Returns:
            生成的答案
        """
        try:
            # 拼接上下文
            context_text = "\n".join([
                f"【文档 {i+1}】\n{ctx}"
                for i, ctx in enumerate(contexts)
            ]) if contexts else "（未找到相关知识库内容）"

            # 格式化提示词
            answer_prompt = ANSWER_PROMPT.format(
                context=context_text,
                question=query
            )

            # 生成答案
            system_msg = SYSTEM_PROMPT.format(subject=subject)

            answer = self.qwen_model.chat(
                messages=[{"role": "user", "content": answer_prompt}],
                system_prompt=system_msg,
                temperature=temperature
            )

            return answer
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "抱歉，我在处理您的问题时出现了错误，请稍后重试。"

    def answer_question(
        self,
        question: str,
        subject: str = "全部学科",
        top_k: int = RAG_CONFIG["top_k"],
        temperature: float = 0.7
    ) -> Dict:
        """
        完整的问答流程

        Args:
            question: 用户问题
            subject: 学科分类
            top_k: 检索的文档数
            temperature: 温度参数

        Returns:
            包含答案、推理步骤、检索结果的字典
        """
        try:
            # 第一步：检索
            logger.info(f"处理问题: {question}")
            contexts, metadata_list = self.retrieve_context(
                question,
                top_k=top_k,
                subject=subject
            )

            # 第二步：生成答案
            answer = self.generate_answer(
                question,
                contexts,
                subject,
                temperature
            )

            # 第三步：提取推理步骤
            reasoning_steps = self.qwen_model.extract_reasoning_steps(answer)
            if not reasoning_steps:
                reasoning_steps = [
                    "初始化知识库检索",
                    "匹配相关文档",
                    "构建上下文推理链",
                    "生成专业回复"
                ]

            # 第四步（新增）：让 Qwen 评估本条回答的置信度
            answer_confidence = self.evaluate_confidence(question, answer, contexts, subject, metadata_list)

            # 第五步（新增）：把 retrieved_documents 规范化为前端友好的 knowledge_sources
            # 每个 source 包含：title / source / page / relevance / excerpt / subject
            knowledge_sources = []
            for i, (ctx, meta) in enumerate(zip(contexts, metadata_list)):
                sim = float(meta.get('similarity', 0.0))
                title = meta.get('title') or meta.get('source') or f"文档 {i + 1}"
                source = meta.get('source') or title
                page = meta.get('page')
                subject_field = meta.get('subject') or subject
                excerpt = ctx.strip()[:200] + ('...' if len(ctx) > 200 else '')
                relevance = int(round(sim * 100)) if 0 <= sim <= 1 else int(round(min(1.0, max(0.0, sim * 0.1)) * 100))
                knowledge_sources.append({
                    'id': f"src-{i + 1}",
                    'title': str(title),
                    'source': str(source),
                    'page': page,
                    'subject': str(subject_field),
                    'relevance': relevance,
                    'excerpt': excerpt,
                    'similarity': sim,
                })

            # 构建返回结果
            return {
                'answer': answer,
                'reasoning_steps': reasoning_steps,
                'retrieved_documents': [
                    {
                        'text': ctx,
                        'metadata': meta
                    }
                    for ctx, meta in zip(contexts, metadata_list)
                ],
                'knowledge_sources': knowledge_sources,
                'answer_confidence': answer_confidence,
                'subject': subject,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"问答流程失败: {e}")
            return {
                'answer': "抱歉，我在处理您的问题时出现了错误，请稍后重试。",
                'reasoning_steps': [],
                'retrieved_documents': [],
                'subject': subject,
                'status': 'error'
            }

    # ==================== 置信度评估（Qwen） ====================

    def evaluate_confidence(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        subject: str,
        metadata_list: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        调用 Qwen 模型评估本次回答的置信度。

        评估维度：
        1) **内容准确性**：回答是否与检索到的知识源一致
        2) **相关性**：回答是否直接、完整地解答了用户问题
        3) **证据充足度**：是否有足够的检索文档支撑这个答案

        返回示例：
        {
            "score": 0.87,
            "level": "高",
            "summary": "回答与 3 个检索文档内容一致，充分覆盖了问题核心。",
        }

        如果模型调用失败，会基于 retrieval 数量和平均 similarity 做一个保守兜底。
        """
        # --- 兜底策略：没有检索到任何文档时，给出较低的保守分数 ---
        if not contexts:
            return {
                "score": round(0.25, 4),
                "level": "低",
                "summary": "未检索到相关知识库文档，回答基于通用学科知识，请注意核对。",
            }

        # 从 metadata_list 里预先提取相似度（列表里每个元素是 RAG 检索的 meta）
        sims: List[float] = []
        if metadata_list:
            for m in metadata_list:
                if isinstance(m, dict):
                    val = m.get('similarity')
                    if isinstance(val, (int, float)):
                        sims.append(float(val))
        if not sims:
            sims = [0.3]

        try:
            # 构造评估 prompt —— 要求模型输出结构化 JSON
            context_snippet = "\n".join([
                f"【源 {i+1}】{c[:300]}"
                for i, c in enumerate(contexts[:3])
            ])

            evaluation_prompt = f"""你是一个严谨的答案质量评估员。请根据下面的「问题」「候选答案」「检索文档」给出 0.0-1.0 的置信度评分。

# 学科
{subject}

# 用户问题
{question}

# 候选答案
{answer[:800]}

# 检索到的相关文档
{context_snippet}

# 评分标准
- 0.0-0.4：答案与检索文档冲突，或严重偏离用户问题
- 0.4-0.7：部分覆盖问题，但证据不充分或存在推测
- 0.7-0.85：与检索文档一致，较好地回答了问题
- 0.85-1.0：完全吻合检索内容，回答充分、准确

# 输出格式（**只输出 JSON，不要任何额外文字**）
{{
  "score": <0.0-1.0>,
  "level": "高|中|低",
  "summary": "一句话说明评分理由（中文，不超过 40 字）"
}}"""

            raw = self.qwen_model.generate(
                evaluation_prompt,
                max_new_tokens=256,
                temperature=0.3,
            )

            # --- 尝试 1：严格 JSON 解析 ---
            parsed = None
            try:
                import json as _json
                cleaned = raw.strip()
                if '```' in cleaned:
                    start = cleaned.find('{')
                    end = cleaned.rfind('}')
                    if start != -1 and end != -1:
                        cleaned = cleaned[start:end + 1]
                parsed = _json.loads(cleaned)
            except Exception:
                parsed = None

            if parsed and isinstance(parsed.get('score'), (int, float)):
                return {
                    "score": round(float(parsed['score']), 4),
                    "level": str(parsed.get('level') or ''),
                    "summary": str(parsed.get('summary') or ''),
                }

            # --- 尝试 2：从文本中提取 0-1 之间的数字 ---
            import re
            m = re.search(r'(0\.\d+|1\.0|\b1\b)', raw)
            if m:
                score = round(float(m.group(1)), 4)
                level = "高" if score >= 0.8 else ("中" if score >= 0.5 else "低")
                return {
                    "score": score,
                    "level": level,
                    "summary": "从 Qwen 回复中提取数值，可能精度不足。",
                }

            # --- 兜底：基于检索文档数和平均相似度估算 ---
            avg_sim = sum(sims) / len(sims)
            estimated = round(min(1.0, 0.4 + 0.08 * len(contexts) + 0.2 * avg_sim), 4)
            return {
                "score": estimated,
                "level": "中",
                "summary": "Qwen 未返回结构化评分，已用检索质量估算。",
            }

        except Exception as e:
            logger.warning(f"置信度评估调用失败（不影响回答）: {e}")
            fallback = round(min(1.0, 0.35 + 0.08 * len(contexts)), 4)
            return {
                "score": fallback,
                "level": "中",
                "summary": "置信度评估服务异常，该分数为系统保守估算。",
            }
            logger.warning(f"置信度评估调用失败（不影响回答）: {e}")
            # 最终兜底：基于是否检索到内容给出一个保守分数
            fallback = round(min(1.0, 0.35 + 0.08 * len(contexts)), 4)
            return {
                "score": fallback,
                "level": "中",
                "summary": "置信度评估服务异常，该分数为系统保守估算。",
            }

    # ==================== 自动学科识别 ====================

    def detect_subject(self, question: str) -> Dict[str, Any]:
        """
        自动判断用户问题属于哪个学科。

        策略（两层融合）：
        1) 关键词规则：快速识别明确领域术语（如 "TCP"→计算机网络，"链表"→数据结构）
        2) 各学科 FAISS 索引检索：用语义相似度补充模糊场景
        3) 融合打分（规则 0.6 权重 + 检索 0.4 权重）

        Returns: {
            "detected_subject": "数据结构",  # 判定的学科
            "confidence": 0.85,              # 置信度
            "scores": {"数据结构": 0.85, ...}, # 各学科得分（全部转换为 Python float）
        }
        """
        if not question or not question.strip():
            return {
                "detected_subject": "全部学科",
                "confidence": 0.0,
                "scores": {},
            }

        q = question.strip()
        subjects = list(self.SUBJECT_KEYWORDS.keys())

        # ---------- 1) 关键词规则打分 ----------
        rule_scores: Dict[str, float] = {s: 0.0 for s in subjects}
        for subject, keywords in self.SUBJECT_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in q)
            if hits > 0:
                # 命中越多，分数越高（0.15 + 0.15 * hits），上限 1.0
                # 命中 1 个 = 0.30，命中 3 个 = 0.60，命中 6+ 个 ≈ 1.0
                rule_scores[subject] = min(1.0, 0.15 + 0.15 * hits)

        # ---------- 2) 各学科 FAISS 索引检索打分 ----------
        search_scores: Dict[str, float] = {s: 0.0 for s in subjects}
        try:
            emb = self.embedding_manager.embed_text(q)
            for subject in subjects:
                # 在每个学科索引中独立检索
                subject_results = self.retriever.search(
                    emb[0],
                    top_k=5,
                    subject_filter=subject
                )
                # 统计平均相似度
                if subject_results:
                    sims = [float(sim) for _, sim, _ in subject_results]
                    avg_sim = sum(sims) / len(sims) if sims else 0.0
                    # 命中数量也作为信号：检索到的文档越多，越可能属于该学科
                    count_signal = min(1.0, len(subject_results) / 5)
                    search_scores[subject] = round(count_signal * 0.5 + avg_sim * 0.5, 4)
        except Exception as e:
            logger.warning(f"自动识别：学科检索打分失败（不影响流程）: {e}")

        # ---------- 3) 融合打分（规则 0.6 + 检索 0.4） ----------
        # 全部 round(float(...), 4) 确保 Python 原生类型
        final_scores: Dict[str, float] = {}
        for s in subjects:
            final_scores[s] = round(float(rule_scores[s]) * 0.6 + float(search_scores[s]) * 0.4, 4)

        # 选择最高分学科
        sorted_subjects = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        best_subject = sorted_subjects[0][0]
        best_score = float(sorted_subjects[0][1])

        # 如果任何学科得分都很低（< 0.1），认为没有明确学科，返回"全部学科"
        if best_score < 0.1:
            detected = "全部学科"
            confidence = best_score
        else:
            detected = best_subject
            confidence = best_score

        logger.info(
            f"自动识别学科: 问题='{q[:40]}...' → {detected} (置信度 {confidence}, "
            f"规则得分={rule_scores[best_subject]}, 检索得分={search_scores[best_subject]})"
        )

        return {
            "detected_subject": detected,
            "confidence": float(confidence),
            "scores": {k: float(v) for k, v in final_scores.items()},
        }

    def add_knowledge(
        self,
        documents: List[Dict],
        embeddings=None,
        subject: str = "全部学科",
    ) -> bool:
        try:
            if not documents:
                return False
            if embeddings is None:
                texts = [doc.get('text', '') for doc in documents]
                embeddings = self.embedding_manager.embed_text(texts)
            # 按学科写入对应索引
            self.retriever.add_documents(embeddings, documents, subject=subject)
            return True
        except Exception as e:
            logger.error(f"添加知识库文档失败[{subject}]: {e}")
            return False

    def list_knowledge(
        self,
        subject: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """列出知识库文档摘要（用于前端展示）。"""
        return self.retriever.list_documents(subject=subject, limit=limit)

    def clear_knowledge(self, subject: str) -> bool:
        """清空指定学科的知识库索引。"""
        return self.retriever.clear_subject(subject)

    def get_stats(self) -> Dict:
        """获取引擎统计信息"""
        return {
            'retriever_stats': self.retriever.get_stats(),
            'embedding_dim': self.embedding_manager.get_dimension()
        }