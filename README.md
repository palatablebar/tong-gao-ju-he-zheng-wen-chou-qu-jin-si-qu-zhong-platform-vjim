# dedupwire · 通稿聚合正文抽取与近似去重台

> 三江传媒集团的通稿池：20 个同行站 + 8 个政务公告站的稿子汇进来，先按正文密度抽出正文，
> 再用 MinHash + LSH 找出同一事件的转载稿，编辑在并排 diff 里确认代表稿，最后按日生成事件时间轴与日报。

## 1. 真实场景

- **模拟客户**：三江传媒集团（3 报 2 网，编辑 40 人），地方媒体集团，监测 20 个同行站 + 8 个政府公告站。
- **现有工作流**：编辑每天早上手工刷 28 个站点，复制粘贴到共享文档；选题会前用肉眼比对转载稿；
  日报靠人从文档里摘。
- **三个痛点**：① 同一事件 6—9 家转载，分不清谁是首发；② 导航/评论/广告混入正文，正则截断经常误伤；
  ③ 事件聚类靠人脑，遗漏高、没有时间轴。
- **上下游**：上游＝信源站点/公告；本系统替代「正文抽取 + 近似去重 + 事件时间轴」这一段；
  下游＝选题会（簇审查）、转载提醒（疑似边）、日报（Markdown/CSV 导出）。

### 角色权限

| 角色 | 账号 | 主要页面 | 权限 | 典型动作 |
|---|---|---|---|---|
| 主编 | `admin@dedupwire.io` | 全部 | 信源管理、簇合并/拆分、事件编辑、发布日报 | 新增信源、拆分簇、建事件 |
| 编辑 | `analyst@dedupwire.io` | 原文/簇/时间轴 | 校正正文、选代表稿、打事件标签；不能加删信源 | 校正正文、确认簇 |
| 只读 | `viewer@dedupwire.io` | 时间轴/日报 | 只读 + 下载日报；运行去重 **403** | 下载日报 |

密码统一 `Demo@2026`。后端按路由依赖强制校验角色（`backend/src/middlewares/auth.py` 的
`require_roles` / `require_permission`），前端只是隐藏/禁用按钮。

### 一天的工作剧本（seed 与验收剧本一致）

1. 09:10 采集 60 条抓取记录落库，48 条被算法 A 抽出正文，其中 2 条低置信（conf 0.32 / 0.21）。
2. 09:30 编辑打开「原文队列」，勾选「只看低置信」，把 `京杭运河二通道全线通航（水路）` 那一条的
   摘要行删掉后保存 → `extractor=manual`、`extract_confidence=0.9`，审计日志 +1。
3. 09:35 编辑点「运行去重」，Celery worker 跑 MinHash + LSH：48 篇 → 12 簇 + 3 条疑似边，
   重复率 75.0% = (48−12)/48。
4. 09:50 打开最大簇（7 篇转载），并排 diff 看正文差异，选发布时间最早、正文最长的代表稿 →
   簇状态 `confirmed`，印章动效落章。
5. 10:10 事件时间轴：11-08 两条、11-10 四条，点开事件看代表稿与关联簇。
6. 10:30 生成 2026-11-10 日报 → 导出 Markdown / CSV（4 条事件 = 4 行）→ 主编发布。
7. 16:00 主编拆分一个簇 → 簇数 +1、审计日志新增。

## 2. 核心功能

| 页面 | 路由 | 说明 |
|---|---|---|
| 登录 | `/login` | JWT 登录，三个演示角色 |
| 信源台账 | `/sources` | 5 个信源，权重、抽取规则状态、抓取/正文/低置信计数；主编可增改 |
| 原文队列 | `/raw-items` | 左原始 HTML 片段、右抽取正文，可合并候选片段并校正 |
| 簇审查 | `/clusters` | 12 个去重簇、并排 diff、相似度、代表稿、疑似边；主编可拆分 |
| 事件时间轴 | `/timeline` | 按日分组 + 事件侧栏（分类/地区/关联簇/代表稿） |
| 日报 | `/daily` | 后端渲染 Markdown 预览，Markdown/CSV 导出，主编发布 |

## 2.1 按信源重抽正文（batch re-extraction）

