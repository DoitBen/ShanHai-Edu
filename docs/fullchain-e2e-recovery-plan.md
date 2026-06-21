# ShanHaiEdu T048-T051 端到端可实测修复计划

**版本**：v1.0  
**日期**：2026-06-21  
**目标阶段**：本地端到端可实测，保证用户能从上传教材走到下载 PPT  
**适用角色**：后端工程师 1、后端工程师 2、后端工程师 3、前端工程师  

---

## 1. 当前结论

T047 测试结论为【阻塞】，但阻塞范围很集中：

- 已通过：PDF 上传、教材解析、字段回填/手改、知识点 Markdown、DeepSeek 教案生成、5 个视频脚本链节点、`storyboard=approved`。
- 已通过：阻塞后单独调用 `export/ppt` 可以生成占位 MP4 和 PPT，且 PPT 内嵌 MP4 与下载 MP4 hash 一致。
- 阻塞点：`PROVIDER_MODE=real` 同时控制文本 provider 和视频 provider，导致 `final_video/generate` 调用真实 Octo provider，返回 `502 / OCTO_REQUEST_FAILED / HTTP 503`，没有产出主链路 `outputs/final_video.mp4`。

本轮目标不是上线发布，也不是追求真实视频质量。本轮唯一目标是：

> 在本地真实 DeepSeek 文本链路 + 占位视频链路下，用户可以完整跑通 PDF → 教案 → 脚本链 → final_video → MP4 下载 → PPT 下载。

---

## 2. 共享运行模式契约

### 2.1 文本 provider

继续使用现有变量：

```env
PROVIDER_MODE=real
```

含义：

- `real` / `deepseek`：文本节点使用 DeepSeek。
- `fake`：文本节点使用 fake provider。

### 2.2 视频 provider

新增独立变量：

```env
VIDEO_PROVIDER_MODE=placeholder
```

取值：

| 值 | 含义 | 本轮要求 |
|---|---|---|
| `placeholder` | 不调用真实视频 provider，直接生成 `outputs/final_video.mp4` 占位视频，并创建可查询任务记录 | 必须实现 |
| `fake` | 等价于 `placeholder`，兼容历史 fake 演示口径 | 必须实现 |
| `real` | 调用真实 Octo 或后续真实视频 provider | 保留现有能力，不作为本轮通过条件 |

默认策略：

