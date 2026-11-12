"""幂等 seed：5 信源 / 60 条原始页 / 48 篇抽取稿 / 12 个去重簇 / 6 个事件 / 3 账号。

场景（batch-plan gb-563 三江传媒）：
  * 5 个信源（3 家同行媒体 + 1 个政务号 + 1 个自媒体）；
  * 60 条抓取记录，其中 48 条被算法 A（Readability 式密度抽取）抽出正文，
    2 条进入低置信队列（conf 0.32 / 0.21，需人工校正），12 条采集失败/待解析；
  * 12 个去重簇（3×7 + 3×5 + 6×2，含 3 条跨簇疑似边），种子态由 corpus 的成员
    关系落库，真实数字由「运行去重」的 MinHash + LSH 重算覆盖；
  * 6 个事件挂在 11-08 / 11-10 两天，日报按日聚合。

幂等规则：所有写入按自然键（email / 信源名 / url / raw_item_id / topic_label /
事件标题+日期）先查后建，已存在则跳过——**不覆盖用户已做的校正、确认与拆分**。
重复执行只在最后打印同一行 SEED_SUMMARY（本行被 batch QA 用于判幂等）。

运行：SEED_DEMO=true 时由 entrypoint 自动执行一次；也可手动：
    docker compose exec backend python scripts/seed_demo.py
"""
import hashlib
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import corpus  # noqa: E402
from src.config.database import SessionLocal, init_db  # noqa: E402
from src.constants.enums import (  # noqa: E402
    ClusterStatus,
    RawStatus,
    SourceType,
)
from src.models import (  # noqa: E402
    Article,
    Cluster,
    ClusterMember,
    Event,
    RawItem,
    Source,
    SuspectedEdge,
    User,
)
from src.services.dedup import _representative  # noqa: E402
from src.services import extraction_service  # noqa: E402
from src.utils.logger import log_event  # noqa: E402
from src.utils.password import hash_password  # noqa: E402
from src.utils.textnorm import jaccard, normalize_text, shingles  # noqa: E402

DEMO_PASSWORD = "Demo@2026"
ACCOUNTS = [
    ("admin@dedupwire.io", "顾砚舟", "admin"),
    ("analyst@dedupwire.io", "沈知微", "analyst"),
    ("viewer@dedupwire.io", "周予安", "viewer"),
]
SHINGLE_SIZE = 4


def _ensure_users(db: Session) -> None:
    for email, display_name, role in ACCOUNTS:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            continue
        db.add(
            User(
                email=email,
                display_name=display_name,
                role=role,
                password_hash=hash_password(DEMO_PASSWORD),
            )
        )
    db.commit()


def _ensure_sources(db: Session) -> dict[str, Source]:
    result: dict[str, Source] = {}
    now = datetime(2026, 11, 10, 9, 0)
    for index, spec in enumerate(corpus.SOURCES):
        row = db.scalar(select(Source).where(Source.name == spec["name"]))
        if row is None:
            row = Source(
                name=spec["name"],
                homepage=spec["homepage"],
                type=spec["type"],
                weight=spec["weight"],
                extract_rule_status=spec["extract_rule_status"],
                description=spec["description"],
                enabled=True,
                last_fetched_at=now,
            )
            db.add(row)
            db.flush()
        result[spec["slug"]] = row
    db.commit()
    return result


def _ensure_raws_and_articles(db: Session, sources: dict[str, Source]) -> dict[str, int]:
    """Insert raw items + run algorithm A for the 48 article pages (idempotent)."""
    article_ids: dict[str, int] = {}
    specs = corpus.build_articles()
    for spec in specs:
        raw = db.scalar(select(RawItem).where(RawItem.url == spec["url"]))
        if raw is None:
            raw = RawItem(
                source_id=sources[spec["source_slug"]].id,
                url=spec["url"],
                title=spec["title"],
                published_at=spec["published_at"],
                raw_html=spec["html"],
                fetched_at=spec["published_at"],
                status=RawStatus.NEW.value,
            )
            db.add(raw)
            db.flush()
        article = db.scalar(select(Article).where(Article.raw_item_id == raw.id))
        if article is None:
            article = extraction_service.extract_and_store(db, raw, agent=spec["author"])
            db.flush()
        article_ids[spec["key"]] = article.id
    for spec in corpus.extra_raws():
        raw = db.scalar(select(RawItem).where(RawItem.url == spec["url"]))
        if raw is None:
            raw = RawItem(
                source_id=sources[spec["source_slug"]].id,
                url=spec["url"],
                title=spec["title"],
                published_at=spec["published_at"],
                raw_html=spec["html"],
                fetched_at=spec["published_at"],
                status=spec["status"],
                error_note=spec["error_note"],
            )
            db.add(raw)
        elif not raw.raw_html and spec["html"]:
            # 旧库的采集失败页没有快照：补上快照，按信源重抽才有可重算的原始页。
            raw.raw_html = spec["html"]
    db.commit()
    return article_ids


def _shingle_set(text: str) -> set[str]:
    return shingles(normalize_text(text), SHINGLE_SIZE)


