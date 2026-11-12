from datetime import datetime

from pydantic import BaseModel, Field


class ConfirmClusterRequest(BaseModel):
    representative_article_id: int


class SplitClusterRequest(BaseModel):
    article_ids: list[int] = Field(min_length=1)


class MergeClusterRequest(BaseModel):
    source_cluster_id: int
    target_cluster_id: int


class ClusterMemberOut(BaseModel):
    article_id: int
    title: str
    source_name: str
    source_id: int
    published_at: datetime
    word_count: int
    similarity_to_rep: float
    is_representative: bool
    extractor: str
    body_text: str
    url: str


class SuspectEdgeOut(BaseModel):
    article_a_id: int
    article_b_id: int
    similarity: float
    title_a: str
    title_b: str


class ClusterOut(BaseModel):
    id: int
    topic_label: str
    member_count: int
    mean_similarity: float
    first_seen_at: datetime | None = None
    status: str
    status_label: str
    representative_title: str = ""
    representative_source: str = ""


class ClusterDetailOut(ClusterOut):
    members: list[ClusterMemberOut] = []
    suspect_edges: list[SuspectEdgeOut] = []