- 未配置 `VIDEO_PROVIDER_MODE` 时默认 `placeholder`。
- 本地 T047/T052 复测使用 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder`。
- `VIDEO_PROVIDER_MODE=real` 失败时，不影响 placeholder 演示链路。

### 2.3 final_video 主链路契约

`POST /projects/{project_id}/nodes/final_video/generate` 在 `VIDEO_PROVIDER_MODE=placeholder|fake` 下必须：

- 不调用 Octo。
- 同步确保 `storage/projects/{project_id}/outputs/final_video.mp4` 存在。
- 响应顶层包含：

```json
{
  "node_id": "final_video",
  "status": "running",
  "video_path": "outputs/final_video.mp4"
}
```

- `content.video_path` 同样为 `outputs/final_video.mp4`。
- `/projects/{project_id}/outputs/final_video.mp4` 返回 `200`，`content-type` 为 `video/mp4`。
- `/projects/{project_id}/tasks` 至少返回 final_video 相关任务记录，方便前端展示“已生成演示视频”。

### 2.4 PPT 契约

`POST /projects/{project_id}/export/ppt` 必须：

- 复用 `outputs/final_video.mp4`。
- 不覆盖已存在的同名视频文件。
- 返回 `.pptx` 下载链接。
- PPT 内至少包含一个 `ppt/media/*.mp4`。

---

## 3. 四人并行安排

### T048 后端工程师 1：拆分文本 provider 与视频 provider 模式

**目标**：解除 `PROVIDER_MODE=real` 同时控制 DeepSeek 和 Octo 的耦合。

**负责文件**：

- `apps\api\app\settings.py`
- `apps\api\app\main.py`
- `apps\api\.env.example`
- `apps\api\tests\test_api_contract.py`
- `apps\api\tests\test_video_demo_contract.py`
- `docs\llm-provider-contract.md`
- `apps\api\README.md`

**必须完成**：

1. 在 `Settings` 中新增 `video_provider_mode`，读取环境变量 `VIDEO_PROVIDER_MODE`，默认 `placeholder`。
2. `create_app()` 中 `PROVIDER_MODE=real|deepseek` 只决定文本 provider。
3. `video_provider` 只在 `VIDEO_PROVIDER_MODE=real` 时初始化 Octo。
4. `VIDEO_PROVIDER_MODE=placeholder|fake` 时 `video_provider=None`，保证 `final_video/generate` 不触发 Octo。
5. 更新 `.env.example`、README、LLM 文档，只写变量名和占位说明，不写真实密钥。
6. 增加测试覆盖 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 时不会初始化真实视频 provider。

**验收命令**：

```powershell
python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_video_demo_contract.py -q
```

---

### T049 后端工程师 2：修复 final_video/generate 占位视频主链路

**目标**：让 `final_video/generate` 在 placeholder/fake 视频模式下产出用户可下载的主链路 MP4，而不是只依赖 `export/ppt` 兜底。

**负责文件**：

- `apps\api\app\services.py`
- `apps\api\app\video_outputs.py`
- `apps\api\tests\test_video_demo_contract.py`
- `apps\api\tests\test_ppt_export.py`

**必须完成**：

1. `final_video/generate` 在 `video_provider=None` 时走占位链路。
2. 占位链路必须调用 `ensure_final_video_output(project_dir)`。
3. 返回顶层 `video_path=outputs/final_video.mp4`。
4. 返回 `content.video_path=outputs/final_video.mp4`。
5. `/projects/{project_id}/tasks` 保持可查询 final_video 任务。
6. `export/ppt` 继续复用同一份 MP4，不能新写另一份。
7. 如果已有 `outputs/final_video.mp4`，不得覆盖。

**验收命令**：

```powershell
python -m pytest apps\api\tests\test_video_demo_contract.py::test_fake_video_generation_chain_creates_queryable_tasks apps\api\tests\test_ppt_export.py -q
```

---

### T050 后端工程师 3：补端到端复测脚本与诊断证据

**目标**：给团队一个可重复执行的本地 E2E 脚本，避免每次靠人工拼接口判断。

**负责文件**：

- `apps\api\tests\test_fullchain_e2e_contract.py`
- `scripts\smoke-fullchain-e2e.ps1`
- `docs\qa-audits\2026-06-21-fullchain-e2e-rerun-guide.md`

**必须完成**：

1. 新增后端集成测试，覆盖 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 的服务创建。
2. 集成测试最少覆盖：
   - 创建项目。
   - 上传文本或 fixture 教材输入。
   - 推进到 `storyboard=approved`。
   - 调用 `final_video/generate`。
   - 下载 `outputs/final_video.mp4`。
   - 调用 `export/ppt`。
   - 检查 PPT 内存在 `ppt/media/*.mp4`。
3. 新增 PowerShell smoke 脚本，参数包含 API base URL、项目名、fixture 路径。
4. 脚本输出必须脱敏，不打印任何 `DEEPSEEK_API_KEY`、`OCTO_API_KEY`。
5. 复测指南写清楚启动命令、环境变量、通过标准、失败时看哪些证据。

**验收命令**：

```powershell
python -m pytest apps\api\tests\test_fullchain_e2e_contract.py -q
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-fullchain-e2e.ps1 -ApiBaseUrl http://127.0.0.1:8000
```

---

### T051 前端工程师：最终视频节点用户可用体验收口

**目标**：用户在真实 API 模式下遇到 placeholder 视频时能明确看到“演示视频已生成”，可以下载 MP4 和 PPT；遇到真实视频 provider 失败时不把用户卡死。

**负责文件**：

- `apps\web\src\lib\api-client.ts`
- `apps\web\src\lib\types.ts`
- `apps\web\src\components\screens\ProjectWorkspaceScreen.tsx`
- `workflow\multi-agent\roles\frontend-ui-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

**必须完成**：

1. 最终视频生成成功后，如果后端返回 `video_path`，展示“下载 MP4”入口。
2. 下载 MP4 使用后端返回或约定路径 `/projects/{project_id}/outputs/final_video.mp4`。
3. PPT 导出入口继续保留。
4. 如果 `final_video/generate` 返回 `OCTO_REQUEST_FAILED`，页面显示可读提示：真实视频服务暂不可用，可切换占位视频模式完成本地演示。
5. placeholder 模式成功时，页面文案不得误导为“真实 AI 视频成片已完成”，建议使用“演示视频文件已生成”。
6. 不改整体 UI 版式，不重构工作区大组件。

**验收命令**：

```powershell
cd apps\web
bunx tsc --noEmit --pretty false
bun run lint
bun run build
```

浏览器验收：

- 真实 API 模式进入最终视频节点。
- 点击生成后显示可下载 MP4。
- 点击导出 PPT 后显示可下载 PPT。
- 控制台无应用级 error/warn。

---

## 4. 集成顺序

1. 后端工程师 1 先完成 `VIDEO_PROVIDER_MODE` 配置拆分。
2. 后端工程师 2 基于新配置收口 `final_video/generate` 占位主链路。
3. 后端工程师 3 在 1、2 完成后补 E2E 契约测试和 smoke 脚本。
4. 前端工程师可并行先接下载入口和错误态，等后端返回字段稳定后做一次联调。
5. 四人完成后，由测试工程师复跑 T047，复跑任务编号为 T052。

---

## 5. T052 复测通过标准

T052 只判断本地可实测，不判断上线发布。

必须全部满足：

- `PROVIDER_MODE=real`
- `VIDEO_PROVIDER_MODE=placeholder`
- PDF 上传成功。
- 教材解析成功。
- 知识点 Markdown 可预览。
- 教案生成成功。
- 5 个视频脚本链节点生成并确认成功。
- `final_video/generate` 返回 `200`。
- `outputs/final_video.mp4` 下载返回 `200` 和 `video/mp4`。
- `export/ppt` 返回 `200`。
- `.pptx` 下载成功。
- PPT 内存在 MP4。
- 前端页面能看到 MP4 下载和 PPT 下载入口。

---

## 6. 本轮不做

- 不追真实视频 provider 稳定性。
- 不做真实视频质量评分。
- 不做音频合成、转码、剪辑。
- 不做 Cloud Run 上线。
- 不做账号权限、多租户、计费。
- 不做大规模性能优化。

