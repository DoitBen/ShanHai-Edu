# ShanHaiEdu 后端架构与安全审查记录

日期：2026-06-20

审查角色：后端开发工程师

## 结论

当前后端已能支撑本机 MVP 冒烟，但不能开放给真实用户或公网生产使用。最大问题不是 Minimax 或章鱼哥调用，而是后端缺少鉴权、权限隔离、上传边界、后台任务队列、生产部署与错误脱敏。

章鱼哥视频任务查询的关键规则已经在代码中落实：提交和查询都走服务端 provider，并由服务端携带 Authorization，不允许前端接触明文密钥。

## 紧急修复项

### 致命漏洞：全部项目与任务接口无鉴权、无用户隔离

位置：

- `apps/api/app/main.py:66`
- `apps/api/app/main.py:92`
- `apps/api/app/main.py:99`
- `apps/api/app/main.py:159`

风险影响：

任何访问者都能创建项目、上传文件、触发真实视频 API、查询任务，直接造成越权访问和费用滥用。

根本原因：

FastAPI 路由没有 `Depends()` 鉴权层，SQLite 表也没有 owner/user 字段。

完整整改代码方案：

```python
# apps/api/app/security.py
from fastapi import Header, HTTPException
import secrets

from .settings import Settings


settings = Settings.from_overrides()


def require_api_token(authorization: str | None = Header(default=None)):
    expected = settings.backend_api_token
    if not expected or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
```

落地要求：

- 所有 `/projects/**`、`/tasks/**`、`/assets/**` 路由加鉴权依赖。
- 表结构补 `owner_id`。
- 所有项目、任务、资产查询必须加 `WHERE project_id=? AND owner_id=?`。

### 严重故障：CORS 全开放且允许 credentials

位置：

- `apps/api/app/main.py:29`

风险影响：

生产环境跨站调用边界不清，配合无鉴权会放大滥用面。

根本原因：

`allow_origins=["*"]` 与 `allow_credentials=True` 是开发默认值，不适合生产。

完整整改代码方案：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

落地要求：

- `.env.example` 增加 `CORS_ORIGINS=http://localhost:3000`。
- Settings 解析逗号分隔 allowlist。

### 严重故障：文件上传无大小限制、无扩展白名单、同名覆盖

位置：

- `apps/api/app/store.py:283`

风险影响：

可能导致磁盘打满、覆盖旧教材、上传非预期文件，后续解析和运维受影响。

根本原因：

上传阶段直接 `copyfileobj` 落盘，类型校验放到了读取文本阶段。

完整整改代码方案：

```python
ALLOWED_TEXTBOOK_SUFFIXES = {".txt", ".md", ".pdf"}
MAX_TEXTBOOK_BYTES = 20 * 1024 * 1024

suffix = Path(file.filename or "").suffix.lower()
if suffix not in ALLOWED_TEXTBOOK_SUFFIXES:
    raise ValueError("unsupported file type")

written = 0
target = project_dir / "uploads" / f"textbook_{uuid.uuid4().hex}{suffix}"
with target.open("wb") as out:
    while chunk := file.file.read(1024 * 1024):
        written += len(chunk)
        if written > MAX_TEXTBOOK_BYTES:
            target.unlink(missing_ok=True)
            raise ValueError("file too large")
        out.write(chunk)
```

落地要求：

- 文件名改为服务端生成。
- 数据库记录 original_filename。
- 失败时删除临时文件。

### 严重故障：外部 API 调用同步阻塞请求线程

位置：

- `apps/api/app/services.py:143`
- `apps/api/app/services.py:185`
- `apps/api/app/providers.py:197`

风险影响：

Minimax 或章鱼哥 120 秒超时会拖住 HTTP 请求；并发时 API 服务不可用。

根本原因：

没有 worker 或队列；`GET task` 还会同步查询远程任务并下载视频。

完整整改代码方案：

```python
@app.post("/projects/{project_id}/nodes/final_video/generate")
def generate_final_video(project_id: str, payload: dict[str, Any], background_tasks: BackgroundTasks):
    task = service.create_video_task(project_id, payload)
    background_tasks.add_task(service.run_video_task, project_id, task["task_id"])
    return ok({"task_id": task["task_id"], "status": "pending"})
```

落地要求：

- `POST generate` 只创建本地任务。
- 后台 worker 负责 submit/query/download。
- `GET task` 只读本地任务状态。

### 严重故障：task retry 是假重试

位置：

- `apps/api/app/main.py:168`

风险影响：

前端显示重试成功，但没有重新提交远程任务，也没有更新数据库。

根本原因：

当前只是返回 `{**task, "status": "generated"}`。

完整整改代码方案：

```python
def retry_task(project_id: str, task_id: str) -> dict[str, Any]:
    old = store.task(project_id, task_id)
    if old["status"] not in {"failed", "completed"}:
        raise ValueError("task not retryable")
    submitted = video_provider.submit_video(build_video_payload(old["payload"]))
    return store.update_task(
        conn,
        task_id,
        submitted["status"],
        {**old["result"], **submitted},
        None,
    )
```

落地要求：

- 仅允许失败任务或下载失败任务重试。
- 重新提交 provider 并更新 provider task id。
- 已成功片段不能被无意重跑。

## 逻辑缺陷

### final_video clip 状态写死 generated

位置：

- `apps/api/app/services.py:160`

风险影响：

远程任务还在 queued/processing 时，节点内容却声明片段已生成，后续 approve/compose 会误判。

根本原因：

`clips[].status` 没有使用 task 实际状态。

整改方案：

- `clips[].status` 使用 `task["status"]`。
- 同步任务完成后反写 final_video 当前版本，或把 clip 状态统一从 `tasks` 表计算。

