# ShanHaiEdu Backend Video Generation Demo Contract

日期：2026-06-20

适用范围：本地 fake provider 视频生成演示链路，不代表上线发布契约。

## 目标

本契约覆盖从 `lesson_plan=approved` 到 `final_video` fake 任务创建的后端最小接口行为，供前端 T024、T028、T029 和测试 T025、T030 使用。

不覆盖：

- 真实 Minimax / 章鱼哥 provider。
- 正式视频质量验收。
- 正式鉴权、多用户权限、行级隔离。
- 字段级 diff、复杂版本树、正式富编辑器。

## 统一调用规则

所有节点复用现有通用接口：

```http
POST /projects/{project_id}/nodes/{node_id}/generate
GET  /projects/{project_id}/nodes/{node_id}
POST /projects/{project_id}/nodes/{node_id}/edit
POST /projects/{project_id}/nodes/{node_id}/approve
GET  /projects/{project_id}/manifest
```

`edit` 请求体：

```json
{
  "content": {}
}
```

当前 `edit` 语义是提交完整节点内容的新人工编辑版本，后端写入新 `node_versions`，节点状态保持 `needs_review`。前端保存后应重新 `GET /nodes/{node_id}` 读取当前版本。

### `/edit` 最小校验错误

视频链节点的 `/edit` 会执行节点级最小 schema 校验。错误响应：

```json
{
  "ok": false,
  "error": {
    "code": "NODE_CONTENT_INVALID",
    "message": "节点内容不符合最小契约",
    "retryable": false,
    "details": [
      {
        "field": "selected_design_ids",
        "code": "required",
        "message": "selected_design_ids 为必填字段"
      }
    ]
  }
}
```

`details[].code` 当前可能值：

- `required`：缺少必填字段。
- `invalid_type`：字段类型明显错误。
- `empty`：必填数组为空。
- `duplicate`：ID 重复。
- `reference_not_found`：引用的上游 ID 不存在。
- `count_mismatch`：数量字段与数组长度不一致。

非对象 `content` 仍由 Pydantic 请求体验证拒绝，返回 `422 / REQUEST_VALIDATION_FAILED`。

## 视频链 `/edit` 最小必填字段

### intro_selection

必填字段：

- `selection_mode`: 非空字符串
- `selected_design_ids`: 非空字符串数组
- `primary_design_id`: 非空字符串，且必须属于 `selected_design_ids`
- `downstream_generation_mode`: 非空字符串
- `selection_reason`: 非空字符串

### intro_video_script

必填字段：

- `total_duration_sec`: 数字
- `video_type`: 非空字符串
- `anchor_to_lesson`: 非空字符串
- `narration_full_text`: 非空字符串
- `narration_word_count`: 数字
- `banned_elements`: 数组

### intro_video_screenplay

必填字段：

- `scenes`: 非空数组

每个 `scenes[]` 必填：

- `scene_id`: 非空字符串
- `duration_sec`: 数字
- `scene_description`: 非空字符串
- `narration_segment`: 非空字符串

### intro_video_asset

必填字段：

- `assets`: 非空数组

每个 `assets[]` 必填：

- `asset_id`: 非空字符串，且同节点内不能重复
- `source_prompt_id`: 非空字符串
- `storage_path`: 非空字符串
- `status`: 非空字符串

### storyboard

必填字段：

- `shots`: 非空数组

每个 `shots[]` 必填：

- `shot_id`: 非空字符串，且同节点内不能重复
- `duration_sec`: 数字
- `main_subject`: 非空字符串
- `reference_image_ids`: 非空字符串数组，且必须引用 `intro_video_asset.assets[].asset_id`
- `narration_slice`: 非空字符串
- `model_prompt`: 非空字符串

### final_video

必填字段：

- `clip_count`: 非负整数
- `clips`: 数组，长度必须等于 `clip_count`
- `model_audio_policy`: 非空字符串
- `english_audio_detected`: 布尔值

每个 `clips[]` 必填：

- `shot_id`: 非空字符串；若当前项目已有 `storyboard`，必须引用 `storyboard.shots[].shot_id`
- `api_task_id`: 非空字符串
- `download_path`: 非空字符串
- `status`: 非空字符串
- `reference_image_ids`: 非空字符串数组

## T023: intro_selection