信源抽取规则升级后，旧抓取页仍停留在旧结果。信源台账每行新增「重抽」按钮，以**信源**为单位
发起一批正文重抽，批次结果在同一处给出「成功 / 失败 / 人工校正跳过」三档数量。

- **入口**：`POST /reextract/batches {"source_id": N}`（`admin` / `analyst`，`viewer` 403）；
  查询 `GET /reextract/batches?source_id=N`、`GET /reextract/batches/{id}`；
  续跑 `POST /reextract/batches/{id}/retry`。
- **幂等**：`request_key = source:{id}:rule:{签名}`，签名覆盖 `EXTRACT_SCORE_DIVISOR /
  EXTRACT_MIN_BODY_CHARS` 与信源的 `extract_rule_status`。同一规则下重复发起复用同一批次，
  不新增任务；规则变化才开新批次。同一批次重复查询/重复任务投递不会新增去重任务或簇。
- **人工校正保护**：`articles.extractor=manual` 或 `corrected_by` 非空的稿件在批次内记为
  `skipped_manual`，正文与置信度不被覆盖；会话中排队/在跑的项在人工保存时也会立即转为
  `skipped_manual`。
- **失败可见 + 断点续跑**：每条抓取记录一行 `reextract_items`（`pending / running /
  succeeded / failed / skipped_manual`），失败项落 `error_note` 并保留在批次中。批次逐项提交，
  中断后 `retry` 只重跑 `pending / failed / 中断在 running` 的项，`attempt_count` 累加，
  `cursor_raw_item_id` 记录断点；没有可续跑项时不会重复投递任务。
- **完成后再去重**：批次结束后自动发起一次 `dedup_runs`（`dedup_run_id`），复用进行中的 run；
  簇按代表稿原地更新，`confirmed/split` 状态保留。代表稿变化时优先沿用成员重叠最多的旧簇
  （cluster.id 与事件关联不变）；旧簇确被删除时，事件置空并写 `audit_logs`
  （`action=dedup.cluster_replaced`）记录去向，已有确认的簇与事件关联可追溯。
- **页面可见**：信源台账的批次面板给出三档计数、正文变化数、断点与去重 run；簇审查与日报页
  顶部展示「本批重抽」横幅（`last_reextract`），包含失败数与重新去重后的簇/疑似边数字。
- **迁移**：`backend/migrations/versions/20261112_0002_reextract.py` 只新增
  `reextract_batches` / `reextract_items` 两张表，不改旧表。

## 3. 两个核心算法（Python 真算并落库，前端不硬编码）

### 算法 A：正文密度抽取 `backend/src/services/readability.py`

- **输入**：`raw_items.raw_html`（原始页面）。
- **过程**：标准库 `html.parser` 建简化 DOM；块级节点打分
  `score = tag_base + 3×标点数 + len(text)/100 − 100×link_density − 噪声惩罚`
  （`article 8 / section 5 / main 5 / div 5 / p 3 / li −1 / form −5`，class/id 命中
  `nav|menu|footer|comment|share|ad|banner|sidebar|copyright|recommend` 记 100 惩罚）。
  取最高分节点合并兄弟、去尾部版权行。
- **输出**：`body_text`、`content_density = 正文长度 / 页面文本长度`、
  `extract_confidence = clamp(score / EXTRACT_SCORE_DIVISOR) × clamp(body_chars/600, 0.36, 1.0)`、
  `extractor ∈ {readability, fallback, manual}`。
- **失败态**：最高分正文 < 120 字 → 兜底合并全部 `<p>`，`extractor=fallback`，
  置信度压到 0.39 以下进入低置信队列（seed 里正好 2 条）。
- **可复现**：纯函数、无随机数、无网络；同一 HTML 永远同一结果。

### 算法 B：MinHash + LSH 近似去重聚类 `backend/src/services/dedup.py`

