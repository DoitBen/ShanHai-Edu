# T064 真实生图/视频 API 稳定性加固后端交接

## 结论

T064 已完成后端加固：真实图片任务、真实视频 clip 任务都能在任务表中暴露 provider 状态、错误码、可重试标记和下载路径；失败不再黑盒；单张图和单个 clip 支持通过 task retry 重新提交；图片、clip、final_video、PPT 下载接口都限制在当前项目目录内。

## 本轮变更

- 新增 `NewApiImageProvider`，用于后端真实生图 provider 接入，默认 OpenAI 兼容 `POST /v1/images/generations` 路径。
- 新增图片 provider 配置：
  - `IMAGE_PROVIDER_MODE=real|placeholder`
  - `IMAGEGEN_MYSELF_API_KEY` / `IMAGEGEN_API_KEY` / `NEWAPI_API_KEY`
  - `IMAGEGEN_MYSELF_BASE_URL` / `IMAGEGEN_BASE_URL` / `NEWAPI_BASE_URL`
  - `IMAGEGEN_MYSELF_MODEL` / `IMAGEGEN_MODEL` / `NEWAPI_IMAGE_MODEL`
- `intro_video_asset/generate` 在配置真实图片 provider 时，会为每个 asset 创建 `image_generation` task，下载到 `assets/generated_images/{asset_id}.png`。
- `POST /projects/{project_id}/tasks/{task_id}/retry` 改为真实 retry：
  - `image_generation`：重新提交单张图并下载到原 `image_path`。
  - `video_clip_generation`：重新提交单个 clip，保留原 `clip_path`。
- 新增 `GET /projects/{project_id}/images/{filename}`，只允许下载当前项目 `assets/generated_images` 下的图片文件。
- task 顶层字段补齐：`provider_task_id`、`image_url`、`image_path`、`clip_path`、`download_status`、`error_code`、`retryable`。

## 失败口径

- 图片 provider submit/download 失败：
  - task 写入 `failed`
  - result 写入 `error_code`、`retryable`、可选 `http_status`、脱敏 `response_excerpt`
  - `intro_video_asset` 节点写入 `failed`
  - API 返回 `502` 和可读错误
- 视频 clip retry 失败：
  - task 写入 `failed`
  - errors log 写入错误码和脱敏消息
  - API 返回 `502`
- `final_video.mp4` 不存在：
  - `GET /projects/{id}/outputs/final_video.mp4` 返回 `404 / OUTPUT_NOT_FOUND`

## 下载安全

- PPT：`GET /projects/{id}/exports/{filename}` 仅允许当前项目 `exports` 下 `.pptx`。
- final_video：固定当前项目 `outputs/final_video.mp4`。
- clip：`GET /projects/{id}/clips/{filename}` 仅允许当前项目 `clips` 下 `.mp4`。
- image：`GET /projects/{id}/images/{filename}` 仅允许当前项目 `assets/generated_images` 下 `.png/.jpg/.jpeg/.webp`。
- 所有下载接口都使用 `Path(filename).name` 收窄文件名，不接受目录穿越路径。

## 验证结果

- 红灯验证：新增 T064 测试初始失败，暴露图片任务不入库、图片失败不转 failed、task retry 假返回、图片下载接口缺失。
- 目标测试：
  - `python -m pytest apps\api\tests\test_real_providers.py::test_real_image_provider_success_persists_task_and_downloadable_path apps\api\tests\test_real_providers.py::test_real_image_provider_failure_persists_failed_task_node_error_and_redacts apps\api\tests\test_real_providers.py::test_retry_image_task_resubmits_single_image_and_updates_task apps\api\tests\test_real_providers.py::test_retry_video_clip_task_resubmits_single_clip apps\api\tests\test_real_providers.py::test_download_image_returns_only_project_generated_images apps\api\tests\test_real_providers.py::test_download_final_video_returns_readable_error_when_missing -q`
  - 结果：`6 passed`
- 相关回归：
  - `python -m pytest apps\api\tests\test_real_providers.py apps\api\tests\test_video_demo_contract.py apps\api\tests\test_ppt_export.py apps\api\tests\test_fullchain_e2e_contract.py -q`
  - 结果：`46 passed`
- 后端全量：
  - `python -m pytest apps\api\tests -q`
  - 结果：`65 passed, 2 xfailed`

## 剩余风险

- 本轮使用 stub provider 做自动化契约，不再次调用真实外部 API。
- 图片 provider 当前默认接 OpenAI 兼容同步生图路径；若后续改走章鱼哥 `/v1/videos` 异步图片路线，需要新增 query/download 状态机。
- 真实视频 reference image 进入 Omni/OTU 的输入通道仍是后续质量链路缺口；新的设计口径是优先使用本地已下载图片文件 multipart 上传，而不是只把临时公网 URL 放入 JSON `images` 让 OTU 服务端拉取。
- 如果 OTU 返回 `媒体预处理失败` / 参考图 `HTTP 403 下载失败`，应归类为参考图输入通道失败；它不同于任务 completed 后本机下载 MP4 URL 失败。
- 后续实现应在 video task payload/result 中记录 `reference_submission_mode=multipart|url`、`reference_image_ids`、本地 `reference_image_paths` 和脱敏远程 URL 摘要，方便判断是图片传输、模型生成、查询还是下载阶段失败。
- 多 clip 合成仍依赖本机 `ffmpeg`，缺失时只记录可读错误，不伪造成片。
