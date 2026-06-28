# Google Flow 核心视频工作台功能需求规格

> 状态：已完成需求确认，待用户审阅
> 日期：2026-06-29
> 目标仓库：`DOIT-Ben/ShanHai-Edu`
> 首期入口：项目工作区
> 首期模型：`omni_flash-10s`

## 1. 文档目的

本文件定义山海教育项目首期视频工作台的完整产品需求、业务规则、接口契约、状态机、数据结构和验收标准。

开发人员或 Codex 获取本文件后，应能明确：

1. 首期必须交付什么。
2. 当前代码从哪里继续开发。
3. 哪些能力明确不进入首期。
4. 前后端如何交换数据。
5. 怎样证明功能真正完成，而不是只完成界面。

第二份配套文档将给出逐文件、逐测试、逐提交的实施计划。本文件是需求和设计真源，实施计划不得改变本文件的功能边界。

## 2. 背景与目标

当前仓库已经具备视频生成的基础链路：

- 项目级接口位于 `apps/api/app/video_workflow.py`。
- 第三方视频适配位于 `apps/api/app/providers.py` 的 `OctoVideoProvider`。
- 项目级前端位于 `apps/web/src/components/video-workflow/VideoWorkflowCanvas.tsx`。
- 后台媒体测试页位于 `apps/web/src/components/screens/AdminMediaWorkbenchScreen.tsx`。
- 模型能力配置位于 `docs/api-research/octo-video/capabilities.json`。

现有链路可以上传参考图、提交任务、手动同步和下载视频，但仍是技术 MVP：

- 项目视频页仍以展示性 ReactFlow 画布为主体。
- 参考图仅显示文件名，缺少缩略图、排序、删除和明确选择状态。
- 只返回最近任务，缺少完整任务历史。
- 任务需要手动同步。
- 完成结果不能在页面内直接播放。
- 缺少幂等、完整上传校验、错误分类和真实端到端验收。
- 项目级视频工作流与后台媒体工作台存在重复实现。

首期目标不是复制 Google Flow 的全部能力，而是复制其最核心、最常用的单段视频生成闭环：

> 在一个项目内管理参考图片，选取并排序最多 7 张图片，输入提示词，通过 Omni 生成 10 秒视频，自动显示进度，直接预览、下载、重试，并能复用历史任务参数。

## 3. 对标基准与接口依据

### 3.1 Google Flow 对标范围

Google Flow 官方资料说明其视频工作台支持从文本、Ingredients/References、帧和其他视频创建视频，并提供项目素材、任务历史和结果继续使用能力：