- **输入**：48 篇 `articles.body_text`（去重运行取全部有正文的稿件）。
- **过程**：正文归一化（NFKC、去空白/标点、数字→`0`）→ 中文 **4-gram shingle** 集合 →
  **MinHash 128 签名**（`hashlib.blake2b` 64bit 基哈希 + 固定 seed `20261110` 的 128 组线性置换）
  → **LSH 32 band × 4 row** 分桶 → 候选对 → **精确 Jaccard 复核**：
  - `jaccard ≥ threshold(0.72)` → 并查集合并成簇；
  - `0.55 ≤ jaccard < 0.72` 且最终不同簇 → 记「疑似边」。
- **代表稿**：`score = 0.5×正文长度归一 + 0.3×发布时间最早归一 + 0.2×信源权重`，
  同分取 article_id 小者。
- **输出（落库）**：`clusters`（topic_label / representative / member_count / mean_similarity /
  first_seen_at / status）、`cluster_members`（similarity_to_rep）、`suspected_edges`，
  以及 `dedup_runs` 结果快照（含 threshold、num_perm、bands、shingle_size、duplicate_rate、
  candidate_pair_count、snapshot_path）。
- **执行**：前端 `POST /dedup/runs` → Celery worker 执行 `dedupwire.run_dedup` →
  结果写入 `/app/var/runs/run-<id>.json`（命名卷 `app_var`）→ 前端轮询 `dedup_runs` 状态。
- **可复现**：seed 语料固定，同一份代码重跑得到同样 12 簇 / 3 疑似边；阈值可从前端请求传入重算。

## 4. 快速启动

```bash
cp .env.example .env
docker compose up -d --build          # 约 1—3 分钟，5 个服务全部 healthy
# backend 启动时自动 alembic upgrade head + seed_demo.py（SEED_DEMO=true）
open http://localhost:18236            # 前端
curl http://localhost:19236/api/health # 后端健康检查（也可 /health）
```

手动 seed（幂等，可重复执行）：

```bash
docker compose exec backend python scripts/seed_demo.py
# SEED_SUMMARY brand=dedupwire sources=5 raws=60 articles=48 clusters=12 events=6 users=3
```

> `seed_demo.py` 按自然键（email / 信源名 / url / raw_item_id / 事件标题+日期）先查后建，
> 不覆盖人工校正、簇确认与拆分结果；已存在簇时不会重建 seed 态簇。

## 5. 访问地址

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:18236 |
| 后端 API | http://localhost:19236（直连 `/health`、`/api/health`） |
| API 文档 | http://localhost:19236/docs |
| PostgreSQL | localhost:17736（`dedupwire` / `dedupwire_pw_2026`） |

## 6. 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite 5 + Pinia + Vue Router + axios；Nginx 托管 dist |
| 后端 | Python 3.11 + FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic v2 + PyJWT + Alembic |
| 异步 | Celery 5.4（worker + beat 心跳）+ Redis 7 |
| 数据库 | PostgreSQL 16 |
| 算法 | 标准库 `html.parser`、`hashlib.blake2b`、并查集、MinHash/LSH（无第三方算法库） |
| 部署 | Docker Compose，5 服务（frontend / backend / worker / db / redis），全部 healthcheck |

## 7. 目录

```
gb-563/
├── docker-compose.yml          # 5 服务、命名卷、健康检查、端口走 .env
├── .env / .env.example
├── backend/
│   ├── Dockerfile              # backend 与 worker 共用镜像（RUN_MODE 区分）
│   ├── entrypoint.sh           # alembic → seed → uvicorn / celery
│   ├── alembic.ini
│   ├── migrations/             # alembic env + 0001 初始迁移（基于 ORM metadata）
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── seed_demo.py        # 幂等 seed，打印 SEED_SUMMARY
│   │   ├── corpus.py           # 12 主题 / 48 篇通稿语料（确定性）
│   │   ├── verify_corpus.py    # 本地纯函数校验：12 簇 / 3 疑似边
│   │   └── worker_healthcheck.py
│   └── src/
│       ├── config/             # settings / database / celery_app
│       ├── constants/          # roles / enums / error_codes / messages
│       ├── models/             # user, source, raw_item, article, cluster(+member/suspect), dedup_run, reextract, event, audit_log
│       ├── schemas/            # pydantic 请求/响应
│       ├── services/           # 业务 + readability.py + dedup.py + 抽取/去重/重抽编排
│       ├── controllers/        # 路由控制器（薄层）
│       ├── routes/             # APIRouter（/api 与无前缀两套挂载）
│       ├── middlewares/        # request_context / auth(JWT+RBAC) / rate_limit
│       ├── tasks/              # Celery：dedup_task / heartbeat
│       ├── utils/              # jwt / password / textnorm / ratelimit / serializers / logger
│       └── main.py
└── frontend/
    ├── Dockerfile / nginx.conf # /api 反代 + SPA 回落
    └── src/
        ├── api/ stores/ types/ constants/ utils/ hooks/
        ├── components/common/  # AppShell / BodyDiffPanel / SimilarityMeter / StampBadge / ReextractPanel
        ├── pages/              # Login / Sources / RawItems / Clusters / Timeline / Daily
        └── router/
```

