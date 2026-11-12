"""Route modules mounted by src.main."""
from src.routes import (
    articles,
    audit,
    auth,
    clusters,
    daily,
    dedup,
    events,
    health,
    overview,
    raw_items,
    reextract,
    sources,
)

ROUTERS = [
    health.router,
    auth.router,
    overview.router,
    sources.router,
    raw_items.router,
    articles.router,
    clusters.router,
    dedup.router,
    reextract.router,
    events.router,
    daily.router,
    audit.router,
]