- [Google Flow 创建视频](https://support.google.com/flow/answer/16353334?co=GENIE.Platform%3DDesktop&hl=en)
- [Google Flow 模型与功能](https://support.google.com/flow/answer/16352836?hl=en)
- [Google Flow 视频编辑与场景构建](https://support.google.com/labs/answer/16935718?hl=en)

本期只对标以下能力：

- 项目内参考素材管理。
- 多参考图作为 Ingredients。
- 文本提示词生成视频。
- 异步任务进度。
- 项目内历史结果。
- 页面内预览、下载、失败重试。
- 从历史任务恢复提示词和参考图组合。

本期不对标 Google Flow 的 Agent、视频编辑、首尾帧、语音参考、多结果批量生成、视频延长和 Scenebuilder。

### 3.2 第三方 Omni 接口依据

仓库能力文件和第三方文档是实现依据：

- [章鱼哥 API 索引](https://6l0ket291i.apifox.cn/llms.txt)
- `docs/api-research/octo-video/capabilities.json`

首期必须遵守以下已确认约束：

| 项目 | 固定值或规则 |
|---|---|
| 模型 | `omni_flash-10s` |
| 请求端点 | `POST /v1/videos` |
| 查询端点 | `GET /v1/videos/{task_id}` |
| 鉴权 | `Authorization: Bearer <server-side key>` |
| 参考图上限 | 7 |
| 输出时长 | 10 秒 |
| 输出尺寸 | `1280x720` |
| 本地图片传输 | `multipart/form-data` |
| 参考图字段 | 对每个文件重复使用 `input_reference` |
| 文生视频 | JSON 请求，不发送参考图字段 |
| 图生视频 | multipart 请求，不同时发送 `images` |
| 任务模式 | 异步，需轮询查询接口 |

接口能力文件声明 Omni 支持视频编辑，但视频编辑不进入首期。

## 4. 用户与使用场景

### 4.1 目标用户

- 内部教研员。
- 课件视频制作人员。
- 项目管理员在排查接口时可查看任务，但后台媒体页不是正式创作入口。

### 4.2 核心场景

教研员进入某个课题项目的视频工作区，上传人物、场景、道具或风格参考图，选择其中最多 7 张并调整顺序，输入对画面主体、动作、环境、镜头和风格的描述，提交生成。系统自动跟踪任务并在完成后直接播放视频。教研员可以下载结果，或者从某条历史任务恢复参数并再次生成。

### 4.3 成功定义

首期成功不是“接口返回任务 ID”，而是用户无需离开项目工作区即可完成：

`管理素材 → 配置输入 → 提交 → 自动等待 → 预览 → 下载/重试/复用`

## 5. 产品边界

### 5.1 首期必须交付

1. 项目级三栏视频工作台。
2. 项目级图片素材上传、缩略图、选择、排序、移除。
3. 0 到 7 张参考图生成。
4. 提示词输入和校验。
5. 固定 Omni 参数提交。
6. 创建请求幂等。
7. 任务列表和状态自动同步。
8. 完成视频自动保存、页面播放和下载。
9. 失败原因、重试和历史参数复用。
10. 重启恢复、项目隔离和测试覆盖。

### 5.2 首期明确不做

- 视频上传和视频到视频编辑。
- 首帧、尾帧模式。
- 音频、声音、Avatar 或角色引用语法。
- `@素材名` 提示词绑定。
- 一次生成多个候选视频。
- 视频延长、局部修改、Remix。
- 多镜头时间线、裁剪、拼接和 Scenebuilder。
- Prompt Agent 或自动改写提示词。
- 费用计量、套餐、积分和支付。
- Celery/Redis 后台队列。
- 对外 SaaS 多租户存储改造。

这些能力只能在首期验收通过后另立需求，不得在本期顺手加入。

## 6. 信息架构与页面布局

正式入口位于具体项目工作区的视频步骤。后台媒体工作台只保留为管理员接口诊断工具。

### 6.1 桌面端

采用 Google Flow 风格三栏布局：

| 区域 | 建议宽度 | 职责 |
|---|---:|---|
| 左栏：项目素材 | 240-280px | 上传、浏览、选择、排序和移除参考图 |
| 中栏：创作与预览 | 自适应 | 视频播放器、提示词、固定参数和生成按钮 |
| 右栏：任务历史 | 300-340px | 任务进度、状态、结果切换、重试和复用 |

页面不得继续把 ReactFlow 节点画布作为主要交互。首期工作流是固定业务流程，拖动节点不能改变后端执行，因此节点画布会误导用户。

### 6.2 移动端

小于桌面断点时切换为三个标签页：

- 素材。
- 创作。
- 历史。

生成按钮和提示词区域不能被固定元素遮挡。视频播放器保持 16:9。

### 6.3 空状态

- 无素材：显示上传入口，但文生视频仍可使用。
- 无任务：中央显示 16:9 占位，右栏说明尚无任务。
- 无已完成结果：中央显示当前运行任务的状态和进度。
- Provider 未配置：禁用生成按钮，显示“视频生成服务未连接”，不显示虚假成功。

## 7. 详细功能需求

### 7.1 项目素材

#### FR-ASSET-01 上传

- 支持 `.jpg`、`.jpeg`、`.png`、`.webp`。
- 支持一次选择多张。
- 单张默认最大 10MB。
- 单项目最多保存 50 张未删除图片素材。
- 上传时必须读取真实图片内容并取得宽高。
- 不能只依赖扩展名或浏览器传入的 MIME。
- 文件名必须安全化，不能影响本地路径。
- 上传中显示逐文件状态。
- 部分文件失败时，成功文件保留，并逐项显示失败原因。

#### FR-ASSET-02 浏览

每张素材卡必须显示：

- 缩略图。
- 原始文件名。
- 图片宽高。
- 是否已选。
- 选中顺序编号。

#### FR-ASSET-03 选择与排序

- 一个任务允许选择 0 到 7 张。
- 选择第 8 张时立即阻止并提示上限。
- 已选素材以独立有序列表展示。
- 支持拖拽改变已选素材顺序。
- 提交时按该顺序构造多个 `input_reference`。
- 未选择任何素材时，任务按文生视频提交。

#### FR-ASSET-04 移除

- 用户可从当前选择中取消素材，不删除文件。
- 用户可从项目素材库移除素材。
- 素材删除采用软删除。
- 已被历史任务引用的素材文件和元数据必须保留，历史任务仍能展示。
- 被移除素材不得出现在新任务的可选列表。

### 7.2 提示词和生成设置

#### FR-PROMPT-01 提示词

- 必填。
- 去除首尾空白后长度为 1 到 5000 字符。
- 支持换行。
- 占位文案应提示用户描述主体、动作、环境、镜头运动、光线和风格。
- 首期不自动改写、不翻译、不拼接隐藏创意词。
- 项目产品红线如需拼入请求，必须来自已有规则层并在开发计划中明确，不能由前端偷偷添加。

#### FR-CONFIG-01 固定参数

首期参数由后端决定，前端只读展示：

- 模型：`omni_flash-10s`。
- 尺寸：`1280x720`。
- 时长：10 秒。
- 输出数：1。

前端不得允许提交其他值。即使客户端伪造字段，后端也必须忽略或拒绝不匹配值。

#### FR-RUN-01 创建任务

- 点击生成后立即禁用重复点击。
- 前端生成 UUID 格式的 `client_request_id`。
- 后端以“项目 ID + client_request_id”保证幂等。
- 相同幂等键重复请求必须返回已存在任务。
- 创建任务时冻结提示词、参考图 ID 顺序和模型参数。
- 任务创建成功后立即出现在历史列表首位。
- 文生视频请求不得包含 `images`、`input_reference` 或本地参考路径。
- 参考图视频请求必须使用 multipart，并为每张图片重复写入 `input_reference`。

### 7.3 视频任务

#### FR-RUN-02 状态

业务状态只允许：

- `submitting`
- `queued`
- `processing`
- `completed`
- `failed`
- `submission_unknown`

下载状态独立保存：

- `not_started`
- `downloading`
- `downloaded`
- `download_failed`

`submission_unknown` 表示请求超时且无法判断上游是否已经创建任务。系统不得自动重新提交，避免重复扣费。

#### FR-RUN-03 自动同步

- 页面打开时立即同步所有运行中任务。
- 之后每 4 秒同步一次。
- 一个项目只允许存在一个轮询调度器。
- `completed`、`failed` 和 `submission_unknown` 停止常规轮询。
- 页面卸载时清理定时器。
- 单次查询失败且标记为可重试时保留原状态，下一个周期继续。
- 不可重试错误进入 `failed`。

#### FR-RUN-04 任务历史

- 默认返回最近 50 条，按创建时间倒序。
- 每条显示状态、进度、提示词摘要、参考图缩略图、创建时间和错误摘要。
- 点击任务后，中栏切换到该任务详情。
- 当前选中任务在右栏有清晰高亮。
- 刷新页面后默认选择最新任务；若最新任务已完成则播放其结果。

#### FR-RUN-05 视频完成

- 查询到上游 `completed` 且存在结果 URL 后，后端负责下载。
- 先下载到临时文件。
- 确认文件非空后原子移动为正式 MP4。
- 重复同步已完成任务不得重复损坏或覆盖正常文件。
- 上游临时 URL 不作为长期播放地址。
- 本地保存成功后返回可播放状态。

#### FR-RUN-06 播放与下载

- 中栏使用 HTML5 video 播放。
- 播放接口返回 `video/mp4`，必须支持浏览器 Range 请求。
- 播放默认不自动播放声音。
- 下载接口使用附件响应和安全文件名。
- 本地文件不存在时返回明确 404 错误，不能返回空视频。

#### FR-RUN-07 失败重试

- 失败任务显示归一化错误文案。
- 可重试错误显示“重试”按钮。
- 重试创建新任务，并写入 `retry_of_run_id`。
- 原失败任务保持不变。
- `submission_unknown` 需要用户确认后才能新建任务。
- 重试仍使用原任务冻结的提示词和参考图顺序。

#### FR-RUN-08 参数复用

- “复用参数”将历史任务的提示词、仍可用的参考图顺序填回创作区。
- 不自动提交。
- 已软删除素材仍可在历史任务中显示，但不能自动加入新的选择；界面必须提示用户重新上传或替换。
- 首期不把成品视频作为下一次生成的参考视频。

## 8. API 契约

所有接口沿用现有项目鉴权和统一 `ok/data`、`ok/error` 响应格式。

### 8.1 获取工作台

`GET /projects/{project_id}/video-workflow`

响应核心结构：

```json
{
  "project_id": "project_123",
  "config": {
    "model": "omni_flash-10s",
    "size": "1280x720",
    "duration_sec": 10,
    "max_reference_images": 7,
    "max_project_assets": 50,
    "max_asset_bytes": 10485760,
    "poll_interval_ms": 4000
  },
  "assets": [],
  "runs": []
}
```

为降低迁移风险，现有 `graph` 字段可暂时保留，但新前端不得依赖它，后续单独清理。

### 8.2 上传素材

`POST /projects/{project_id}/video-workflow/assets`

- Content-Type：`multipart/form-data`
- 字段：一个或多个 `files`

返回完整新增素材列表和当前项目有效素材数量。

### 8.3 素材内容

`GET /projects/{project_id}/video-workflow/assets/{asset_id}/content`

用于缩略图和原图预览。必须验证 asset 属于当前 project。

### 8.4 删除素材

`DELETE /projects/{project_id}/video-workflow/assets/{asset_id}`

执行软删除。当前选择由前端状态维护；删除成功后前端立即从当前选择移除。

### 8.5 创建任务

`POST /projects/{project_id}/video-workflow/runs`

请求：

```json
{
  "client_request_id": "03d6d568-fb26-4a8a-a3e1-9ca785ed16e0",
  "prompt": "固定镜头中，卡通三角形积木逐渐组合成一座桥，温暖课堂插画风格。",
  "reference_asset_ids": ["vref_a", "vref_b", "vref_c"]
}
```

后端自行补齐固定模型、尺寸和时长。

### 8.6 获取任务列表

`GET /projects/{project_id}/video-workflow/runs?limit=50`

limit 允许 1 到 100，默认 50。

### 8.7 获取单任务

`GET /projects/{project_id}/video-workflow/runs/{run_id}`

### 8.8 同步任务

`POST /projects/{project_id}/video-workflow/runs/{run_id}/sync`

必须幂等。已终态且文件已下载时直接返回当前任务。

### 8.9 重试任务

`POST /projects/{project_id}/video-workflow/runs/{run_id}/retry`

请求必须包含新的 `client_request_id`。返回新任务。

### 8.10 播放和下载

- `GET /projects/{project_id}/video-workflow/runs/{run_id}/content`
- `GET /projects/{project_id}/video-workflow/runs/{run_id}/download`

## 9. 数据结构

### 9.1 VideoReferenceAsset

```json
{
  "asset_id": "vref_abc123",
  "filename": "triangle-character.png",
  "path": "video_workflow/references/vref_abc123_triangle-character.png",
  "mime_type": "image/png",
  "byte_size": 123456,
  "width": 1024,
  "height": 1024,
  "created_at": "2026-06-29T00:00:00Z",
  "deleted_at": null
}
```

路径只在后端内部使用，API响应不得暴露绝对路径。

### 9.2 VideoWorkflowRun

```json
{
  "run_id": "task_abc123",
  "client_request_id": "03d6d568-fb26-4a8a-a3e1-9ca785ed16e0",
  "retry_of_run_id": null,
  "status": "processing",
  "download_status": "not_started",
  "progress": 42,
  "prompt": "提示词快照",
  "model": "omni_flash-10s",
  "size": "1280x720",
  "duration_sec": 10,
  "reference_asset_ids": ["vref_a", "vref_b"],
  "reference_assets": [
    {
      "asset_id": "vref_a",
      "filename": "character.png",
      "mime_type": "image/png",
      "width": 1024,
      "height": 1024
    }
  ],
  "provider_task_id": "remote_task_id",
  "error_code": null,
  "error_message": null,
  "retryable": false,
  "video_ready": false,
  "created_at": "2026-06-29T00:00:00Z",
  "updated_at": "2026-06-29T00:01:00Z"
}
```

`reference_assets` 是创建任务时冻结的展示元数据快照。即使素材之后被软删除，历史任务仍依靠该快照显示文件名、尺寸和缩略图；真实文件继续保留在原项目目录。

### 9.3 存储策略

- 继续使用现有项目 `tasks` 表。
- 请求快照写入 task payload JSON。
- Provider 状态、进度、错误和下载状态写入 result JSON。
- `client_request_id` 在项目内必须唯一；若现有表不支持数据库唯一约束，服务层必须在事务内检查。
- 素材清单继续保存在项目视频工作流目录的 JSON 清单中，写入采用临时文件加原子替换。
- 参考图片位于 `video_workflow/references/`。
- 成品视频位于 `video_workflow/runs/{run_id}.mp4`。

## 10. Provider 适配要求

`OctoVideoProvider` 继续作为唯一第三方网关适配层。

必须修正或保证：

1. multipart 中每个文件使用真实 MIME，而不是统一写死 `image/png`。
2. 参考图顺序必须与请求 ID 顺序一致。
3. 文生视频走 JSON，图生视频走 multipart。
4. 解析顶层和 `data` 内的 task ID、status、progress、video URL。
5. 将 `success` 归一化为 `completed`。
6. 将 `in_progress`、`processing` 归一化为 `processing`。
7. 任务查询必须携带 Bearer token。
8. Provider 原始错误写日志前必须脱敏。
9. 下载必须设置合理超时并使用临时文件。
10. 不在浏览器端暴露第三方 Base URL 或 API key。

## 11. 错误模型

首期至少提供以下稳定错误码：

| 错误码 | 场景 | 可重试 |
|---|---|---:|
| `VIDEO_PROVIDER_NOT_CONFIGURED` | 未配置服务 | 否 |
| `VIDEO_REFERENCE_INVALID` | 文件不是有效图片 | 否 |
| `VIDEO_REFERENCE_TOO_LARGE` | 单图超过限制 | 否 |
| `VIDEO_REFERENCE_LIMIT_EXCEEDED` | 超过 7 张或项目超过 50 张 | 否 |
| `VIDEO_REFERENCE_NOT_FOUND` | 素材不存在或不属于项目 | 否 |
| `VIDEO_PROMPT_REQUIRED` | 提示词为空 | 否 |
| `VIDEO_PROMPT_TOO_LONG` | 超过 5000 字符 | 否 |
| `VIDEO_REQUEST_CONFLICT` | 幂等键对应不同请求 | 否 |
| `VIDEO_SUBMIT_UNCERTAIN` | 提交超时，结果未知 | 需用户确认 |
| `VIDEO_AUTH_FAILED` | 上游鉴权失败 | 否 |
| `VIDEO_QUOTA_EXHAUSTED` | 上游额度不足 | 否 |
| `VIDEO_RATE_LIMITED` | 上游限流 | 是 |
| `VIDEO_CONTENT_REJECTED` | 内容审核拒绝 | 否 |
| `VIDEO_TASK_NOT_FOUND` | 上游任务不存在 | 否 |
| `VIDEO_TASK_FAILED` | 上游生成失败 | 视返回 |
| `VIDEO_DOWNLOAD_FAILED` | 视频下载失败 | 是 |
| `VIDEO_OUTPUT_NOT_FOUND` | 本地结果不存在 | 是 |

前端显示用户可理解的中文文案，同时保留错误码供排查。

## 12. 安全、可靠性和性能

### 12.1 安全

- 所有写接口必须走现有鉴权。
- 必须验证 project、asset 和 run 的归属关系。
- 上传文件名只能作为展示元数据，实际路径由服务端生成。
- 使用图片解码库验证真实格式。
- API key 仅存在服务端环境变量。
- 日志不得记录 Authorization 头。
- Provider 原始响应返回前必须移除可能的敏感字段。

### 12.2 可靠性

- 素材清单原子写入。
- 任务提交使用幂等键。
- 同步和下载幂等。
- 上游完成链接必须及时下载到本地。
- 服务重启后从 project.db 恢复任务。
- 文件下载失败不能把生成成功误写为生成失败；应保留 `completed + download_failed`。

### 12.3 性能

- 上传和下载使用流式文件操作，不能一次性把大文件全部读入内存。
- 一个页面只运行一个轮询器。
- 已终态任务不再轮询。
- 工作台初次最多返回 50 条任务。
- 缩略图首期可复用原图响应，但前端必须使用固定尺寸和懒加载；后期再增加独立缩略图。

## 13. 测试要求

### 13.1 后端单元和接口测试

必须覆盖：

- 有效 JPG、PNG、WebP 上传。
- 伪造扩展名、空文件、超大文件拒绝。
- 项目素材上限。
- 0、1、7 张参考图创建成功。
- 8 张参考图拒绝。
- 参考图顺序保持。
- 文生视频不发送参考字段。
- multipart 使用重复 `input_reference` 和真实 MIME。
- 相同幂等键返回同一任务。
- 相同幂等键但 payload 不同返回冲突。
- 状态归一化。
- 查询可重试和不可重试错误。
- 下载临时文件和原子替换。
- 重复同步不重复下载正常文件。
- 重试创建新任务并保留原任务。
- 应用重启后素材和任务仍存在。
- asset/run 跨项目访问被拒绝。

### 13.2 前端测试

必须覆盖：

- 0 张素材时仍可文生视频。
- 第 8 张素材无法选择。
- 拖拽排序后提交顺序正确。
- 空提示词禁用生成。
- 提交中防止双击。
- 每 4 秒轮询且终态停止。
- 页面卸载清理轮询器。
- 点击历史任务切换预览。
- 复用任务填回提示词和参考图顺序。
- 失败任务显示错误和重试按钮。
- Provider 未配置时禁止生成。

### 13.3 浏览器端到端测试

使用 fake provider 完成：

1. 创建或打开项目。
2. 进入视频工作台。
3. 上传 3 张图片。
4. 调整顺序。
5. 输入提示词。
6. 创建任务。
7. 自动从 queued 进入 processing 和 completed。
8. 页面播放视频。
9. 下载视频。
10. 刷新页面后仍能查看任务和结果。

### 13.4 真实接口烟测

通过环境变量显式启用，不进入默认 CI：

- 使用真实第三方 key。
- 上传 1 到 3 张无敏感内容的测试图。
- 创建一个 `omni_flash-10s` 任务。
- 轮询至完成或明确失败。
- 验证 MP4 已保存且非空。
- 保存脱敏的任务 ID、时间和结果，不保存 key。

## 14. 验收标准

只有以下条件全部满足，首期才算完成：

1. 用户能在项目工作区上传、预览、选择、排序和移除图片。
2. 单次最多 7 张，顺序与上游请求一致。
3. 文生视频和多参考图视频均能真实提交。
4. 页面自动显示状态和进度，不需要手动同步。
5. 完成视频能够在页面内播放并下载。
6. 任务历史至少保留最近 50 条。
7. 失败任务具有明确错误、重试入口和审计关系。
8. 历史任务可以恢复提示词和参考图组合。
9. 刷新页面、关闭浏览器和服务重启后任务不丢失。
10. 相同 `client_request_id` 不会创建两次上游任务。
11. 所有自动化测试通过。
12. 至少完成一次受控真实 Omni API 烟测。
13. 连续执行 10 次完整流程，不发生跨项目串数据、素材丢失、任务覆盖或错误状态倒退。

## 15. 当前代码改造方向

### 15.1 继续使用

- `apps/api/app/video_workflow.py`
- `apps/api/app/providers.py::OctoVideoProvider`
- `apps/api/app/store.py` 中现有项目 task 存储
- `apps/api/app/main.py` 中项目级 video-workflow 路由
- `apps/web/src/lib/api-client.ts`
- `apps/web/src/lib/store.ts`
- `apps/web/src/lib/types.ts`

### 15.2 需要重做

- `apps/web/src/components/video-workflow/VideoWorkflowCanvas.tsx`

该文件应拆分为固定工作台组件，停止使用 ReactFlow 作为首期主交互。具体拆分由实施计划定义。

### 15.3 只保留诊断用途

- `apps/api/app/media_workbench.py`
- `apps/web/src/components/screens/AdminMediaWorkbenchScreen.tsx`

首期不得同时给后台媒体页和项目工作区各实现一套新功能。正式能力只在项目级工作流演进。

## 16. Definition of Done

- 代码已合并到目标分支。
- 数据迁移或兼容逻辑已验证旧项目可打开。
- 后端测试、前端测试和浏览器 E2E 全部通过。
- 真实接口烟测完成。
- 配置说明更新，明确 `OCTO_API_KEY`、Base URL 和 Provider 模式。
- 不存在“假成功”“仅展示按钮”“需要人工改数据库”等未闭环行为。
- 功能行为与本文件一致；任何删减都需要重新获得产品确认。

## 17. 后续版本候选

首期完成后按价值另行排期：

1. 视频上传和 Omni 视频编辑。
2. `@角色/@场景/@道具` 素材语义。
3. 多结果批量生成和结果对比。
4. 视频帧提取并转为项目素材。
5. Prompt Agent 和多轮修改。
6. 首尾帧和 Veo 模型。
7. 视频延长、Remix。
8. 多片段 Scenebuilder。
9. 与课题分镜、中文配音和最终视频拼接流程集成。

这些候选不构成首期验收条件。
