# 视频工作台回滚演练

> 范围：项目级 Google Flow 核心视频工作台。  
> 原则：回滚入口和服务，不删除历史任务、参考图或已下载视频。

## Web 回滚

- 触发条件：正式入口渲染异常、Next 代理异常、浏览器出现阻断性错误。
- 操作：回滚 Web 服务到上一稳定版本。
- 验证：打开项目工作区，确认非视频功能正常；视频工作台入口若不可用，应显示可理解的暂停提示。
- 数据要求：不修改 FastAPI storage，不删除 `video_workflow` 目录。

## API 回滚

- 触发条件：视频工作台 API 创建任务、同步、下载或清理出现发布后回归。
- 操作前先备份当前 storage 根目录，必须包含项目 SQLite、`video_workflow/assets.json`、参考图和视频输出。
- 操作：回滚 API 服务到上一稳定版本，保持同一 storage 挂载。
- 验证：调用 `GET /projects/{project_id}/video-workflow`，确认历史素材和任务可读。

## SQLite 与 Storage 恢复

- SQLite/storage 当前按单 API 实例写入，不支持多个 API 副本同时写同一目录。
- 恢复顺序：停止 API，恢复项目目录，确认 SQLite/WAL/SHM 与媒体文件一致，再启动 API。
- 验证项：项目可列出，视频工作台可读取，已完成任务的下载文件大小大于 0。
- 物理清理前必须保留备份；软删除资产默认不立即物理删除。

## provider 故障降级

- 触发条件：Omni provider 鉴权、额度、模型权限、网络或上游稳定性异常。
- 操作：保留历史任务和素材，临时禁用新建真实任务或切回 fake/demo 验收模式。
- 用户提示：展示“视频生成服务暂不可用”，不得创建付费任务，不得用占位视频冒充真实结果。
- 排障入口：读取 `/video-workflow/observability` 的脱敏 metrics/events，并检查 provider readiness。

## 临时关闭视频工作台入口

- 适用场景：Web 入口存在严重交互问题但 API 和历史数据需要保留。
- 操作：关闭或隐藏正式入口，保留 API 查询、下载和运维排障能力。
- 验证：历史任务不丢失，素材文件仍在 storage，后续版本恢复入口后可继续读取。

## 演练完成标准

- Web 回滚后非视频主流程可用。
- API 回滚后 `GET /video-workflow` 可读历史数据。
- provider 不可用时不创建新付费任务。
- 恢复后的视频下载仍返回非空 MP4。
- 演练记录脱敏保存，禁止包含 token、完整 header、provider task id 或签名 URL。
