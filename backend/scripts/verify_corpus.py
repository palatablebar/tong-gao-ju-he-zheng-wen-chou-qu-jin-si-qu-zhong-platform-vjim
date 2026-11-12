"""Deterministic local verifier for the two core algorithms (no DB, no network).

用法（在 backend/ 目录）：
    python3 scripts/verify_corpus.py

它把 corpus.py 生成的 48 篇 HTML 跑一遍正文抽取，再把抽取结果送进
MinHash + LSH，打印簇结构 / 疑似边 / 低置信文章，用于确认 seed 与
「运行去重」的预期数字（12 簇、3 疑似边、1 篇 conf≈0.32 低置信）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus  # noqa: E402
from src.services.dedup import ArticleDoc, DedupParams, run_dedup  # noqa: E402
from src.services.readability import extract  # noqa: E402
from src.utils.textnorm import chinese_char_count  # noqa: E402


def main() -> int:
    articles = corpus.build_articles()
    extracted = []
    for item in articles:
        result = extract(item["html"])
        extracted.append((item, result))

    print("== readability ==")
    lows = 0
    for item, result in extracted:
        flag = "LOW" if result.extract_confidence < 0.4 else "   "
        if flag.strip():
            lows += 1
            print(
                f"{flag} {item['key']:<16} conf={result.extract_confidence:<5} "
                f"extractor={result.extractor:<11} chars={result.body_chars:<4} "
                f"density={result.content_density:<6} top={result.top_score}"
            )
    normal = [r.extract_confidence for _, r in extracted if r.extract_confidence >= 0.4]
    print(f"normal confidence: min={min(normal)} max={max(normal)} low_count={lows}")

    docs = []
    for item, result in extracted:
        source_weight = corpus.SOURCES[item["source_index"]]["weight"]
        docs.append(
            ArticleDoc(
                article_id=len(docs) + 1,
                text=result.body_text,
                title=item["title"],
                published_at=item["published_at"],
                source_id=item["source_index"] + 1,
                source_weight=source_weight,
                word_count=chinese_char_count(result.body_text),
            )
        )
    result = run_dedup(docs, DedupParams(threshold=0.72, suspect_threshold=0.55))
    print("\n== dedup ==")
    print(f"articles={result.article_count} clusters={len(result.clusters)} "
          f"suspects={len(result.suspect_edges)} candidates={result.candidate_pairs} "
          f"duplicate_rate={result.duplicate_rate}")
    for idx, cluster in enumerate(result.clusters, 1):
        print(f"  cluster{idx:02d} size={len(cluster.members)} mean_sim={cluster.mean_similarity} "
              f"label={cluster.topic_label}")
    print("suspect edges:")
    for edge in result.suspect_edges:
        print(f"  {edge.article_a_id} ~ {edge.article_b_id} sim={edge.similarity}")
    sizes = sorted((len(c.members) for c in result.clusters), reverse=True)
    print("cluster sizes:", sizes)
    expected = [7, 7, 7, 5, 5, 5, 2, 2, 2, 2, 2, 2]
    ok = sizes == expected and len(result.suspect_edges) == 3
    print("EXPECTED MATCH:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
