"""算法 A：正文密度抽取（Readability 式，纯标准库 html.parser）。

输入：一个原始页面 HTML（RawItem.raw_html）。
输出：``Extraction`` 数据类 —— body_text / blocks / content_density /
extract_confidence / extractor / top_score / candidates。

打分口径（与 batch-plan 一致，可按 settings 调整）::

    score(node) = tag_base + 3 * punctuation_count + len(text) / 100
                  - 100 * link_density - noise_penalty

    tag_base: article 8 / section 5 / main 5 / div 5 / p 3 / li -1 / form -5
              nav -8 / footer -8 / aside -5 / header -3
    link_density: 节点内 <a> 文本长度 / 节点文本长度
    noise_penalty: class|id 命中 nav|menu|footer|comment|share|ad|banner|
                   sidebar|copyright|recommend 时记 100

置信度：``clamp(top_score / EXTRACT_SCORE_DIVISOR) * length_factor``，其中
``length_factor = clamp(body_chars / 600, 0.36, 1.0)``。正文 < 120 字时走兜底
（合并全部 <p>），extractor=fallback，并把置信度压到 0.39 以下进入低置信队列。

确定性：不依赖随机数、不依赖网络，同一 HTML 永远得到同一结果。
"""
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

# 算法的默认口径；运行时由 extraction_service 用 settings 覆盖，便于本地纯函数校验。
DEFAULT_SCORE_DIVISOR = 45.0
DEFAULT_MIN_BODY_CHARS = 120

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
BLOCK_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote",
    "figcaption", "td", "article", "section", "div", "main",
}
TAG_BASE = {
    "article": 8.0, "section": 5.0, "main": 5.0, "div": 5.0, "p": 3.0,
    "li": -1.0, "form": -5.0, "nav": -8.0, "footer": -8.0, "aside": -5.0,
    "header": -3.0, "h1": 2.0, "h2": 2.0, "h3": 2.0, "blockquote": 3.0,
}
NOISE_RE = re.compile(
    r"(nav|menu|footer|comment|share|advert|banner|sidebar|copyright|recommend|\bad\b|\bads\b)",
    re.IGNORECASE,
)
PUNCT_RE = re.compile(r"[\u3000-\u303f\uff00-\uffef!-/:-@\[-`{-~，。、；：？！“”‘’（）《》【】…—·]")
COPYRIGHT_RE = re.compile(
    r"(版权所有|未经授权|责任编辑|本文转载|来源[:：]|分享到|版权声明|点击查看|扫码关注|返回顶部)"
)
TAIL_JUNK = ("（完）", "（本文完）", "【完】")


@dataclass
class Node:
    tag: str
    attrs: dict
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)

    @property
    def classes(self) -> str:
        raw = " ".join(
            str(self.attrs.get(key, "")) for key in ("class", "id", "role", "data-type")
        )
        return raw

    def own_text(self) -> str:
        return " ".join(part for part in self.texts if part.strip())

    def full_text(self) -> str:
        chunks = [self.own_text()]
        for child in self.children:
            chunks.append(child.full_text())
        return " ".join(chunk for chunk in chunks if chunk)

    def iter_nodes(self):
        yield self
        for child in self.children:
            yield from child.iter_nodes()


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.stack: list[Node] = [self.root]

    def handle_starttag(self, tag, attrs):  # noqa: ANN001
        node = Node(tag.lower(), dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):  # noqa: ANN001
        node = Node(tag.lower(), dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):  # noqa: ANN001
        tag = tag.lower()
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == tag:
                del self.stack[idx:]
                return

    def handle_data(self, data):  # noqa: ANN001
        if data:
            self.stack[-1].texts.append(data)


def _clean_ws(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v\u00a0]+", " ", text or "")
    return re.sub(r"\n{2,}", "\n", text).strip()


def _link_text_len(node: Node) -> int:
    total = 0
    for sub in node.iter_nodes():
        if sub.tag == "a":
            total += len(sub.full_text())
    return total


def _noise_penalty(node: Node) -> float:
    if node.tag in ("nav", "footer"):
        return 100.0
    return 100.0 if NOISE_RE.search(node.classes or "") else 0.0


def _score(node: Node) -> float:
    text = node.full_text()
    if not text.strip():
        return 0.0
    chars = len(text)
    punct = len(PUNCT_RE.findall(text))
    link_density = _link_text_len(node) / max(1, chars)
    base = TAG_BASE.get(node.tag, 2.0)
    return (
        base
        + 3.0 * punct
        + chars / 100.0
        - 100.0 * min(1.0, link_density)
        - _noise_penalty(node)
    )


