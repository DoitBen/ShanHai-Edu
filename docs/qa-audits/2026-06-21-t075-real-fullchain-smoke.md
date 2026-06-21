# T075 真实全链路一键 smoke 交付说明

日期：2026-06-21  
角色：后端工程师 3  
结论：一键 smoke 脚本已交付；fake/placeholder 结构闭环通过；real/real 当前阻塞在真实生图 provider，已输出可定位证据。

## 新增脚本

- `scripts\t075_real_fullchain_smoke.py`

脚本只做 HTTP 编排与证据采集，不读取、不打印真实 provider key。服务端 provider 仍由 API 进程环境变量控制；脚本参数中的 provider mode 用于记录本轮期望运行口径。

## 使用方式

fake/placeholder 结构验证：

```powershell
python scripts\t075_real_fullchain_smoke.py `
  --api-base http://127.0.0.1:8175 `
  --provider-mode fake `
  --image-provider-mode placeholder `
  --video-provider-mode placeholder `
  --storage storage-t075-fake-smoke `
  --task-timeout-sec 120 `
  --poll-interval-sec 1 `
  --allow-placeholder-media
```

real/real 验证：

```powershell
python scripts\t075_real_fullchain_smoke.py `
  --api-base http://127.0.0.1:8176 `
  --provider-mode real `
  --image-provider-mode real `
  --video-provider-mode real `
  --storage storage-t075-real-smoke `
  --task-timeout-sec 900 `
  --poll-interval-sec 15
```

默认 PDF fixture：

- `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`

## 覆盖节点

脚本逐步执行并在失败节点停止：

1. `GET /health`
2. `POST /projects`
3. `POST /projects/{project_id}/textbook`
4. `textbook_parse generate/approve`
5. `lesson_plan generate/approve`
6. `intro_selection generate/edit selected_anchor/approve`
7. `intro_video_script generate/approve`
8. `intro_video_screenplay generate/approve`
9. `intro_video_asset generate/approve`
10. `storyboard generate/approve`
11. `final_video generate`
12. `GET /projects/{project_id}/tasks/{task_id}` 轮询 video task
13. 下载 clip、`outputs/final_video.mp4`
14. `POST /export/ppt` 并下载 PPT

## 固定证据文件

每轮输出到 `docs\qa-audits\t075-real-fullchain-smoke-evidence\<timestamp>\`：

- `summary.json`
- `manifest.json`
- `tasks.json`
- `generated-image-paths.json`
- `video-task-paths.json`
- `final-artifact-paths.json`
- `provider-error-summary.json`

成功时还会下载：

- `final_video.mp4`
- `lesson-video-demo.pptx`
- 真实 clip 与真实图片会分别落入 `clips\`、`images\`

## 本轮执行证据

fake/placeholder 结构验证通过：

- 证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-175007`
- 项目 ID：`proj_add5dc2e2ca7`
- 结果：`ok=true`
- `outputs/final_video.mp4` 下载成功，48 bytes
- PPT 下载成功，35097 bytes
- PPT 内含 `ppt/media/media1.mp4`
- 说明：该轮使用 `--allow-placeholder-media`，所以真实图片和真实 clip 不作为成功门槛。

real/real 运行结果：

- 证据目录：`docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-174737`
- 项目 ID：`proj_2a6bb6bc4280`
- 失败节点：`intro_video_asset_generate`
- HTTP 状态：`502`
- 错误码：`IMAGE_RESPONSE_INVALID`
- 脱敏摘要：图片 provider 返回 HTML 页面，不是 JSON；后端已写入 `intro_video_asset=failed` 和 `image_generation` failed task。
- 未继续执行：storyboard、真实视频 clip、final_video、PPT。

## 当前判断

T075 脚本和证据闭环已完成。真实外部链路未通过不是脚本问题，而是当前真实生图 provider 响应不符合 API 预期；证据已满足“停在失败节点、输出接口、HTTP 状态、错误码、脱敏摘要”的定位要求。

后续若要解除 real/real 阻塞，应由后端/运维继续检查 `IMAGEGEN_*` 网关配置、模型路径或 provider endpoint，目标是让 `intro_video_asset/generate` 返回 JSON 图片结果并下载至少 1 张真实图片。