### 上游修改后下游 approved 不会降级

位置：

- `apps/api/app/store.py:217`
- `apps/api/app/services.py:67`

风险影响：

教案被改后，旧文稿、分镜、视频仍保持 approved，产物链路不可信。

根本原因：

`write_version()` 只更新当前节点，没有依赖图反向失效。

整改方案：

- 基于 `MVP_DEPENDENCIES` 建反向图。
- 当前节点写新版本后，把所有下游 approved 改为 needs_review。
- 所有降级写入 events。

### JSON schema 校验过浅

位置：

- `apps/api/app/providers.py:24`

风险影响：

只检查 required 字段，类型、数组长度、枚举、嵌套结构都可能错误。

根本原因：

没有使用完整 JSON Schema 校验器。

整改方案：

- 引入 `jsonschema.Draft202012Validator`。
- 所有 LLM 输出和人工 edit 内容都走同一 schema 校验。

### 最终视频交付链路未完成

位置：

- `apps/api/app/services.py:169`

风险影响：

目前只生成 clip task，没有中文男声 TTS、静音、ffmpeg 拼接、ffprobe 音频验证、完整视频 approve 硬规则。

根本原因：

MVP 后端只落到了视频任务层。

整改方案：

- 新增 `POST /nodes/final_video/compose`。
- 实现 `TTSProvider`、`VideoComposer`、`ffprobe` 验证。
- 满足 `clip_count>=6`、`zh-CN male`、`audio_verified=true` 后才能 approve。

## 数据库与一致性

### 性能优化：项目列表逐目录扫描并打开每个 SQLite

位置：

- `apps/api/app/store.py:179`

风险影响：

项目多后列表接口变慢，启动盘 IO 增大。

根本原因：

没有全局 registry DB。

整改方案：

- 新增 `storage/index.db`。
- 存储 `project_id -> project_dir -> owner_id -> created_at`。
- 项目列表直接查 index。

### 严重故障：缺少索引和迁移机制

位置：

- `apps/api/app/store.py:73`

风险影响：

数据增长后查询慢；schema 变更只能靠 `CREATE TABLE IF NOT EXISTS`，不可控。

根本原因：

没有 migration/version 表。

整改代码方案：

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_status
ON tasks(project_id, status, created_at);

CREATE INDEX IF NOT EXISTS idx_versions_project_node
ON node_versions(project_id, node_id, created_at);

CREATE INDEX IF NOT EXISTS idx_assets_project_kind
ON assets(project_id, kind, created_at);

CREATE INDEX IF NOT EXISTS idx_events_project_created
ON events(project_id, created_at);
```

### 逻辑缺陷：文件系统写入与数据库写入非原子

位置：

- `apps/api/app/store.py:288`

风险影响：

文件写入成功但 DB 写入失败会残留孤儿文件；下载视频同理。

根本原因：

跨文件系统和 SQLite 没有补偿逻辑。

整改方案：

- 先写临时文件。
- DB 成功后 rename。
- 异常时删除临时文件并写 errors。

## 安全与日志

### 严重故障：错误信息直接返回前端

位置：

- `apps/api/app/main.py:103`
- `apps/api/app/main.py:105`
- `apps/api/app/services.py:196`

风险影响：

可能泄露内部路径、上游错误细节、下载 URL 状态。

根本原因：

响应层直接 `str(exc)`。

整改方案：

- 前端只返回错误码和用户可读短句。
- 详细异常写结构化日志。
- 日志必须脱敏。

### 代码规范优化：日志缺少统一 request_id/task_id 追踪

位置：

- `apps/api/app/store.py:421`
- `apps/api/app/store.py:431`

风险影响：

故障定位靠人工翻文件，难关联一次请求。

整改方案：

- 接入 Python `logging` JSON formatter。
- 所有 provider 调用记录 `project_id/node_id/task_id/request_id/provider/status/duration_ms`。
- 密钥和 Authorization 永远过滤。

## 部署与环境

### 严重故障：后端依赖与容器部署不可复现

位置：

- `apps/api`

风险影响：

换机器、Cloud Run、CI 都无法稳定安装运行。

根本原因：

当前本地 MVP 依赖宿主 Python 环境，缺少 `requirements.txt`、`pyproject.toml`、`Dockerfile`。

整改方案：

- 新增 `pyproject.toml`，固定 `fastapi`、`uvicorn`、`pydantic`、`pyyaml`、`jsonschema`、`httpx`。
- 新增 Dockerfile。
- 健康检查拆分 `/healthz` 和 `/readyz`。

## 改造实施顺序

1. 先补鉴权、CORS allowlist、上传大小和类型限制、错误脱敏。
2. 再做后台任务 worker，把视频提交、查询、下载从 HTTP 请求线程移出去。
3. 修正 retry、clip 状态同步、上游变更下游降级。
4. 引入完整 JSON schema 校验和 edit 校验。
5. 补 index DB、迁移表、关键索引、事务补偿。
6. 实现 TTS、ffmpeg compose、ffprobe approve 硬规则。
7. 最后补 Dockerfile、依赖锁定、结构化日志、生产运行文档。

## 验证依据

- 已审查后端关键文件：`main.py`、`store.py`、`services.py`、`providers.py`、`settings.py`、`responses.py`、`workflow_config.py`、后端测试。
- 已运行：`python -m pytest apps/api/tests -q`，结果 `14 passed`。
- 测试覆盖了 MVP 正向链路、Minimax JSON 重试、章鱼哥提交/查询 Authorization、视频 URL 字段兼容。
- 尚未覆盖鉴权、上传限流、后台任务、事务回滚、生产部署。
