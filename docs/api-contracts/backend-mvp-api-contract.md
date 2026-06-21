# ShanHaiEdu Backend MVP API Contract

日期：2026-06-20

适用范围：前端接入项目列表、创建项目、manifest、教材上传、节点生成/编辑/确认、任务查询。

## Base URL

本地默认：

```text
http://localhost:8000
```

## Authentication

MVP 采用服务端最小鉴权边界：

- 未配置 `BACKEND_API_TOKEN`：本地开发/联调模式，项目接口开放。
- 已配置 `BACKEND_API_TOKEN`：所有项目、节点、任务、资产、schema 接口必须带请求头。

```http
Authorization: Bearer <BACKEND_API_TOKEN>
```

公开接口：

- `GET /health`
- `GET /workflow`
- `GET /video/capabilities`

受保护接口：

- `GET /schemas/{schema_name}`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/manifest`
- `POST /projects/{project_id}/textbook`
- `POST /projects/{project_id}/nodes/{node_id}/generate`
- `POST /projects/{project_id}/nodes/{node_id}/edit`
- `POST /projects/{project_id}/nodes/{node_id}/approve`
- `POST /projects/{project_id}/nodes/{node_id}/retry`
- `GET /projects/{project_id}/nodes/{node_id}`
- `GET /projects/{project_id}/nodes/{node_id}/versions`
- `GET /projects/{project_id}/tasks`
- `GET /projects/{project_id}/tasks/{task_id}`
- `POST /projects/{project_id}/tasks/{task_id}/retry`
- `GET /projects/{project_id}/assets`
- `GET /projects/{project_id}/assets/{asset_id}`

## CORS

CORS 来源由后端环境变量控制：

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

生产或共享网络环境禁止使用 `*`。

## Response Envelope

成功：

```json
{
  "ok": true,
  "data": {}
}
```

失败：

```json
{
  "ok": false,
  "error": {
    "code": "REQUEST_VALIDATION_FAILED",
    "message": "请求参数不符合接口契约",
    "retryable": false,
    "details": []
  }
}
```

`details` 只在请求体验证失败等场景返回。

## Error Codes

| HTTP | code | 含义 |
|---|---|---|
| 401 | `UNAUTHORIZED` | 配置了 `BACKEND_API_TOKEN`，但请求未携带 Bearer token |
| 403 | `FORBIDDEN` | Bearer token 不匹配 |
| 404 | `PROJECT_NOT_FOUND` | 项目不存在 |
| 404 | `NOT_FOUND` | 节点、任务或资产不存在 |
| 404 | `SCHEMA_NOT_FOUND` | schema 不存在 |
| 409 | `UPSTREAM_NOT_APPROVED` | 上游节点未 approve，禁止生成下游 |
| 409 | `NODE_NOT_READY` | 节点当前状态不允许 approve |
| 422 | `REQUEST_VALIDATION_FAILED` | 请求体不符合 Pydantic 契约 |
| 400 | `GENERATION_INPUT_INVALID` | 生成输入不符合业务约束 |
| 502 | provider-specific code | 外部 provider 请求失败 |

## Status Enum

节点状态：

```text
not_started
running
needs_review
approved
failed
blocked
skipped
```

任务状态：

```text
queued
processing
running
generated
completed
failed
```

当前可通过的上游状态：

```text
approved
skipped
```

## Create Project

```http
POST /projects
Content-Type: application/json
```

Request:

```json
{
  "name": "三年级分数导入视频",
  "subject": "math",
  "grade": "3",
  "textbook_version": "renjiao",
  "volume": "xia",
  "lesson_type": "public"
}
```

Response `data`:

```json
{
  "project_id": "proj_xxx",
  "name": "三年级分数导入视频",
  "subject": "math",
  "grade": "3",
  "textbook_version": "renjiao",
  "volume": "xia",
  "lesson_type": "public",
  "status": "active",
  "project_dir": "storage/projects/..."
}
```

## List Projects

```http
GET /projects
```

Response `data`:

```json
[
  {
    "project_id": "proj_xxx",
    "name": "三年级分数导入视频",
    "created_at": "2026-06-20T00:00:00+00:00",
    "status": "active"
  }
]
```

## Project Manifest

```http
GET /projects/{project_id}/manifest
```

Response `data`:

```json
{
  "project": {
    "project_id": "proj_xxx",
    "name": "三年级分数导入视频"
  },
  "nodes": [
    {
      "project_id": "proj_xxx",
      "node_id": "textbook_parse",
      "status": "not_started",
      "current_version_id": null,
      "updated_at": "2026-06-20T00:00:00+00:00"
    }
  ]
}
```

## Upload Textbook

```http
POST /projects/{project_id}/textbook
Content-Type: multipart/form-data
```

Form field:

```text
file=<txt/md/pdf file>
```

Response `data`:

```json
{
  "asset_id": "asset_xxx",
  "kind": "textbook",
  "path": "uploads/textbook.txt",
  "mime_type": "text/plain",
  "filename": "textbook.txt",
  "status": "uploaded"
}
```

MVP 当前支持 `.txt`、`.md`、`.pdf`。PDF 本地演示红线 fixture：

```text
fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf
```

## Generate Node

```http
POST /projects/{project_id}/nodes/{node_id}/generate
Content-Type: application/json
```

Request body is optional. For `final_video`:

```json
{
  "model": "omni_flash-10s",
  "size": "1280x720",
  "mode": "reference",
  "full_run": false
}
```

For text nodes, send `{}` or no body.

For `textbook_parse`, frontend may pass a selected knowledge point id:

```json
{
  "knowledge_point_id": "kp_001"
}
```

If omitted, backend uses the default detected knowledge point for the current demo fixture.

Rule:

- If any runtime dependency is not `approved` or `skipped`, backend returns `409 UPSTREAM_NOT_APPROVED`.

## Textbook Parse Content

`POST /projects/{project_id}/nodes/textbook_parse/generate` writes the node version and returns:

```json
{
  "version_id": "ver_xxx",
  "node_id": "textbook_parse",
  "status": "needs_review",
  "content": {
    "subject": "math",
    "grade": "1",
    "textbook_version": "renjiao",
    "volume": "shang",
    "lesson_title": "5以内数的认识",
    "core_knowledge_points": ["5以内数的认识"],
    "textbook_meta": {
      "subject": "math",
      "grade": "1",
      "textbook_version": "renjiao",
      "volume": "shang",
      "title": "人教版小学数学一年级上册"
    },
    "knowledge_points": [
      {
        "id": "kp_001",
        "title": "5以内数的认识",
        "unit": "5以内数的认识和加、减法",
        "page_start": 14,
        "page_end": 23,
        "pdf_page_start": 19,
        "pdf_page_end": 28,
        "keywords": ["1-5", "比大小", "第几", "分与合"]
      }
    ],
    "selected_knowledge_point_id": "kp_001",
    "selected_knowledge_point": {
      "knowledge_point_id": "kp_001",
      "title": "5以内数的认识",
      "source_pages": {
        "textbook_pages": "14-23",
        "pdf_pages": "19-28"
      },
      "markdown_path": "knowledge-points/kp_001.md",
      "markdown": "# 《5以内数的认识》图文教材结构化整理\n..."
    },
    "parse_artifacts": {
      "outline_path": "assets/textbook_parse/textbook_outline.json",
      "markdown_path": "knowledge-points/kp_001.md"
    }
  }
}
```

Frontend can use `textbook_meta` for automatic field backfill, `knowledge_points` for the selector, and `selected_knowledge_point.markdown` for Markdown preview.

## Lesson Plan Markdown Input

After `textbook_parse` is approved, `lesson_plan/generate` prioritizes `textbook_parse.selected_knowledge_point.markdown`.

Response `content` keeps existing demo fields and adds:

```json
{
  "source_knowledge_point_id": "kp_001",
  "source_markdown_path": "knowledge-points/kp_001.md",
  "lesson_plan_markdown": "# 《5以内数的认识》公开课教案\n..."
}
```

## Edit Node

```http
POST /projects/{project_id}/nodes/{node_id}/edit
Content-Type: application/json
```

Request:

```json
{
  "content": {
    "field": "value"
  }
}
```

Response `data`:

```json
{
  "version_id": "ver_xxx",
  "node_id": "lesson_plan",
  "status": "needs_review",
  "content": {}
}
```

## Approve Node

```http
POST /projects/{project_id}/nodes/{node_id}/approve
Content-Type: application/json
```

Request body optional:

```json
{
  "approve_note": "确认可进入下一步"
}
```

Response `data`:

```json
{
  "node_id": "lesson_plan",
  "status": "approved"
}
```

## Task Query

```http
GET /projects/{project_id}/tasks
GET /projects/{project_id}/tasks/{task_id}
```

Response task shape:

```json
{
  "task_id": "task_xxx",
  "project_id": "proj_xxx",
  "node_id": "final_video",
  "task_type": "video_clip_generation",
  "status": "completed",
  "payload": {},
  "result": {},
  "error_message": null
}
```

Note:

- 章鱼哥任务查询由后端 provider 携带服务端 token。
- 前端不得传入或保存 provider key。

## Runtime Workflow Source

Runtime node ids and dependencies are now derived from `workflow/workflow.yaml` when possible.

Temporary bridge:

- `textbook_parse` is still a backend bridge node because current `workflow.yaml` starts from `lesson_plan` and does not yet model textbook upload/parse.
- Runtime dependency override: `lesson_plan -> textbook_parse`.

This bridge should be removed after `workflow.yaml` formally adds textbook upload/parse nodes.
