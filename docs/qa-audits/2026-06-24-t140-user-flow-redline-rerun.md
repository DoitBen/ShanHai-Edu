# T140 用户态红线专项复测报告

## 结论

【通过】。

T139 修复后，工作区普通教师主界面在“开发诊断”之前未再出现 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage` 红线词；教材页段 PDF 入口已启用，弹窗和 iframe 地址不暴露本地 `storage` 路径，走 Web 后端代理 `/api/backend/projects/{project_id}/files/...`。

本结论只表示 T140 测试验收通过，不代表阶段封板；是否进入用户态封板仍需 T141 架构复核。

## 测试范围

- 只覆盖 T138/T139 红线复测面。
- 覆盖工作区普通教师主界面“开发诊断”之前的红线词扫描。
- 覆盖教材页段 PDF 入口是否暴露本地路径。
- 不重跑后端三段式全量主链路。
- 不测试真实 MinerU/provider、真实视频、PPT、生产权限或任意教材泛化。

## 测试环境

- API：`http://127.0.0.1:8140`
- Web：`http://127.0.0.1:3140`
- Storage：`storage-t140-user-flow-redline-rerun`
- Provider：`fake`
- Video/Image/TTS provider：`placeholder`
- Web 模式：真实 API 模式
- 测试用户：`qa-t140`
- 项目 ID：`proj_305436b48356`
- 教材 ID：`renjiao-grade1-volume1-2024`
- 知识点 ID：`kp_001`
- 证据目录：`docs\qa-audits\t140-user-flow-redline-rerun-evidence\20260624-100115`

## 执行说明

- 使用当前 worktree 状态启动隔离 API/Web。
- 通过 API 创建 T140 测试项目、挂载教材库 fixture、生成 `textbook_parse`，并用最小测试数据将 `visual_contract`、`character_dict` 前置节点确认到 approved，使前端 manifest 自然进入 `textbook_parse` 当前步骤。
- 测试数据准备只写入隔离 storage 和证据目录，未修改业务代码。

## 通过项

- API `/health` 正常。
- Web 首页 HTTP 200，真实 API 模式可登录。
- 工作区进入 `教材解析与核验` 当前任务卡。
- 普通区展示教师可读内容：
  - 课时标题：`5以内数的认识`
  - 教材页码：`教材页 14-23；PDF 页 19-28`
  - 解析状态：`已解析 / 待确认`
  - 知识点摘要：`5以内数的认识`、`1-5`、`比大小`、`第几`、`分与合`
  - 教材内容预览为 Markdown 摘要
- “开发诊断”默认折叠。
- 红线扫描结果：`main_hits_before_developer_diagnostics=[]`。
- 主界面可见区域红线扫描结果：`visible_hits_in_main=[]`。
- “查看教材页段”按钮可点击。
- 页段弹窗文本无 `storage` 或本地盘符路径。
- 页段 iframe 地址为 `/api/backend/projects/proj_305436b48356/files/knowledge-points/kp_001/source.pdf`。
- 页段 iframe 地址使用 `/api/backend/projects/.../files/...` 代理。
- 页段代理 GET 返回 `200`，`Content-Type=application/pdf`。
- 浏览器 console `error/warn` 为空。

## 缺陷清单

| 级别 | 问题 | 复现步骤 | 影响范围 | 建议处理 |
|---|---|---|---|---|
| 无 | 本轮未发现 P0/P1 阻塞 | 不适用 | 不适用 | 进入 T141 架构复核 |

## 关键证据

- 启动参数：`runtime-launch-params.json`
- API 健康检查：`api-health.json`
- 教材资产：`asset-kp001.json`
- 切分证据：`textbook-split-kp001.json`
- 解析证据：`textbook-extract-kp001.json`
- 测试项目：`project-created-api.json`
- 教材挂载：`project-attach-textbook.json`
- 教材解析生成：`textbook-parse-generate.json`
- 节点详情：`textbook-parse-node-detail.json`
- 前置测试数据准备：`prep-visual-contract-*.json`、`prep-character-dict-*.json`
- 最终 manifest：`manifest-final.json`
- API 用户态工作区：`workspace-user-flow-api-after-prep.json`
- 浏览器工作区截图：`browser-workspace-textbook-main.png`
- 浏览器红线扫描：`browser-redline-scan-main.json`
- 页段弹窗截图：`browser-textbook-slice-dialog.png`
- 页段入口扫描：`browser-pdf-entry-scan.json`
- 页段代理 GET：`pdf-proxy-get.json`
- 浏览器控制台：`browser-console.json`

说明：`pdf-proxy-head.json` 记录到该代理路由对 HEAD 返回 405；浏览器 iframe 使用 GET，已由 `pdf-proxy-get.json` 验证返回 200。

## 回归测试清单

- 工作区普通主界面在“开发诊断”之前扫描 `JSON/provider/manifest/node_id/StateEngine/schema/R010/输出路径/安全模式/storage`：通过。
- “开发诊断”默认折叠：通过。
- 教材页段 PDF 按钮可用：通过。
- 页段弹窗不暴露本地 `storage` 路径：通过。
- 页段 iframe 使用 `/api/backend/projects/{project_id}/files/...` 代理：通过。
- 页段代理 GET 可访问 PDF：通过。
- 浏览器 console `error/warn`：通过。

## 剩余风险

- 本轮只复测 T138/T139 红线，不覆盖后端三段式全量主链路。
- 本轮只使用人教版一年级上册 fixture，不代表任意教材泛化。
- 本轮不测试真实 MinerU/provider、真实视频、PPT、生产权限或多浏览器。
- 阶段封板需 T141 对照 T138 报告、T139 代码级交接、T140 证据和关键 diff 后裁决。

## 交接给其他角色

- 建议进入 T141，由首席系统架构师做阶段复核。
- T141 复核重点：T138 P0 是否已被 T139/T140 证据关闭；是否还存在未纳入本轮红线的用户态表达风险；是否允许进入用户态封板或产品演示录屏。
