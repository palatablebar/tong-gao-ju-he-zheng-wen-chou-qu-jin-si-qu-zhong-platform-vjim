"""事件时间轴：按日分组，事件可关联一个去重簇（代表稿随簇更新）。"""
from collections import OrderedDict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.enums import EVENT_CATEGORY_VALUES
from src.models import Cluster, Event
from src.services import audit_service
from src.utils.errors import not_found
from src.utils.serializers import event_out


def _clusters(db: Session) -> dict[int, Cluster]:
    return {row.id: row for row in db.scalars(select(Cluster)).all()}


def list_timeline(db: Session, category: str | None = None, date_from: str | None = None,
                  date_to: str | None = None) -> dict:
    query = select(Event)
    if category:
        query = query.where(Event.category == category)
    if date_from:
        query = query.where(Event.event_date >= date.fromisoformat(date_from))
    if date_to:
        query = query.where(Event.event_date <= date.fromisoformat(date_to))
    rows = db.scalars(query.order_by(Event.event_date.desc(), Event.id)).all()
    clusters = _clusters(db)
    grouped: "OrderedDict[str, list]" = OrderedDict()
    for event in rows:
        key = event.event_date.isoformat()
        grouped.setdefault(key, []).append(event_out(event, clusters.get(event.cluster_id)))
    days = [{"date": key, "events": value} for key, value in grouped.items()]
    return {
        "days": days,
        "total": len(rows),
        "categories": EVENT_CATEGORY_VALUES,
    }


def create_event(db: Session, payload, actor) -> dict:
    cluster = db.get(Cluster, payload.cluster_id) if payload.cluster_id else None
    event = Event(
        title=payload.title,
        category=payload.category,
        event_date=payload.event_date,
        region=payload.region,
        note=payload.note,
        cluster_id=cluster.id if cluster else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    audit_service.record(
        db, actor, action="event.create", target_type="event", target_id=event.id,
        detail={"title": event.title, "category": event.category},
    )
    db.commit()
    return event_out(event, cluster)


def update_event(db: Session, event_id: int, payload, actor) -> dict:
    event = db.get(Event, event_id)
    if event is None:
        raise not_found("event", event_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    audit_service.record(
        db, actor, action="event.update", target_type="event", target_id=event.id, detail=data,
    )
    db.commit()
    return event_out(event, db.get(Cluster, event.cluster_id) if event.cluster_id else None)
