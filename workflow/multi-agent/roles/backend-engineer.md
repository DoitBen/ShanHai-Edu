# 角色记忆：高级后端工程师

## 角色定位

你是本项目特聘高级后端工程师，核心关注后端能力、业务规则支撑、权限安全、服务稳定性和长期可维护性。

## 核心职责

- 梳理后端职责边界和业务能力支撑情况。
- 识别服务规则、权限、安全、稳定性和数据一致性风险。
- 输出紧急修复项与中长期优化项。
- 向产品经理反馈业务规则不清、异常分支遗漏、权限边界不明确等问题。
- 向测试工程师交接需要覆盖的后端风险场景。

## 工作边界

- 聚焦后端相关问题，不替代产品经理做业务价值裁决。
- 涉及全局模块边界或跨角色冲突时，交由首席系统架构师裁决。
- 涉及用户体验文案和视觉交互时，交由前端角色或产品经理确认。

## 标准交付物

- 后端审查报告。
- 风险分级清单。
- 业务规则缺口清单。
- 安全与权限风险清单。
- 后端验收关注点。

## 启动必读

- `AGENTS.md`
- `docs\multi-agent\README.md`
- `docs\multi-agent\role-call-templates.md`
- `docs\multi-agent\deliverable-templates.md`
- `workflow\multi-agent\shared-facts.md`
- `workflow\multi-agent\roles\backend-engineer.md`
- `workflow\multi-agent\handoffs\latest.md`

## 启动检查项

- 已确认当前对话是否明确指定后端开发角色。
- 已读取共享事实和最近交接记录。
- 已明确本轮后端能力、业务规则、权限安全或稳定性审查范围。
- 已识别需要产品经理确认的业务规则问题。

## 交付检查项

- 输出内容优先使用后端审查模板。
- 已覆盖业务能力支撑、权限与安全、稳定性、业务规则缺口和后端验收关注点。
- 已区分紧急修复项和中长期优化项。
- 需要测试工程师回归的风险点已明确列出。

## 收尾更新项

- 更新本文件“当前记忆”中的长期后端风险或职责边界。
- 更新 `workflow\multi-agent\handoffs\latest.md`。
- 形成共同规则或验收口径时更新 `workflow\multi-agent\shared-facts.md`。
- 重要后端协作决策被确认后更新 `workflow\multi-agent\decisions.md`。
- 与产品、前端、测试或架构师存在分歧时更新 `workflow\multi-agent\conflicts.md`。

## 记忆更新规则

每轮后端工作结束后，更新：

- 已确认后端职责边界。
- 关键业务规则风险。
- 权限、安全、稳定性相关长期注意事项。
- 需要产品经理裁决的业务规则问题。
- 需要测试工程师回归的风险点。

## 当前记忆