## 8. 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `dedupwire` | Compose 项目名 / 容器名前缀 |
| `FRONTEND_PORT` / `BACKEND_PORT` / `DB_PORT` | 18236 / 19236 / 17736 | 端口映射 |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | dedupwire / dedupwire / … | PostgreSQL 连接 |
| `JWT_SECRET` | 见 .env.example | JWT 签名密钥（生产必须替换） |
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker / backend + 限流 + worker 心跳 |
| `SEED_DEMO` | `true` | backend 启动时是否自动 seed |
| `EXTRACT_SCORE_DIVISOR` / `EXTRACT_MIN_BODY_CHARS` | 45 / 120 | 算法 A 置信度分母与兜底阈值 |
| `DEDUP_SIM_THRESHOLD` / `DEDUP_SUSPECT_THRESHOLD` | 0.72 / 0.55 | MinHash 判重 / 疑似边阈值 |
| `DEDUP_NUM_PERM` / `DEDUP_BANDS` / `DEDUP_SHINGLE_SIZE` | 128 / 32 / 4 | LSH 参数 |
| `DEDUP_RATE_LIMIT_PER_MINUTE` | 10 | 去重任务每用户每分钟次数 |

## 9. 共享枚举（前后端各一份，位置如下）

| 枚举组 | 后端 | 前端 |
|---|---|---|
| 角色 `admin/analyst/viewer` + 权限矩阵 | `backend/src/constants/roles.py` | `frontend/src/constants/roles.ts` |
| 业务状态：信源类型 `media/government/selfmedia`、原文状态 `new/parsed/failed`、抽取器 `readability/fallback/manual`、簇状态 `auto/confirmed/split`、去重任务状态 `queued/running/succeeded/failed`、重抽批次状态 `queued/running/succeeded/failed/partial`、重抽条目状态 `pending/running/succeeded/failed/skipped_manual`、事件分类 `政策/产业/民生/财经` | `backend/src/constants/enums.py` | `frontend/src/constants/enums.ts` |

> 前端 `constants/enums.ts` 里的 `LOW_CONFIDENCE_THRESHOLD / DEDUP_SIM_THRESHOLD /
> DEDUP_SUSPECT_THRESHOLD` 只用于展示（阈值刻度、低置信标红），判定一律以后端为准。

## 10. 本地开发（可选）

```bash
# 后端（宿主机需 PostgreSQL/Redis，或复用 compose 的 db/redis）
cd backend && pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# 前端
cd frontend && npm install --registry=https://registry.npmjs.org && npm run dev
# Vite 代理 /api → http://localhost:19236 并剥掉 /api 前缀
```

## 11. 测试产物

源码目录不放测试产物。真机测试记录、截图脚本与 1440×900 截图在
`batch-20261110d/test-artifacts/gb-563/`（`TESTING.md`、`tests/screenshots.cjs`、`screenshots/`、`logs/`）。

## 12. 已知简化

- 不真发 HTTP 抓取：seed 里的 `raw_html` 是固定页面快照；「采集」结果以 60 条抓取记录呈现。
- 事件手工创建（seed 6 条），不做自动事件抽取；事件与簇通过 `cluster_id` 关联。
- 中文近似去重用字符 4-gram 近似分词，未引入分词器。
- 中文字体回退：Playfair Display / IBM Plex Mono 由 `@fontsource` 本地打包，中文正文回退系统宋体。

## License

内部演示项目，仅用于评审，未授权不得外传。
