import json
import logging
import sys
import os
from typing import List, Dict, Tuple
from collections import defaultdict

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from agent.rag import RAGEngine
from config import SUBJECTS

logging.basicConfig(level=logging.INFO)

# ========== 测试数据集 ==========
TEST_CASES = {
    "数据结构": [
        "链表的头插法和尾插法区别",
        "二叉树的前中后序遍历递归实现",
        "图的深度优先搜索DFS算法",
        "哈希冲突的解决方法有哪些",
        "堆排序的时间复杂度分析",
        "动态规划和贪心的适用场景",
        "并查集解决连通性问题",
        "AVL树和红黑树的平衡策略对比",
        "Trie字典树的插入和查找",
        "拓扑排序Kahn算法步骤",
    ],
    "计算机网络": [
        "TCP三次握手和四次挥手机制",
        "HTTP和HTTPS的主要区别",
        "DNS域名解析的完整过程",
        "ARP协议如何获取MAC地址",
        "TCP拥塞控制四个算法阶段",
        "OSI七层模型各层功能",
        "路由器和交换机的工作层次",
        "子网划分和CIDR表示方法",
        "Socket编程的基本流程",
        "HTTP/2相比HTTP/1.1的改进",
    ],
    "操作系统": [
        "进程和线程的核心区别",
        "死锁产生的四个必要条件",
        "LRU页面置换算法实现",
        "进程调度算法FCFS SJF RR",
        "虚拟内存的实现原理",
        "信号量和互斥锁解决同步问题",
        "文件系统的inode结构",
        "系统调用和库函数的区别",
        "上下文切换的开销分析",
        "段页式内存管理方式",
    ],
    "计算机组成原理": [
        "冯诺依曼体系结构五大部件",
        "Cache直接映射组相联全相联",
        "MIPS指令格式R型I型J型",
        "流水线冒险数据冒险控制冒险",
        "DRAM和SRAM存储原理差异",
        "中断和异常的处理流程",
        "总线的分类和仲裁机制",
        "ALU运算器的基本结构",
        "指令周期的四个阶段",
        "存储器层次结构设计思想",
    ],
}

# ========== 执行测试 ==========
def run_test(engine: RAGEngine) -> Dict:
    """对所有测试样本执行分类，返回详细结果"""
    results = {
        "total": 0,
        "correct": 0,
        "by_subject": defaultdict(lambda: {"total": 0, "correct": 0}),
        "details": [],
    }

    for true_subject, questions in TEST_CASES.items():
        for q in questions:
            detection = engine.detect_subject(q)
            predicted = detection["detected_subject"]
            is_correct = predicted == true_subject

            results["total"] += 1
            results["by_subject"][true_subject]["total"] += 1
            if is_correct:
                results["correct"] += 1
                results["by_subject"][true_subject]["correct"] += 1

            results["details"].append({
                "question": q,
                "true_subject": true_subject,
                "predicted_subject": predicted,
                "confidence": detection["confidence"],
                "scores": detection["scores"],
                "correct": is_correct,
            })
            print(f"[{is_correct and '✓' or '✗'}] {q[:30]:<30} "
                  f"预测:{predicted:<10} 实际:{true_subject:<10} "
                  f"置信度:{detection['confidence']:.2f}")
    return results

# ========== 计算指标 ==========
def calc_metrics(results: Dict) -> Dict:
    """计算各学科的精确率、召回率、F1"""
    # 构建混淆矩阵
    confusion = defaultdict(lambda: defaultdict(int))
    for d in results["details"]:
        confusion[d["true_subject"]][d["predicted_subject"]] += 1

    metrics = {}
    valid_subjects = list(TEST_CASES.keys())

    for sub in valid_subjects:
        tp = confusion[sub][sub]
        fp = sum(confusion[other][sub] for other in valid_subjects if other != sub)
        fn = sum(confusion[sub][other] for other in valid_subjects if other != sub)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        metrics[sub] = {
            "TP": tp, "FP": fp, "FN": fn,
            "Precision": round(precision, 4),
            "Recall": round(recall, 4),
            "F1": round(f1, 4),
        }

    # 宏平均（各学科平均）
    macro_p = sum(m["Precision"] for m in metrics.values()) / len(metrics)
    macro_r = sum(m["Recall"] for m in metrics.values()) / len(metrics)
    macro_f1 = sum(m["F1"] for m in metrics.values()) / len(metrics)

    metrics["_macro_avg"] = {
        "Precision": round(macro_p, 4),
        "Recall": round(macro_r, 4),
        "F1": round(macro_f1, 4),
    }
    metrics["_accuracy"] = round(results["correct"] / results["total"], 4)
    return metrics

# ========== 主入口 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("学科分类准确性测试")
    print("=" * 60)

    engine = RAGEngine()
    results = run_test(engine)
    metrics = calc_metrics(results)

    print("\n" + "=" * 60)
    print(f"整体准确率: {metrics['_accuracy']:.2%}")
    print(f"宏平均 F1:  {metrics['_macro_avg']['F1']:.4f}")
    print("-" * 60)
    for sub, m in metrics.items():
        if sub.startswith("_"):
            continue
        print(f"{sub:<14} P={m['Precision']:.2f}  "
              f"R={m['Recall']:.2f}  F1={m['F1']:.2f}  "
              f"(TP={m['TP']}, FP={m['FP']}, FN={m['FN']})")

    # 保存详细结果
    with open("subject_classification_report.json", "w", encoding="utf-8") as f:
        json.dump({"results": results, "metrics": metrics}, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存到 subject_classification_report.json")