def _ensure_clusters(db: Session, article_ids: dict[str, int]) -> dict[str, int]:
    """Seed-state clusters from the corpus plan; skipped entirely once clusters exist."""
    existing = db.scalar(select(func.count(Cluster.id))) or 0
    if existing:
        return {}
    plan = corpus.build_clusters()
    cluster_ids: dict[str, int] = {}
    for item in plan:
        labels = corpus.PAIRS
        member_ids = [article_ids[key] for key in item["member_keys"]]
        rep_id = article_ids[item["rep_key"]]
        articles = {
            article.id: article
            for article in db.scalars(select(Article).where(Article.id.in_(member_ids))).all()
        }
        docs = {
            aid: type(
                "Doc",
                (),
                {
                    "article_id": aid,
                    "text": articles[aid].body_text,
                    "word_count": articles[aid].word_count,
                    "published_at": articles[aid].raw_item.published_at,
                    "source_weight": articles[aid].raw_item.source.weight,
                },
            )()
            for aid in member_ids
        }
        sims = {}
        rep_set = _shingle_set(articles[rep_id].body_text)
        for aid in member_ids:
            sims[aid] = 1.0 if aid == rep_id else round(
                jaccard(rep_set, _shingle_set(articles[aid].body_text)), 4
            )
        others = [sim for aid, sim in sims.items() if aid != rep_id]
        cluster = Cluster(
            run_id=None,
            topic_label=articles[rep_id].raw_item.title,
            representative_article_id=rep_id,
            member_count=len(member_ids),
            mean_similarity=round(sum(others) / len(others), 4) if others else 1.0,
            first_seen_at=min(articles[aid].raw_item.published_at for aid in member_ids),
            status=ClusterStatus.AUTO.value,
        )
        db.add(cluster)
        db.flush()
        for aid in member_ids:
            db.add(
                ClusterMember(cluster_id=cluster.id, article_id=aid, similarity_to_rep=sims[aid])
            )
        cluster_ids[item["rep_key"].split("-")[0] if "-" in item["rep_key"] else item["rep_key"]] = cluster.id
        # topic_key 的映射：正文 key 前缀就是主题 key（pair 的 key 也是 pair['key']）
        topic_key = item["rep_key"].rsplit("-", 1)[0]
        cluster_ids[topic_key] = cluster.id

    # 3 条跨簇疑似边（公告原文共用），相似度用同一套 Jaccard 真算
    for key_a, key_b in corpus.suspected_pairs():
        aid_a, aid_b = article_ids[key_a], article_ids[key_b]
        article_a = db.get(Article, aid_a)
        article_b = db.get(Article, aid_b)
        similarity = round(jaccard(_shingle_set(article_a.body_text), _shingle_set(article_b.body_text)), 4)
        db.add(
            SuspectedEdge(
                run_id=None,
                article_a_id=aid_a,
                article_b_id=aid_b,
                similarity=similarity,
            )
        )
    db.commit()
    return cluster_ids


def _ensure_events(db: Session, article_ids: dict[str, int]) -> None:
    for spec in corpus.EVENTS:
        event_day = date.fromisoformat(spec["event_date"])
        existing = db.scalar(
            select(Event).where(Event.title == spec["title"], Event.event_date == event_day)
        )
        if existing is not None:
            continue
        # 事件挂到该主题的簇：用主题首篇（member 1）的代表稿反查簇
        rep_key = f"{spec['topic_key']}-1" if f"{spec['topic_key']}-1" in article_ids else f"{spec['topic_key']}-a1"
        rep_id = article_ids.get(rep_key)
        cluster_id = None
        if rep_id is not None:
            cluster = db.scalar(select(Cluster).where(Cluster.representative_article_id == rep_id))
            cluster_id = cluster.id if cluster else None
        db.add(
            Event(
                title=spec["title"],
                category=spec["category"],
                event_date=event_day,
                region=spec["region"],
                note=spec["note"],
                cluster_id=cluster_id,
            )
        )
    db.commit()


def _counts(db: Session) -> dict[str, int]:
    return {
        "sources": db.scalar(select(func.count(Source.id))) or 0,
        "raws": db.scalar(select(func.count(RawItem.id))) or 0,
        "articles": db.scalar(select(func.count(Article.id))) or 0,
        "clusters": db.scalar(select(func.count(Cluster.id))) or 0,
        "events": db.scalar(select(func.count(Event.id))) or 0,
        "users": db.scalar(select(func.count(User.id))) or 0,
    }


def main() -> int:
    init_db()
    db: Session = SessionLocal()
    try:
        _ensure_users(db)
        sources = _ensure_sources(db)
        article_ids = _ensure_raws_and_articles(db, sources)
        _ensure_clusters(db, article_ids)
        _ensure_events(db, article_ids)
        counts = _counts(db)
        line = (
            f"SEED_SUMMARY brand=dedupwire sources={counts['sources']} raws={counts['raws']} "
            f"articles={counts['articles']} clusters={counts['clusters']} "
            f"events={counts['events']} users={counts['users']}"
        )
        print(line, flush=True)
        log_event("seed.done", **counts)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
