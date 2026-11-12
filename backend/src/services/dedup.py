"""算法 B：MinHash + LSH 近似去重聚类（纯标准库，可复现）。

流程：正文归一化（去空白/标点、数字占位）→ 中文 4-gram shingle → MinHash 128
签名（blake2b 64bit + 固定 seed 的 128 组线性置换）→ LSH 32 band × 4 row 分桶 →
候选对 → 精确 Jaccard 复核（>= threshold 判重合并，[suspect, threshold) 记疑似边）
→ 并查集合并簇 → 代表稿打分。

代表稿打分：``0.5 * 正文长度归一 + 0.3 * 发布时间最早归一 + 0.2 * 信源权重``。

可复现条件：``hash_seed`` 固定（默认 20261110）、置乱系数由 ``random.Random(seed)``
生成、shingle 集合按字符串排序后再取最小值，因此同一语料任意次运行结果一致。
"""
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime

from src.utils.textnorm import jaccard, normalize_text, shingles

MOD = (1 << 61) - 1


@dataclass
class DedupParams:
    threshold: float = 0.72
    suspect_threshold: float = 0.55
    num_perm: int = 128
    bands: int = 32
    shingle_size: int = 4
    hash_seed: int = 20261110

    @property
    def rows(self) -> int:
        if self.bands <= 0:
            return self.num_perm
        return max(1, self.num_perm // self.bands)


@dataclass
class ArticleDoc:
    article_id: int
    text: str
    title: str
    published_at: datetime
    source_id: int
    source_weight: int
    word_count: int = 0


@dataclass
class ClusterResult:
    members: list[int]
    representative_id: int
    topic_label: str
    mean_similarity: float
    first_seen_at: datetime | None
    member_similarity: dict[int, float] = field(default_factory=dict)


@dataclass
class SuspectEdgeResult:
    article_a_id: int
    article_b_id: int
    similarity: float


@dataclass
class DedupResult:
    params: DedupParams
    article_count: int
    clusters: list[ClusterResult]
    suspect_edges: list[SuspectEdgeResult]
    candidate_pairs: int
    signatures: dict[int, list[int]] = field(default_factory=dict)

    @property
    def duplicate_rate(self) -> float:
        if not self.article_count:
            return 0.0
        return round((self.article_count - len(self.clusters)) / self.article_count, 4)


def _base_hash(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % MOD


def _permutations(params: DedupParams) -> list[tuple[int, int]]:
    rng = random.Random(params.hash_seed)
    return [
        (rng.randrange(1, MOD - 1), rng.randrange(0, MOD - 1)) for _ in range(params.num_perm)
    ]


def minhash_signature(norm_text: str, perms: list[tuple[int, int]], params: DedupParams) -> list[int]:
    tokens = shingles(norm_text, params.shingle_size)
    if not tokens:
        return [0] * params.num_perm
    hashes = [_base_hash(token) for token in tokens]
    signature = []
    for a, b in perms:
        signature.append(min((a * h + b) % MOD for h in hashes))
    return signature


def lsh_candidates(signatures: dict[int, list[int]], params: DedupParams) -> set[tuple[int, int]]:
    rows = params.rows
    bands = min(params.bands, max(1, params.num_perm // rows))
    pairs: set[tuple[int, int]] = set()
    for band in range(bands):
        buckets: dict[tuple[int, ...], list[int]] = {}
        start = band * rows
        for article_id, sig in signatures.items():
            key = tuple(sig[start : start + rows])
            buckets.setdefault(key, []).append(article_id)
        for ids in buckets.values():
            if len(ids) < 2:
                continue
            ids = sorted(ids)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pairs.add((ids[i], ids[j]))
    return pairs


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[int, int] = {}

    def add(self, item: int) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: int) -> int:
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != root:
            self.parent[item], item = root, self.parent[item]
        return root

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _representative(members: list[int], docs: dict[int, ArticleDoc]) -> int:
    word_counts = [max(1, docs[mid].word_count or len(docs[mid].text)) for mid in members]
    max_words = max(word_counts)
    times = [docs[mid].published_at for mid in members]
    earliest, latest = min(times), max(times)
    span = max(1.0, (latest - earliest).total_seconds())

    def score(article_id: int) -> tuple[float, float, int]:
        doc = docs[article_id]
        words = max(1, doc.word_count or len(doc.text))
        longest = words / max_words
        if span <= 1.0:
            earliest_norm = 1.0
        else:
            earliest_norm = 1.0 - (doc.published_at - earliest).total_seconds() / span
        weight = min(1.0, doc.source_weight / 5.0)
        total = 0.5 * longest + 0.3 * earliest_norm + 0.2 * weight
        return (total, -article_id)

    return max(members, key=score)


def _title_label(title: str, fallback: str) -> str:
    title = (title or "").strip()
    if not title:
        return fallback
    return title if len(title) <= 40 else title[:40] + "…"


def run_dedup(docs: list[ArticleDoc], params: DedupParams | None = None) -> DedupResult:
    params = params or DedupParams()
    perms = _permutations(params)
    by_id = {doc.article_id: doc for doc in docs}
    shingle_sets: dict[int, set[str]] = {}
    signatures: dict[int, list[int]] = {}
    for doc in docs:
        norm = normalize_text(doc.text)
        shingle_sets[doc.article_id] = shingles(norm, params.shingle_size)
        signatures[doc.article_id] = minhash_signature(norm, perms, params)

    candidates = lsh_candidates(signatures, params)
    uf = _UnionFind()
    for doc in docs:
        uf.add(doc.article_id)

    merged_pairs: list[tuple[int, int, float]] = []
    suspect_pairs: list[tuple[int, int, float]] = []
    for a, b in sorted(candidates):
        sim = jaccard(shingle_sets[a], shingle_sets[b])
        if sim >= params.threshold:
            uf.union(a, b)
            merged_pairs.append((a, b, sim))
        elif sim >= params.suspect_threshold:
            suspect_pairs.append((a, b, sim))

    groups: dict[int, list[int]] = {}
    for doc in docs:
        groups.setdefault(uf.find(doc.article_id), []).append(doc.article_id)

    clusters: list[ClusterResult] = []
    cluster_of: dict[int, int] = {}
    for root in sorted(groups):
        members = sorted(groups[root])
        if len(members) < 2:
            continue
        rep = _representative(members, by_id)
        sims = {}
        for mid in members:
            sims[mid] = 1.0 if mid == rep else round(jaccard(shingle_sets[rep], shingle_sets[mid]), 4)
        others = [sims[mid] for mid in members if mid != rep]
        mean_sim = round(sum(others) / len(others), 4) if others else 1.0
        first_seen = min(by_id[mid].published_at for mid in members)
        idx = len(clusters)
        clusters.append(
            ClusterResult(
                members=members,
                representative_id=rep,
                topic_label=_title_label(by_id[rep].title, f"簇 {idx + 1}"),
                mean_similarity=mean_sim,
                first_seen_at=first_seen,
                member_similarity=sims,
            )
        )
        for mid in members:
            cluster_of[mid] = idx

    suspect_edges: list[SuspectEdgeResult] = []
    for a, b, sim in sorted(suspect_pairs, key=lambda item: (-item[2], item[0], item[1])):
        # 只有跨簇（或未成簇）的候选对才是「疑似边」，簇内近邻不算。
        if a in cluster_of and b in cluster_of and cluster_of[a] == cluster_of[b]:
            continue
        suspect_edges.append(
            SuspectEdgeResult(article_a_id=a, article_b_id=b, similarity=round(sim, 4))
        )

    return DedupResult(
        params=params,
        article_count=len(docs),
        clusters=clusters,
        suspect_edges=suspect_edges,
        candidate_pairs=len(candidates),
        signatures=signatures,
    )
