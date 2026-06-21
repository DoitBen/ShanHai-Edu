# T047 全链路冲刺验收报告

日期：2026-06-21  
角色：测试工程师  
结论：阻塞  
验收口径：真实 DeepSeek + 占位 MP4，本地完整轻量 E2E，不做上线验收。

## 环境

- API：`http://127.0.0.1:8147`
- Web：`http://127.0.0.1:3147`
- Storage：`storage-t047-fullchain-e2e`
- Provider：`PROVIDER_MODE=real`
- Web：真实 API 模式，`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8147`
- 测试账号：`qa-t047`
- 项目：`T047全链路冲刺验收`
- 项目 ID：`proj_b930449fae90`
- 教材 fixture：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
- 安全说明：未输出任何 DeepSeek key。

## 已通过范围

- API `/health` 正常：`200`，`status=ok`，`workflow_version=1.0.0`。
- Web 首屏可打开：`200`。
- PDF 上传成功：`POST /projects/{id}/textbook` 返回 `200`。
- 教材解析成功：`textbook_parse=approved`。
- 字段回填与手工修改完成：
  - 解析结果包含 `subject=math`、`textbook_version=renjiao`、`volume=shang`。
  - 通过 edit 接口写入 `qa_manual_edit_marker=T047 field manual edit evidence`。
- 知识点与 Markdown 预览数据存在：
  - `selected_markdown_path=knowledge-points/kp_001.md`
  - Markdown 内容包含“5以内数的认识”。
- 教案生成成功并确认：`lesson_plan=approved`，教案 Markdown 包含“5以内数的认识”。
- 视频脚本链 5 个节点均生成并确认：
  - `intro_selection=approved`
  - `intro_video_script=approved`
  - `intro_video_screenplay=approved`
  - `intro_video_asset=approved`
  - `storyboard=approved`
- 浏览器真实 API 模式能读取该项目，首页和工作区显示：
  - 当前阶段：`最终视频`
  - 总进度：`90%`
  - 工作区 manifest 节点数：`10`
- 浏览器控制台应用级 `error/warn`：空。

## 阻塞点

### 严重：`PROVIDER_MODE=real` 下 `final_video/generate` 未走占位 MP4，转而调用真实 Octo 视频 provider 并失败

- 分类：后端 / Provider 路由 / 演示环境配置
- 阻塞等级：阻塞演示
- 接口：`POST /projects/proj_b930449fae90/nodes/final_video/generate`
- 实际结果：
  - HTTP `502`
  - error code：`OCTO_REQUEST_FAILED`
  - message：`HTTP 503`
  - retryable：`true`
  - `final_video` 节点仍为 `not_started`
  - `/projects/{id}/tasks` 返回 0 个任务
  - `/projects/{id}/outputs/final_video.mp4` 随后返回 `404 / OUTPUT_NOT_FOUND`
- 期望结果：
  - 在“真实 DeepSeek + 占位 MP4”口径下，文本节点使用 DeepSeek。
  - `final_video/generate` 不调用真实视频 provider，必须同步产出 `outputs/final_video.mp4`。
  - `GET /projects/{id}/outputs/final_video.mp4` 返回 `200`，`content-type=video/mp4`。
  - `/tasks` 可查询到本地演示任务或至少 final_video 节点进入可展示状态。
- 影响范围：
  - T047 主链路无法完成。
  - MP4 下载验收无法在主链路中通过。
  - PPT 导出下载虽然可单独调用通过，但不属于完整主链路成功。
- 复现步骤：
  1. 启动 API：`PROVIDER_MODE=real`，`STORAGE_ROOT=storage-t047-fullchain-e2e`，端口 `8147`。
  2. 创建项目并上传 fixture PDF。
  3. 依次生成并确认 `textbook_parse`、`lesson_plan`、`intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard`。
  4. 调用 `POST /projects/{id}/nodes/final_video/generate`。
  5. 观察返回 `502 / OCTO_REQUEST_FAILED / HTTP 503`。
- 建议转交角色：后端工程师。
- 标准修复方案：
  - 拆分文本 provider 与视频 provider 的运行模式，例如保留 `PROVIDER_MODE=real` 给 DeepSeek 文本链路，同时新增 `VIDEO_PROVIDER_MODE=fake|placeholder|real`。
  - T047 本地演示默认应为 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`。
  - `final_video/generate` 在 placeholder/no-provider 模式下复用 `ensure_final_video_output()`，产出 `outputs/final_video.mp4`，不要触发 Octo。
  - 增加契约测试覆盖“真实文本 provider + 占位视频 provider”组合。

## 补充证据：PPT 导出接口单独可用

阻塞发生后，单独调用 `POST /projects/{id}/export/ppt` 通过，仅作为定位证据，不判定 T047 通过。

- `POST /projects/{id}/export/ppt`：`200`
- `GET /projects/{id}/outputs/final_video.mp4`：`200`
- MP4 content-type：`video/mp4`
- MP4 文件大小：`48 bytes`
- `GET /projects/{id}/exports/lesson-video-demo.pptx`：`200`
- PPT content-type：`application/vnd.openxmlformats-officedocument.presentationml.presentation`
- PPT 文件大小：`35100 bytes`
- PPT 内嵌媒体：`ppt/media/media1.mp4`
- PPT 内嵌 MP4 hash 与下载 MP4 hash 一致：`true`

该补充说明：`export/ppt` 会兜底创建占位 MP4 并嵌入 PPT，但 `final_video/generate` 在真实 provider 模式下没有使用同一套占位逻辑。

## 证据文件

- API 阻塞证据：`docs\qa-audits\t047-blocked-final-video-error.json`
- 阻塞前节点摘要：`docs\qa-audits\t047-preblock-node-summary.json`
- 浏览器证据：`docs\qa-audits\t047-browser-evidence.json`
- PPT 补充证据：`docs\qa-audits\t047-postblock-ppt-evidence.json`
- 补充下载 MP4：`docs\qa-audits\t047-postblock-final_video.mp4`
- 补充下载 PPT：`docs\qa-audits\t047-postblock-lesson-video-demo.pptx`
- API 服务日志：`t047-api.log`
- Web 服务日志：`t047-web.log`

说明：浏览器截图采集接口连续超时，已用浏览器 DOM 快照证据替代；DOM 证据包含“后端动作执行失败”和“HTTP 503”，控制台 `error/warn` 为空。

## 最终结论

T047 不通过，状态为【阻塞】。

阻塞角色：后端工程师。  
阻塞原因：当前后端缺少“真实 DeepSeek 文本 + 占位 MP4 视频”的独立运行模式，`PROVIDER_MODE=real` 会让 `final_video/generate` 调用真实 Octo provider，导致本地轻量 E2E 在最终视频节点失败。
