# 视频工作流存储生命周期治理

> 范围：项目级 `video-workflow` 参考图、生成任务下载产物和临时文件。
> 日期：2026-06-29

## 默认策略

- 单张参考图最大值：由 `VIDEO_REFERENCE_MAX_BYTES` 控制，默认 10MB。
- 单项目参考图库上限：50 张。
- 单项目参考图存储配额：由 `VIDEO_WORKFLOW_REFERENCE_QUOTA_BYTES` 控制，默认 512MB。
- 软删除保留期：由 `VIDEO_WORKFLOW_SOFT_DELETE_RETENTION_DAYS` 控制，默认 30 天。
- 失败任务保留期：由 `VIDEO_WORKFLOW_FAILED_RUN_RETENTION_DAYS` 控制，默认 30 天。
- 临时上传文件保留期：由 `VIDEO_WORKFLOW_TEMP_FILE_RETENTION_HOURS` 控制，默认 24 小时。

## 运行时行为

- 上传参考图前后都在服务端校验格式、大小和项目级存储配额。
- 删除参考图默认只写 `deleted_at`，保留 manifest 元数据，避免破坏历史任务引用。
- 软删除文件超过保留期后可物理清理；清理后写入 `purged_at`，继续保留 `asset_id`、原始路径和历史大小。
- 清理临时上传文件只处理 `video_workflow/references/.*.upload`，不扫描项目外路径。
- 下载视频产物仍保留在项目目录内，备份和恢复以整个项目目录为单位。
- 失败任务超过保留期后写入 `retention_status=expired` 和 `expired_at`，保留任务记录用于审计，不自动删除。
- 运维查询入口：`GET /projects/{project_id}/video-workflow/storage` 返回当前策略和项目存储用量。
- 手动清理入口：`POST /projects/{project_id}/video-workflow/storage/cleanup` 按当前策略清理过期软删除文件、临时上传文件并标记过期失败任务。

## 备份与恢复

- 物理清理前先备份项目目录。
- 备份应包含项目 SQLite、`video_workflow/assets.json`、参考图、视频输出和任务下载文件。
- 恢复时先恢复项目目录，再启动 API，通过 `GET /projects/{project_id}/video-workflow` 校验 manifest、用量统计和任务历史。
- SQLite/storage 当前默认按单 API 实例写入；横向多副本前必须迁移到外部数据库和对象存储，不能只复制本地目录。

## 对象存储迁移口径

- 首版文件系统仍是权威二进制存储，manifest 记录相对路径。
- 参考图元数据已同步写入项目 SQLite `video_workflow_assets` 表，`assets.json` 暂保留为兼容快照；后续完全迁移前不得删除 JSON 读写路径。
- 迁移对象存储时，manifest 应新增 `storage_backend` 和对象 key，保留现有 `asset_id`。
- CDN 或签名 URL 不得持久化到普通任务结果、manifest 或日志；只允许请求内短暂使用。

## 验收证据

- 并发上传和删除不会丢失 `assets.json` 更新。
- 上传、删除和清理参考图时，SQLite `video_workflow_assets` 元数据同步写入 `deleted_at/purged_at`。
- 超过项目参考图配额返回 `VIDEO_STORAGE_QUOTA_EXCEEDED`，并带脱敏用量信息。
- 软删除过期清理会删除本地文件、写入 `purged_at`，但不移除 manifest 历史记录。
- 失败任务过期清理会写入 `retention_status=expired`，不删除任务行。
- 工作台配置返回 `storage_lifecycle` 和 `storage_usage`，前端类型显式覆盖。
- storage/cleanup 接口返回同一策略和用量结构，便于部署后手动排障与清理验收。

## 可观测性口径

- 首版在 API 进程内维护视频工作流可观测性快照，用于本地和试运行排障。
- 项目级排障接口：`GET /projects/{project_id}/video-workflow/observability`，使用现有 protected 鉴权，只返回当前项目过滤后的脱敏快照。
- 事件必须包含 `project_id`、`run_id`、`trace_id`、状态、进度、错误码和下载字节数等标准字段。
- 指标至少覆盖 provider submit/query 次数、下载成功/失败次数、重复幂等请求次数和下载字节数。
- 快照不得包含上游原始响应、授权头、完整签名媒体地址或密钥形态字符串。
- 进入正式运维时，可将同一事件结构接入结构化日志或指标系统；接入前仍按脱敏事件作为唯一允许输出。