前置条件：

- `lesson_plan=approved`

若 `lesson_plan` 未确认，调用：

```http
POST /projects/{project_id}/nodes/intro_selection/generate
```

返回：

```json
{
  "ok": false,
  "error": {
    "code": "UPSTREAM_NOT_APPROVED"
  }
}
```

成功链路：

1. `POST /nodes/intro_selection/generate`
2. `GET /nodes/intro_selection`
3. `POST /nodes/intro_selection/edit`
4. `GET /nodes/intro_selection`
5. `POST /nodes/intro_selection/approve`
6. `GET /manifest`

fake provider 输出包含：

- `selection_mode`
- `selected_design_ids`
- `primary_design_id`
- `downstream_generation_mode`
- `selection_reason`

确认后 manifest 应显示：

- `intro_selection=approved`
- `intro_video_script=not_started`

## T027: 视频生产节点

节点顺序：

```text
intro_video_script
intro_video_screenplay
intro_video_asset
storyboard
final_video
```

前置依赖：

- `intro_video_script` 依赖 `intro_selection=approved` 和 `lesson_plan=approved`
- `intro_video_screenplay` 依赖 `intro_video_script=approved`
- `intro_video_asset` 依赖 `intro_video_screenplay=approved`
- `storyboard` 依赖 `intro_video_asset=approved` 和 `intro_video_screenplay=approved`
- `final_video` 依赖 `storyboard=approved` 和 `intro_video_script=approved`

前四个视频生产节点均支持：

```http
POST /nodes/{node_id}/generate
GET  /nodes/{node_id}
POST /nodes/{node_id}/edit
POST /nodes/{node_id}/approve
```

每个节点 `generate` 成功后进入 `needs_review`，`approve` 成功后进入 `approved`。

## final_video fake 任务

请求：

```http
POST /projects/{project_id}/nodes/final_video/generate
Content-Type: application/json
```

推荐本地演示请求体：

```json
{
  "model": "veo_3_1-fast",
  "size": "1280x720",
  "mode": "reference",
  "full_run": true
}
```

fake provider 模式下返回：

```json
{
  "node_id": "final_video",
  "status": "running",
  "content": {
    "clip_count": 6,
    "clips": []
  },
  "tasks": []
}
```

本地 fake 行为：

- `final_video` 节点状态为 `running`
- 创建 6 个 `video_clip_generation` 任务
- 每个任务状态为 `generated`
- 任务 payload 保存 `model`、`size`、`mode`、`prompt`、`reference_image_ids`
- 本轮 fake 模式不下载真实 mp4，不承诺视频质量

查询任务：

```http
GET /projects/{project_id}/tasks
GET /projects/{project_id}/tasks/{task_id}
```

任务列表应返回 6 个 `final_video` 任务，状态集合为：

```text
generated
```

## 前端建议

视频生产节点前端可复用教案节点的轻量 JSON 编辑模式：

1. `generate`
2. `GET node`
3. 编辑完整 `content`
4. `edit`
5. `GET node`
6. `approve`
7. `GET manifest`

`final_video` 不需要 `approve` 才能展示 fake 任务；本地演示重点是“已创建 6 个视频生成任务并可查询”。

## 当前验证证据

- 新增后端契约测试：`apps\api\tests\test_video_demo_contract.py`
- `python -m pytest apps\api\tests\test_video_demo_contract.py -q`：`6 passed`
- `python -m pytest apps\api\tests -q`：`33 passed, 2 xfailed`
- HTTP 直连项目：`proj_57b91a8359ae`
- HTTP 直连结果：
  - `intro_selection` 在 `lesson_plan` 未 approve 时返回 `UPSTREAM_NOT_APPROVED`
  - `intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 均完成 generate/edit/approve
  - `final_video/generate` 返回 `running`
  - fake task 数量为 6
  - `/tasks` 查询状态集合为 `generated`

## 上线前风险

- `edit` 当前只校验 `content` 是对象，尚未按各节点 schema 校验字段完整性。
- `final_video` fake 任务不代表真实视频生成、下载、拼接或质量验收。
- 未配置 `BACKEND_API_TOKEN` 时接口在本地联调模式开放。
- 真实 provider、异步恢复、失败重试、成本日志和下载持久化仍需单独验收。
