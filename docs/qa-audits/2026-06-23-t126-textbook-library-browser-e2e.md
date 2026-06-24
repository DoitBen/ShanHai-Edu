# T126 教材库 / MinerU / 教案库边界收尾浏览器 E2E

## 结论

T126 通过。真实 API 模式下已覆盖教材库选择、上传 fixture PDF 入全局教材库、解析 job 轮询、知识点资产抽取与确认、教案库查询/查看/选为参考、`reference_lesson_plan_id` 持久化，以及 `lesson_plan/generate` 来源追溯。

本轮不代表真实 MinerU CLI/provider 已替换，也不代表任意教材自动泛化完成。

## 环境

- API：`http://127.0.0.1:8126`
- Web：`http://127.0.0.1:3126`
- Storage：`storage-t126-browser-e2e`
- 文本/图片/视频/TTS：fake 或 placeholder 演示模式
- 教材：fixture `fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`

## 核心证据

- 新建项目：`proj_4bd7d8ae2f59`
- 参考教案：`lp_b16b139739bb`
- 教材：`renjiao-grade1-volume1-2024`
- 教材版本：`renjiao-grade1-volume1-2024-v1`
- 知识点：`kp_001` / `5以内数的认识`
- 资产：`ta_ad7cdc33a7d2`
- 上传 job：`tj_e215896d59ca`

## 验收结果

| 场景 | 结果 | 证据 |
|---|---|---|
| 从教材库选择 fixture 教材 | 通过 | `browser-step2-summary.json`、`browser-step2-evidence.png` |
| 上传 fixture PDF 经 Web 代理入全局库 | 通过 | `upload-via-web-proxy.status.txt`、`upload-via-web-proxy.json` |
| 解析 job 轮询 | 通过 | `upload-job-via-web-proxy.json`，状态 `indexed`，provider `mineru_fixture` |
| 教材库列表来自后端 | 通过 | `textbook-library-via-web-proxy.json`，知识点数 `9` |
| PDF 页段预览 | 通过 | `slice-pdf-http-evidence.json`、`browser-pdf-dialog.png` |
| MinerU Markdown 预览 | 通过 | `browser-dialog-states.json`、`browser-markdown-dialog.png` |
| 教案库查询、查看教案抽屉 | 通过 | `browser-dialog-states.json`、`browser-lesson-drawer.png` |
| 选为参考并持久化 | 通过 | `project-after-reference-and-lesson.json` |
| 教案生成仍绑定当前教材证据包 | 通过 | 已验证输出包含当前教材、版本、知识点、PDF 页段和 MinerU Markdown 来源 |
| 浏览器 console error/warn | 通过 | `browser-step2-summary.json`、`browser-dialog-states.json` 均为空数组 |

## 本轮修复

首次经 Web 代理上传 fixture PDF 时，Next.js 代理把 `Expect` 请求头原样转给后端，Node/Undici fetch 返回 `UND_ERR_NOT_SUPPORTED`，导致 `/api/backend/textbook-library/uploads` 500。

已修复：

- `apps\web\src\app\api\backend\[...path]\route.ts` 删除转发请求中的 `expect` header。
- `apps\web\src\lib\api-proxy-contract.test.ts` 增加契约检查，防止回归。

验证：

```powershell
cd apps\web
bun src/lib/api-proxy-contract.test.ts
```

结果：退出码 0。

实际上传复测：

- HTTP 状态：`200`
- 返回：`textbook_id=renjiao-grade1-volume1-2024`，`job_id=tj_e215896d59ca`，`parse_status=uploaded`
- job 轮询：`status=indexed`

## 保守边界

- 当前 MinerU 仍为 `mineru_fixture` provider，不是真实 MinerU CLI/provider。
- 当前固定验证人教版一年级上册 fixture，不承诺任意教材自动泛化。
- 当前教材库/教案库后台管理 UI 与生产 RBAC 不在 T126 范围。
- 浏览器文件选择器未作为自动化路径单独证明；上传入库由 Web 代理 multipart HTTP 复测证明，前端 UI 文件选择仍需后续专项覆盖。