def _block_texts(node: Node) -> list[str]:
    """Collect paragraph-like texts in document order."""
    out: list[str] = []

    def walk(current: Node) -> None:
        if current.tag in ("script", "style", "noscript"):
            return
        has_block_child = any(child.tag in BLOCK_TAGS for child in current.children)
        if current.tag in BLOCK_TAGS and not has_block_child:
            text = _clean_ws(current.full_text())
            if text:
                out.append(text)
            return
        for child in current.children:
            walk(child)

    for child in node.children:
        walk(child)
    return out


def _strip_tail(blocks: list[str]) -> list[str]:
    cleaned = []
    for text in blocks:
        if COPYRIGHT_RE.search(text) and len(text) < 120:
            continue
        for junk in TAIL_JUNK:
            if text.endswith(junk):
                text = text[: -len(junk)].strip()
        if text:
            cleaned.append(text)
    return cleaned


def _punct_count(text: str) -> int:
    return len(PUNCT_RE.findall(text))


@dataclass
class Candidate:
    block_id: str
    text: str
    score: float
    tag: str


@dataclass
class Extraction:
    body_text: str
    blocks: list[str]
    content_density: float
    extract_confidence: float
    extractor: str
    top_score: float
    page_chars: int
    candidates: list[Candidate]

    @property
    def body_chars(self) -> int:
        return len(self.body_text.replace("\n", ""))


def extract(
    html: str,
    score_divisor: float | None = None,
    min_body_chars: int | None = None,
) -> Extraction:
    score_divisor = score_divisor or DEFAULT_SCORE_DIVISOR
    min_body_chars = min_body_chars or DEFAULT_MIN_BODY_CHARS
    html = html or ""
    builder = _TreeBuilder()
    try:
        builder.feed(html)
        builder.close()
    except Exception:  # noqa: BLE001 - malformed HTML still gets a best effort
        pass
    root = builder.root
    page_text = _clean_ws(root.full_text())
    page_chars = len(page_text.replace(" ", ""))

    scored: list[tuple[float, Node]] = []
    for node in root.iter_nodes():
        if node.tag in BLOCK_TAGS or node.tag in ("nav", "footer", "aside", "header", "form"):
            scored.append((_score(node), node))
    scored.sort(key=lambda item: item[0], reverse=True)
    top_score, top_node = (scored[0][0], scored[0][1]) if scored else (0.0, root)

    # 候选正文片段：高分段落的正文块，按文档顺序给出，供人工校正时合并。
    ordered_nodes = [node for node in root.iter_nodes()]
    candidate_blocks: list[Candidate] = []
    top_nodes = [node for score, node in scored[:12] if score > 0]
    for idx, node in enumerate(top_nodes):
        text = _clean_ws(node.full_text())
        if len(text) < 24:
            continue
        candidate_blocks.append(
            Candidate(block_id=f"c{idx + 1}", text=text, score=round(_score(node), 2), tag=node.tag)
        )
        if len(candidate_blocks) >= 8:
            break

    blocks = _strip_tail(_block_texts(top_node))
    body = "\n".join(blocks)
    body_chars = len(body.replace("\n", ""))

    density = round(min(1.0, body_chars / page_chars), 4) if page_chars else 0.0
    length_factor = max(0.36, min(1.0, body_chars / 600.0))
    score_norm = max(0.0, min(1.0, top_score / score_divisor))
    confidence = round(min(1.0, score_norm * length_factor), 2)
    extractor = "readability"

    if body_chars < min_body_chars:
        # 失败态：正文过短 → 兜底合并全部 <p>，置信度压到低置信阈值以下。
        fallback_blocks: list[str] = []
        for node in ordered_nodes:
            if node.tag == "p":
                text = _clean_ws(node.full_text())
                if len(text) >= 20 and not COPYRIGHT_RE.search(text):
                    fallback_blocks.append(text)
        if fallback_blocks:
            blocks = _strip_tail(fallback_blocks)
            body = "\n".join(blocks)
            body_chars = len(body.replace("\n", ""))
            density = round(min(1.0, body_chars / page_chars), 4) if page_chars else 0.0
            length_factor = max(0.36, min(1.0, body_chars / 600.0))
            confidence = round(min(0.39, score_norm * length_factor), 2)
        extractor = "fallback"

    return Extraction(
        body_text=body,
        blocks=blocks,
        content_density=density,
        extract_confidence=confidence,
        extractor=extractor,
        top_score=round(top_score, 2),
        page_chars=page_chars,
        candidates=candidate_blocks,
    )
