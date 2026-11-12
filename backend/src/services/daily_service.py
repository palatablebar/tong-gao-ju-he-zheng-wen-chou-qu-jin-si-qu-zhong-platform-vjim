"""日报：按日聚合事件 + 代表稿，输出 Markdown / CSV（后端生成，前端只负责下载）。"""
import csv
import io
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Cluster, Event, SuspectedEdge
from src.services import audit_service
from src.utils.serializers import event_out


def _build(db: Session, date_text: str) -> dict:
    target_day = date.fromisoformat(date_text)
    events = db.scalars(
        select(Event).where(Event.event_date == target_day).order_by(Event.category, Event.id)
    ).all()
    clusters = {row.id: row for row in db.scalars(select(Cluster)).all()}
    payload = [event_out(event, clusters.get(event.cluster_id)) for event in events]
    total_articles = 0
    for cluster in clusters.values():
        total_articles += cluster.member_count
    suspect_count = len(db.scalars(select(SuspectedEdge)).all())
    cluster_count = len(clusters)
    duplicate_rate = (
        round((total_articles - cluster_count) / total_articles, 4) if total_articles else 0.0
    )
    return {
        "date": date_text,
        "events": payload,
        "summary": {
            "date": date_text,
            "event_count": len(payload),
            "article_count": total_articles,
            "cluster_count": cluster_count,
            "suspect_count": suspect_count,
            "duplicate_rate": duplicate_rate,
        },
    }


def _markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        f"# 三江传媒 · 通稿日报（{report['date']}）",
        "",
        f"> 当日事件 {summary['event_count']} 条；通稿库 {summary['article_count']} 篇 / "
        f"{summary['cluster_count']} 簇；疑似边 {summary['suspect_count']} 条；"
        f"重复率 {summary['duplicate_rate'] * 100:.1f}%（(篇数-簇数)/篇数）。",
        "",
        "| # | 事件 | 分类 | 地区 | 代表稿 | 信源 | 转载 | 相似度 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for idx, event in enumerate(report["events"], 1):
        lines.append(
            f"| {idx} | {event['title']} | {event['category']} | {event['region']} | "
            f"{event['representative_title']} | {event['representative_source']} | "
            f"{event['member_count']} | — |"
        )
    lines += [
        "",
        "---",
        "本日报由 dedupwire 自动生成：正文抽取（Readability 式）+ MinHash/LSH 去重，"
        "代表稿按 0.5×正文长度 + 0.3×发布时间 + 0.2×信源权重 选出。",
    ]
    return "\n".join(lines) + "\n"


CSV_HEADER = ["序号", "事件标题", "分类", "地区", "代表稿标题", "信源", "发布时间", "重复篇数", "平均相似度"]


def _csv(report: dict) -> str:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    for idx, event in enumerate(report["events"], 1):
        writer.writerow(
            [
                idx,
                event["title"],
                event["category"],
                event["region"],
                event["representative_title"],
                event["representative_source"],
                event["published_at"].strftime("%Y-%m-%d %H:%M") if event["published_at"] else "",
                event["member_count"],
                "—",
            ]
        )
    return buffer.getvalue()


def report(db: Session, date_text: str) -> dict:
    data = _build(db, date_text)
    data["markdown"] = _markdown(data)
    return data


def export(db: Session, date_text: str, fmt: str) -> tuple[str, str, str]:
    data = _build(db, date_text)
    if fmt == "csv":
        return _csv(data), "text/csv; charset=utf-8", f"dedupwire-daily-{date_text}.csv"
    return _markdown(data), "text/markdown; charset=utf-8", f"dedupwire-daily-{date_text}.md"


def publish(db: Session, date_text: str, actor) -> dict:
    data = _build(db, date_text)
    audit_service.record(
        db,
        actor,
        action="daily.publish",
        target_type="daily_report",
        target_id=date_text,
        detail={"event_count": data["summary"]["event_count"], "published": True},
    )
    db.commit()
    return {"message": f"日报已发布（{date_text}）", "date": date_text,
            "event_count": data["summary"]["event_count"]}