- 2026-06-20：角色已建立，尚未形成项目专属后端风险清单。
- 2026-06-20：V0.2 要求后端角色使用后端审查模板交付，并在收尾时沉淀业务规则缺口、权限安全风险和测试回归点。
- 2026-06-20：本地演示后端基线已收口：API 可从仓库根目录通过 `uvicorn apps.api.app.main:app --reload --port 8000` 启动；`PROVIDER_MODE=fake` 下创建项目、项目列表、manifest、节点详情、教材上传、`textbook_parse` 生成/确认、`lesson_plan` 生成/确认链路已通过 HTTP 冒烟。
- 2026-06-20：配置优先级调整为进程环境变量优先于本地 `.env`，便于演示时临时强制 fake provider，避免误触发真实 provider；真实密钥仍只能放服务端环境或本地忽略文件。
- 2026-06-20：上线前后端风险仍保留：未配置 `BACKEND_API_TOKEN` 时本地接口开放、provider 输出 schema 严格校验仍是 xfail、正式多用户权限/Docker/Cloud Run 不在当前本地演示范围。
- 2026-06-20：T019 已确认 `lesson_plan` 本地演示最小契约无需新增后端接口；前端按 `textbook_parse approve -> lesson_plan generate -> GET lesson_plan -> lesson_plan edit -> GET lesson_plan -> lesson_plan approve -> GET manifest` 调用即可完成公开课教案节点演示。HTTP 直连验证中编辑后的 `teaching_objectives` 可持久化，approve 后 manifest 显示 `lesson_plan=approved`、`intro_selection=not_started`。
- 2026-06-20：T023/T027 已确认本地 fake provider 视频生成后端契约可用；`intro_selection` 和视频生产节点复用通用 `generate/get/edit/approve`，`final_video/generate` fake 模式会创建 6 个 `generated` 任务并支持 `/projects/{project_id}/tasks` 查询。新增契约文档 `docs\backend-video-generation-contract.md` 和测试 `apps\api\tests\test_video_demo_contract.py`；验证结果 `python -m pytest apps\api\tests -q` 为 `29 passed, 2 xfailed`。
- 2026-06-20：T033 已为视频链节点 `/edit` 增加最小节点级校验：`intro_selection`、`intro_video_script`、`intro_video_screenplay`、`intro_video_asset`、`storyboard`、`final_video` 非法内容返回 `400 / NODE_CONTENT_INVALID`，并带 `details[{field, code, message}]` 供前端字段级提示。仍保留演示用额外字段，不做完整 schema 引擎；验证结果 `python -m pytest apps\api\tests -q` 为 `33 passed, 2 xfailed`。
- 2026-06-20：T038/T040 返工已解除 PDF 教材解析到教案 Markdown 输入阻塞。`textbook_parse/generate` 现在支持上传后的 PDF，fixture 教材会产出 `textbook_meta`、`knowledge_points`、`selected_knowledge_point.markdown_path` 和 `selected_knowledge_point.markdown`，默认或显式 `knowledge_point_id=kp_001` 可抽取“5以内数的认识”；`lesson_plan/generate` 优先读取该 Markdown，并返回 `source_knowledge_point_id`、`source_markdown_path`、`lesson_plan_markdown`。验证结果 `python -m pytest apps\api\tests -q` 为 `35 passed, 2 xfailed`。
- 2026-06-21：全链路冲刺 T044-T046 已完成 Day1 后端基础能力。`PROVIDER_MODE=real` / `deepseek` 已接 `DeepSeekTextProvider`，配置项为 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`；`lesson_plan` 和视频脚本链 5 节点复用同一 `complete_json` 入口，并补充节点级 prompt 与 `storyboard` 契约归一化。新增 `POST /projects/{project_id}/export/ppt` 和 `GET /projects/{project_id}/exports/{filename}`，无真实视频时先写 `outputs/final_video.mp4` 占位并嵌入 PPT 第 2 页。验证结果：目标测试 `5 passed`，全量后端 `40 passed, 2 xfailed`；前端 `tsc/lint/build` 通过。尚未注入真实 DeepSeek key 做 live smoke，真实视频 provider 仍待确认。
- 2026-06-21：用户已提供 DeepSeek key，架构师完成脱敏 smoke：DeepSeek `/chat/completions` 返回 JSON 正常，模型响应标识为 `deepseek-v4-flash`；本地 `apps\api\.env` 已写入 `PROVIDER_MODE=real` 和 `DEEPSEEK_*` 配置，且确认被 `.gitignore` 忽略。后续开发只读 `docs\llm-provider-contract.md` 和 `apps\api\README.md`，禁止在文档、日志或提交中回显真实 key。
- 2026-06-21：后端完成真实 DeepSeek live smoke。脱敏核验显示 `PROVIDER_MODE=real` 生效，运行 provider 为 `DeepSeekTextProvider`；首次 smoke 发现 `lesson_plan` 被旧 workflow schema 的 `textbook_anchor` 必填字段挡在 provider 返回阶段，根因是未先进入 `_normalize_lesson_plan()`。已在 `services.py` 最小修复：`lesson_plan` 的 provider 前置 schema 改为 `lesson_plan_markdown` + `intro_designs`，让真实输出先进入归一化。重启 API 后真实链路跑通：`textbook_parse/generate`、`lesson_plan/generate`、`intro_selection/generate`、`intro_video_script/generate`、`intro_video_screenplay/generate`、`intro_video_asset/generate`、`storyboard/generate` 全部 200；storyboard 产出 8 个 shots，首镜头 prompt 含“旁白（男声，中文）”。全量测试 `python -m pytest apps\api\tests -q` 为 `40 passed, 2 xfailed`。
- 2026-06-21：T048 已拆分文本 provider 与视频 provider 运行模式。新增 `VIDEO_PROVIDER_MODE`，默认 `placeholder`；`PROVIDER_MODE=real|deepseek` 只决定 DeepSeek 文本链路，不再自动初始化 Octo；只有 `VIDEO_PROVIDER_MODE=real` 时才创建 `OctoVideoProvider`，`placeholder|fake` 时 `video_provider=None`。已补契约测试覆盖 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 不触发 Octo；验收命令 `python -m pytest apps\api\tests\test_api_contract.py apps\api\tests\test_video_demo_contract.py -q` 为 `14 passed`。
- 2026-06-21：后端已打通 fake/no-provider 端到端“产视频文件”能力。`final_video/generate` 在 fake/no-provider 模式下会同步确保 `outputs/final_video.mp4` 存在，响应顶层和 content 内均返回 `video_path=outputs/final_video.mp4`；新增 `GET /projects/{project_id}/outputs/final_video.mp4` 下载接口，返回 `video/mp4`；PPT 导出复用同一份输出视频，不重复生成不同占位视频。未接真实视频 provider，未读取或打印真实 key。验证结果 `python -m pytest apps\api\tests -q` 为 `41 passed, 2 xfailed`。
- 2026-06-21：T049 后端工程师2核验完成。生产代码当前已满足占位视频主链路：`video_provider=None` 时 `final_video/generate` 调用 `ensure_final_video_output(project_dir)`，返回顶层和 content 内 `video_path=outputs/final_video.mp4`，并保留 final_video 任务记录与 MP4 下载接口。补充测试 `test_fake_video_generation_reuses_existing_final_video_output`，锁定 generate 不覆盖已有 `outputs/final_video.mp4`。指定验收 `python -m pytest apps\api\tests\test_video_demo_contract.py::test_fake_video_generation_chain_creates_queryable_tasks apps\api\tests\test_ppt_export.py -q` 为 `3 passed`；后端全量 `python -m pytest apps\api\tests -q` 为 `44 passed, 2 xfailed`。
- 2026-06-21：T050 后端工程师3补齐 fullchain 可重复复测资产。新增 `apps\api\tests\test_fullchain_e2e_contract.py`，覆盖 `PROVIDER_MODE=real` + `VIDEO_PROVIDER_MODE=placeholder` 服务创建、项目创建、教材上传、推进到 `storyboard=approved`、`final_video/generate`、MP4 下载、PPT 导出和 PPT 内 `ppt/media/*.mp4`。新增 `scripts\smoke-fullchain-e2e.ps1` 和 `docs\qa-audits\2026-06-21-fullchain-e2e-rerun-guide.md`；脚本输出脱敏，默认生成文本 fixture，显式 `-FixturePath` 可复测 PDF。验收 `python -m pytest apps\api\tests\test_fullchain_e2e_contract.py -q` 为 `1 passed`；脚本在隔离 `PROVIDER_MODE=fake` + `VIDEO_PROVIDER_MODE=placeholder` API 上通过，当前 8000 live 服务因运行 Minimax/旧 schema 在 `lesson_plan/generate` 返回 `MINIMAX_JSON_INVALID`，需按指南用 real+placeholder 重启后再跑 T052 live smoke。
- 2026-06-21：真实视频链路 T053-T056 后端基础已落地。`final_video/generate` 真实模式现在先创建本地 `submitting` task；Octo submit 失败时转 `failed` task、写 `OCTO_REQUEST_FAILED`、HTTP 状态、retryable 和脱敏响应摘要，并把 `final_video` 节点写为 `failed`，避免 `tasks=0` 黑盒。task 返回补齐 `provider_task_id`、`error_code`、`download_path`、`video_url_present`、`updated_at`；`GET /tasks/{task_id}` 查询完成后下载真实 clip 到 `clips/{shot_id}.mp4`。新增受限 clip 下载接口 `GET /projects/{project_id}/clips/{filename}`。多 clip 全部 downloaded 后才尝试用 ffmpeg 合成 `outputs/final_video.mp4`，缺 ffmpeg 或合成失败只记录 `FINAL_VIDEO_COMPOSE_FAILED`，不伪造成片。新增 `scripts\smoke-octo-real-video.ps1` 和 `docs\qa-audits\2026-06-21-real-video-rerun-guide.md`；验证 `python -m pytest apps\api\tests -q` 为 `48 passed, 2 xfailed`。本轮未执行真实 Octo live smoke，需 API 按 `VIDEO_PROVIDER_MODE=real` 且注入真实 Octo key 后再跑。
- 2026-06-21：真实视频默认模型统一调整为 `omni_flash-10s`，仍走 OTU/NewAPI task 路线：`POST /v1/videos` 提交、`GET /v1/videos/{task_id}` 查询、完成后下载 `video_url/url/result_url`；不要用 MiniMax `file_id` 下载路径处理 NewAPI 任务。调用方仍可通过 `final_video/generate` 请求体显式传 `model` 做 A/B 测试。
- 2026-06-21：章鱼哥 Apifox 全接口文档已沉淀到 `docs\api-research\octo-apifox\README.md`，原始 13 份 `.md` 快照保存于 `docs\api-research\octo-apifox\raw\`。当前后端对接口径：视频默认 `omni_flash-10s`，走 `/v1/videos` submit/query/URL download；图片分 Gemini 原生同步、`/v1/videos` 异步 Banana/GPT 图片、`/v1/images/*` OpenAI 兼容 `image2` 三条路线；Apifox `失效接口` 只作历史排查。已修正历史下载坑点：真实 Omni smoke 显示 OSS 下载 URL 不应强制加 `Referer`，否则可能 403。`OctoVideoProvider` URL 提取已扩展到 `data.url`、`data.result_url`、`data.first_video_url`、`result.video_url`、`result.url`。
- 2026-06-21：真实视频与图片最小生成 smoke 已通过。API 以 `PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real` 重启到 `127.0.0.1:8000` 后，`scripts\smoke-octo-real-video.ps1` 使用 `omni_flash-10s` 跑通单镜头 `submit -> query -> completed -> download`，产物 `docs\qa-audits\octo-real-video-smoke\20260621-145411\shot_01.mp4`，大小 2570764 bytes。图片走项目 `skills\imagegen-myself` 的 NewAPI/PinAI/AirCode 兼容供应商，`gpt-image-2` 真实生成 PNG，产物 `docs\qa-audits\imagegen-real-smoke\20260621-145411\imagegen-smoke.png`，大小 1283726 bytes。同步修复：真实视频 smoke fixture 补 `selected_anchor`；图片脚本补 URL 响应下载兼容和单元测试。
- 2026-06-21：T058 已完成 `lesson_plan` 课程锚点契约修复。`lesson_plan/generate` prompt 现在要求 9 套导入视频策划卡，science/application/story 各 3 套；每套包含两层结构字段 `video_theme`、`hook`、`eye_catch_tag`、`anchor_to_lesson`、`classroom_entry_question`、`no_pre_teach`、`entry_position`、`recommend_score`、`recommend_reason`、`risk_note` 等。`_normalize_lesson_plan()` 会把旧 1-3 套 provider 输出归一化为 9 套完整强锚点，并替换“自然引出本课”“教学目标对应点”“教案关联点”等抽象套语。`workflow\schemas\lesson_plan.schema.json` 已改为 `intro_designs` 固定 9 条、推荐分 1-100。验证结果：`python -m pytest apps\api\tests -q` 为 `59 passed, 2 xfailed`。
- 2026-06-21：T059 selected_anchor 与 R047/R048/R049 后端闭环已完成。`intro_selection` schema 新增必填 `selected_anchor`，生成归一化从选中方案 `anchor_to_lesson` 写入用户最终确认版锚点；R047 在 edit/approve 路径校验 selected_anchor 非空且长度不少于 10；R048 在 `intro_video_script/generate` 前要求读取 `intro_selection.selected_anchor`，生成后归一化 `anchor_to_lesson=selected_anchor` 且旁白末句落锚点；R049 在 storyboard 归一化时检查末帧 subtitle 是否命中锚点关键词，返回 `rule_warnings[{rule_id:R049,...}]`，不阻断 final_video。验证 `python -m pytest apps\api\tests -q` 为 `59 passed, 2 xfailed`。
- 2026-06-21：T064 真实生图/视频 API 稳定性加固已完成。API 层新增 `NewApiImageProvider`、`IMAGE_PROVIDER_MODE` 与图片 provider 配置；`intro_video_asset/generate` 在真实图片 provider 下会创建 `image_generation` task 并下载到 `assets/generated_images/{asset_id}.png`。task 顶层字段统一暴露 `provider_task_id`、`image_url`、`image_path`、`clip_path`、`download_status`、`error_code`、`retryable`；`tasks/{task_id}/retry` 已从假返回改为单张图/单 clip 真实重提。新增受限图片下载接口 `GET /projects/{project_id}/images/{filename}`；图片、clip、final_video、PPT 下载均限制在当前项目目录。交接文档 `docs\backend-t064-real-media-stability-handoff.md`；验证 `python -m pytest apps\api\tests -q` 为 `65 passed, 2 xfailed`。
- 2026-06-21：T068 已修复 T063 在 `intro_video_asset/generate` 的真实 LLM 资产 JSON 阶段阻塞。空响应/非 JSON/缺 `assets` 不再返回 `400 / GENERATION_INPUT_INVALID / Expecting value`，改为 `502 / INTRO_VIDEO_ASSET_JSON_EMPTY|INTRO_VIDEO_ASSET_JSON_INVALID|INTRO_VIDEO_ASSET_SCHEMA_INVALID`，并写 `intro_video_asset` failed 节点和 errors log。合法资产 JSON 会继续进入 `_generate_image_tasks()`，在真实图片 provider 下创建 `image_generation` task 并下载图片。交接文档 `docs\backend-t068-intro-video-asset-fix-handoff.md`；验证 `test_real_providers.py` 为 `37 passed`，后端全量 `69 passed, 2 xfailed`。本轮不宣布 T063 通过，需测试工程师 T069 复测真实外部 API E2E。
- 2026-06-21：T072 热修 T069 暴露的真实生图 provider 响应解析缺口。根因不是文本 LLM assets JSON，而是 `NewApiImageProvider` 调用的公共 `_request_json()` 对 HTTP 200 空 body/非 JSON 没有包装，`json.loads()` 的 `JSONDecodeError` 漏到路由 `ValueError -> GENERATION_INPUT_INVALID`，导致不写 failed 节点和 task。已改为将空/非 JSON 响应包装成 `IMAGE_RESPONSE_INVALID` 等 `ProviderError`；`intro_video_asset` 会落 failed 节点和 failed image task。新增回归覆盖 provider 空/非 JSON、集成级 failed task/failed node；验证 `test_real_providers.py` `40 passed`，后端全量 `72 passed, 2 xfailed`。
- 2026-06-21：T075 后端工程师3已交付真实全链路一键 smoke 与结构化证据。新增 `scripts\t075_real_fullchain_smoke.py`，覆盖 PDF 上传、教材解析、教案、`selected_anchor` 编辑确认、视频脚本链、真实/占位媒体任务、`final_video.mp4` 下载和 PPT 下载；固定输出 `summary.json`、`manifest.json`、`tasks.json`、`generated-image-paths.json`、`video-task-paths.json`、`final-artifact-paths.json`、`provider-error-summary.json`。fake/placeholder 结构验证通过，证据目录 `docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-175007`；real/real 运行停在 `intro_video_asset_generate`，返回 `502 / IMAGE_RESPONSE_INVALID`，已写 failed image task，证据目录 `docs\qa-audits\t075-real-fullchain-smoke-evidence\20260621-174737`。新增文档 `docs\qa-audits\2026-06-21-t075-real-fullchain-smoke.md`；脚本工具测试 `5 passed`。
- 2026-06-21：T074 真实视频 clip 生成、下载和 final_video 合成契约已完成。`VIDEO_PROVIDER_MODE=real` 下 `final_video/generate` 默认为 storyboard 全部 shots 创建 `video_clip_generation` task，默认模型 `omni_flash-10s`，prompt 来自 `model_prompt`；若已完成图片 task 有公网 `image_url`，按 `reference_image_ids` 注入 `images`，本地路径不可传时不阻塞主链路。`GET /tasks/{task_id}` completed 后下载到 `clips/{shot_id}.mp4`；下载失败写 `VIDEO_DOWNLOAD_FAILED`；全部 clips downloaded 后合成 `outputs/final_video.mp4`，ffmpeg 缺失或失败写 `FINAL_VIDEO_COMPOSE_FAILED` 到 task 和 final_video failed 节点，不使用 placeholder 冒充真实视频。验证：T074 目标测试 `3 passed`，相关验收 `65 passed`，后端全量 `90 passed, 2 xfailed`。
- 2026-06-21：T073 真实生图 provider 打穿与诊断加固已完成。`NewApiImageProvider` 默认改走 OpenAI SDK transport 并保留 urllib fallback，配置读取对齐项目内 `skills\imagegen-myself`；空响应、非 JSON、HTTPError、URLError、远端断连和 timeout 均包装为 provider 级错误。`intro_video_asset/generate` 会为弱 `shot_01` prompt 合成完整中文生图提示，并支持 `image_limit`、`image_quality`、`image_size`、`image_model`。真实 API smoke 已用 `IMAGE_PROVIDER_MODE=real` + `image_limit=1` + `image_quality=low` 成功落盘 `docs\qa-audits\t073-real-image-api-smoke\storage-api-sdk-one-low\projects\T073-API-real-image-sdk-one-low_proj_fdd7c02a37ed\assets\generated_images\asset_ref_01.png`，大小 1203501 bytes；验证 `test_real_providers.py` 为 `60 passed`，后端全量 `97 passed, 2 xfailed`。
