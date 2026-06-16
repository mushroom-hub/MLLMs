#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库批量构建脚本
====================
扫描 dataset/408/408推荐用书及答案 目录下的 PDF，
按文件名自动识别学科（数据结构 / 计算机组成原理 / 计算机网络 / 操作系统），
提取文本并写入对应的 FAISS 索引文件。

用法:
    cd backend
    python scripts/build_knowledge_base.py

增量构建：如果某书的索引已存在，会跳过（--force 可强制重建）。
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 让脚本可以直接 import backend 模块
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent  # backend/
PROJECT_DIR = BACKEND_DIR.parent  # 大作业/
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

# ------ 日志 ------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("kb_builder")

# ===== 路径配置 =====
PDF_ROOT = PROJECT_DIR / "dataset" / "408" / "408推荐用书及答案"

# ===== 学科识别关键字 =====
# 每个学科对应一组关键字，出现在文件名中即判定为该学科
SUBJECT_KEYWORDS: Dict[str, List[str]] = {
    "数据结构": [
        "数据结构"
    ],
    "计算机组成原理": [
        "计算机组成原理",
        "计算机组成与系统结构",
        "计组"
    ],
    "计算机网络": [
        "计算机网络",
        "计网",
    ],
    "操作系统": [
        "操作系统",
        "os"
    ],
}


def detect_subject(filename: str) -> Optional[str]:
    """
    根据文件名判断所属学科。
    返回: 学科名 或 None（识别失败）
    """
    name = filename
    # 逐学科匹配（按 SUBJECT_KEYWORDS 的顺序，先匹配到的优先）
    for subject, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return subject
    return None


def list_pdf_files(root: Path) -> List[Path]:
    """列出根目录下所有 PDF 文件。"""
    if not root.exists():
        logger.error(f"PDF 目录不存在: {root}")
        return []
    pdfs = sorted([p for p in root.rglob("*.pdf") if p.is_file()])
    logger.info(f"发现 {len(pdfs)} 个 PDF 文件")
    return pdfs


def classify_pdfs(pdfs: List[Path]) -> Dict[str, List[Path]]:
    """
    按学科对 PDF 进行分类。
    返回: {学科名: [pdf_path, ...]}
    """
    result: Dict[str, List[Path]] = {s: [] for s in SUBJECT_KEYWORDS}
    unknown: List[Path] = []

    for pdf in pdfs:
        subject = detect_subject(pdf.name)
        if subject:
            result[subject].append(pdf)
            logger.info(f"  [{subject}] {pdf.name}")
        else:
            unknown.append(pdf)
            logger.warning(f"  [未识别] {pdf.name}")

    if unknown:
        logger.warning(f"\n以下 {len(unknown)} 个文件未能识别学科，将跳过：")
        for p in unknown:
            logger.warning(f"  - {p.name}")

    return result


def build_knowledge_base(force: bool = False, limit_per_subject: Optional[int] = None):
    """
    主构建流程：
    1. 扫描 PDF 并分类
    2. 初始化 RAGEngine
    3. 逐学科、逐 PDF 提取文本并写入索引
    """
    # ---- 第一步：扫描并分类 ----
    logger.info("=" * 60)
    logger.info(f"扫描目录: {PDF_ROOT}")
    pdfs = list_pdf_files(PDF_ROOT)
    if not pdfs:
        logger.error("未找到任何 PDF 文件，终止。")
        return

    classified = classify_pdfs(pdfs)

    logger.info("\n" + "=" * 60)
    logger.info("学科分类统计：")
    for subject, files in classified.items():
        logger.info(f"  {subject}: {len(files)} 本")
    logger.info("=" * 60)

    # ---- 第二步：初始化 RAGEngine ----
    logger.info("\n正在初始化 RAG 引擎（加载 m3e-base 嵌入模型...）")
    try:
        from agent.rag import RAGEngine
        rag = RAGEngine()
    except Exception as e:
        logger.error(f"RAG 引擎初始化失败: {e}")
        logger.error("请确认：")
        logger.error("  1. embedding/m3e-base 模型已下载")
        logger.error("  2. sentence-transformers / faiss-cpu / pymupdf 已安装")
        sys.exit(1)

    logger.info("RAG 引擎初始化完成")

    # 如果是 force 模式，先清空所有学科索引
    if force:
        logger.warning("--force 模式：将清空所有已有学科索引")
        for subject in SUBJECT_KEYWORDS.keys():
            rag.clear_knowledge(subject)
        logger.info("已清空所有学科索引")

    # ---- 第三步：逐学科、逐 PDF 处理 ----
    from agent.multimodal import MultimodalProcessor
    processor = MultimodalProcessor()

    total_docs = 0
    total_pages = 0

    for subject, files in classified.items():
        if not files:
            continue
        if limit_per_subject:
            files = files[:limit_per_subject]

        logger.info(f"\n{'='*60}")
        logger.info(f"处理学科: {subject}（{len(files)} 本书）")
        logger.info("=" * 60)

        subject_pages = 0
        subject_files = 0

        for idx, pdf_path in enumerate(files, 1):
            logger.info(f"  [{idx}/{len(files)}] 正在处理: {pdf_path.name}")
            try:
                docs = processor.process_pdf(str(pdf_path))
                if not docs:
                    logger.warning(f"    ! 未提取到任何文本，跳过")
                    continue

                # 过滤掉几乎为空的页（文本字符 < 20）
                valid_docs = [d for d in docs if d.get('text') and len(d['text'].strip()) >= 20]
                if not valid_docs:
                    logger.warning(f"    ! 所有页内容过短，跳过")
                    continue

                # 写入索引
                ok = rag.add_knowledge(valid_docs, subject=subject)
                if ok:
                    subject_pages += len(valid_docs)
                    subject_files += 1
                    logger.info(f"    ✓ 添加 {len(valid_docs)} 页到 [{subject}] 知识库")
                else:
                    logger.error(f"    ✗ 添加失败")

            except Exception as e:
                logger.error(f"    ✗ 处理出错: {e}")
                continue

        total_docs += subject_files
        total_pages += subject_pages
        logger.info(f"\n  学科 [{subject}] 完成: {subject_files} 本书，{subject_pages} 页有效内容")

    # ---- 第四步：输出统计 ----
    logger.info("\n" + "=" * 60)
    logger.info("知识库构建完成！")
    logger.info("=" * 60)
    stats = rag.get_stats()
    retriever_stats = stats.get("retriever_stats", {})
    logger.info(f"总文档数: {retriever_stats.get('total_documents', 0)}")
    logger.info(f"向量维度: {retriever_stats.get('dimension', 'N/A')}")
    logger.info(f"\n各学科详情:")
    for sub, info in retriever_stats.get("subjects", {}).items():
        logger.info(f"  {sub}: {info.get('documents', 0)} 条记录")
        logger.info(f"    └─ 索引文件: {info.get('index_file', '')}")
    logger.info(f"\n本次新增: {total_docs} 本书，{total_pages} 页")
    logger.info("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="构建 408 学科知识库")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重建：先清空所有学科索引再构建",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="每个学科最多处理的 PDF 数量（用于测试）",
    )
    args = parser.parse_args()

    logger.info("EduBrain AI - 408 知识库构建工具")
    logger.info(f"工作目录: {BACKEND_DIR}")
    logger.info(f"强制重建: {args.force}")
    if args.limit:
        logger.info(f"每学科上限: {args.limit} 本 PDF")

    build_knowledge_base(force=args.force, limit_per_subject=args.limit)


if __name__ == "__main__":
    main()