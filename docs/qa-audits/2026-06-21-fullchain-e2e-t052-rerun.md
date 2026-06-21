# T052 全链路轻量 E2E 复测报告

日期：2026-06-21  
角色：测试工程师  
结论：通过  
验收口径：真实 DeepSeek 文本链路 + placeholder MP4 视频链路，本地轻量 E2E，不做上线验收。

## 环境

- API：`http://127.0.0.1:8152`
- Web：`http://127.0.0.1:3152`
- Storage：`storage-t052-fullchain-e2e`
- 文本 Provider：`PROVIDER_MODE=real`
- 视频 Provider：`VIDEO_PROVIDER_MODE=placeholder`
- 运行态脱敏确认：
  - `provider_mode=real`
  - `video_provider_mode=placeholder`
  - `provider_class=DeepSeekTextProvider`
  - `video_provider_is_none=True`
- Web：真实 API 模式，`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8152`
- 测试账号：`qa-t052`
- 项目：`T052全链路复测`
- 项目 ID：`proj_ef5de05702de`
- 教材 fixture：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
- 安全说明：未输出任何 DeepSeek / Octo 密钥。

## 执行结果

| 验证项 | 结果 | 证据 |
|---|---:|---|
| API `/health` | 通过 | `200`，`status=ok`，`workflow_version=1.0.0` |
| Web 启动 | 通过 | 首页 `200` |
| API 运行口径 | 通过 | `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` |
| PDF 上传 | 通过 | `POST /projects/{id}/textbook` 返回 `200` |
| 教材解析 | 通过 | `textbook_parse=approved` |
| 字段回填与手工修改 | 通过 | 初始字段 `math / 1 / renjiao / shang`，手改 marker 为 `T052 field manual edit evidence` |
| 知识点 Markdown | 通过 | `knowledge-points/kp_001.md`，内容包含“5以内数的认识” |
| lesson_plan 真实文本生成 | 通过 | `lesson_plan=approved`，Markdown 长度 `1655`，内容包含“5以内数的认识” |
| 5 个视频脚本链节点 | 通过 | `intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard` 均 approved |
| `final_video/generate` | 通过 | 返回 `200`，`status=running`，`video_path=outputs/final_video.mp4` |
| tasks 查询 | 通过 | `/tasks` 返回 6 个 `generated` task |
| MP4 下载 | 通过 | `GET /projects/{id}/outputs/final_video.mp4` 返回 `200`，`content-type=video/mp4` |
| PPT 导出 | 通过 | `POST /projects/{id}/export/ppt` 返回 `200` |
| PPT 下载 | 通过 | `GET /projects/{id}/exports/lesson-video-demo.pptx` 返回 `200` |
| PPT 内嵌 MP4 | 通过 | 存在 `ppt/media/media1.mp4` |
| PPT 内嵌 MP4 与下载 MP4 一致 | 通过 | sha256 一致 |
| 前端 MP4 下载入口 | 通过 | 最终视频页显示 `下载 MP4`，指向 `/outputs/final_video.mp4` |
| 前端 PPT 下载入口 | 通过 | 点击导出后显示 `下载 PPT`，指向 `/exports/lesson-video-demo.pptx` |
| 浏览器控制台 | 通过 | 应用级 `error/warn` 为空 |

## API 关键证据

- API 证据文件：`docs\qa-audits\t052-1782019558-api-evidence.json`
- MP4 文件：`docs\qa-audits\t052-1782019558-final_video.mp4`
- PPT 文件：`docs\qa-audits\t052-1782019558-lesson-video-demo.pptx`
- MP4：
  - content-type：`video/mp4`
  - size：`48 bytes`
  - sha256：`94be2290e8cfba6051fcfaf3ad34dba43305ea16896ce23f35ee84755b7de690`
- PPT：
  - content-type：`application/vnd.openxmlformats-officedocument.presentationml.presentation`
  - size：`35093 bytes`
  - 内嵌媒体：`ppt/media/media1.mp4`
  - 内嵌 MP4 sha256：`94be2290e8cfba6051fcfaf3ad34dba43305ea16896ce23f35ee84755b7de690`
  - 与下载 MP4 一致：`true`

## 浏览器证据

- 浏览器证据文件：`docs\qa-audits\t052-browser-evidence.json`
- 页面：真实 API 模式，项目 `T052全链路复测`
- 首页显示：
  - 当前阶段：`最终视频`
  - 总进度：`90%`
- 工作区最终视频结果页显示：
  - `演示视频文件已生成`
  - `下载 MP4`
  - `路径：outputs/final_video.mp4`
  - `交付 PPT`
  - 导出后显示 `已生成`、`lesson-video-demo.pptx`、`下载 PPT`
- 浏览器采集的 `consoleErrorWarn=[]`。

## 备注

- `t052-web.log` 中存在 Next.js dev server 的跨源开发提示，属于本地开发服务器提示；浏览器页面采集的应用级 `error/warn` 为空，不阻塞本轮本地轻量 E2E。
- 本轮不测试真实 Octo 视频 provider。
- 本轮 placeholder MP4 仅证明链路产物、下载和 PPT 嵌入可用，不代表真实视频质量。
- 本轮不做上线验收，不覆盖正式鉴权、多租户、部署、性能和真实视频质量。

## 最终结论

T052 复测【通过】。

T047 阻塞点已关闭：在 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 下，系统可从 fixture PDF 上传完整推进到 placeholder MP4 下载与 PPT 下载，且 PPT 内存在同一份 MP4 媒体文件。
