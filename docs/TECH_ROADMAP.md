# v1 技术路线规划

版本：2026-06-19 v1
状态：交付开发团队，待评审
读者：全栈开发、后端、前端、AI 接入、DevOps、PM

本文档是 `AI-youjiao-promax` 半自动化工作流产品的开发实施规划。读完它你应该清楚：
1. 整体技术架构
2. 模块拆解 + 每模块的输入输出和依赖
3. 三个月里程碑 + 验收标准
4. 技术选型理由
5. 风险点和兜底策略

---

## 0. 前置阅读

按这个顺序读，再回来读本文：

1. `半自动化工作流/README.md` — 工作流总览
2. `半自动化工作流/workflow.yaml` — DAG / 状态机 / 红线 / 词表（**核心**）
3. `半自动化工作流/schemas/*.json` — 19 个节点产物的字段定义
4. `半自动化工作流/rules/` — 36 条机器可调度规则
5. `半自动化工作流/prompts/` — 11 个 LLM 模板
6. `v1_产品决策记录.md` — 产品决策和"为什么"

不要去读 `执行规范/` 和 `工作流主包/`。那些是**历史素材库**，不是产品输入。

---

## 1. 产品一句话定义

一节小学数学公开课作为一个项目，单人独立操作，AI 按字段化 schema 生成产物，
教研员每步可直接编辑或让 AI 重做，满意后 approve 进入下一步，
最终交付可编辑 PPTX + 中文男声配音的导入视频。

---

## 2. 技术架构

### 2.1 三层架构

```
┌──────────────────────────────────────────────────────────┐
│  前端层 (Next.js + React)                                │
│  - 9 步工作流可视化（项目首页 / 节点工作区 / 偏好画像）  │
│  - 字段化表单（按 schemas/*.json 自动渲染）              │
│  - 重做/编辑双通道 + 种子参数面板                        │
│  - 异步任务状态/进度可视化                               │
│  - 错误反馈一键打包                                      │
└─────────────────┬────────────────────────────────────────┘
                  │  REST + Server-Sent Events
┌─────────────────┴────────────────────────────────────────┐
│  后端层 (Python FastAPI)                                 │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  状态引擎       │  │  规则执行器     │                │
│  │  (workflow.yaml │  │  (rules/*.yaml) │                │
│  │   驱动)         │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  LLM 调用层     │  │  异步任务队列   │                │
│  │  (统一 Provider │  │  (Celery/RQ)    │                │
│  │   接口)         │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  字段化校验     │  │  飞轮记录       │                │
│  │  (JSON Schema)  │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
└─────────────────┬────────────────────────────────────────┘
                  │
┌─────────────────┴────────────────────────────────────────┐
│  存储层                                                  │
│  - SQLite per project (project.db)                       │
│  - 文件系统存二进制 (assets/, exports/)                  │
│  - 错误日志 (errors.log)                                 │
└──────────────────────────────────────────────────────────┘
                  │
┌─────────────────┴────────────────────────────────────────┐
│  外部依赖                                                │
│  - LLM: DeepSeek / Claude / GPT                          │
│  - 生图: gpt-image-2                                     │
│  - 视频: omni_flash-10s / sora-2-12s                     │
│  - TTS: 待选型                                            │
│  - 现有脚本: ppt-master, scripts/*.py 门禁脚本           │
└──────────────────────────────────────────────────────────┘
```

### 2.2 关键架构原则

**A. workflow.yaml 是真源**
状态引擎不写死 9 步流程，而是读 workflow.yaml 动态构建 DAG。改流程改 yaml 即可，不改代码。

**B. JSON Schema 驱动一切结构化**
前端表单按 schema 渲染、后端校验按 schema 跑、LLM prompt 按 schema 约束输出。
三层共用一套 schema 文件，**永远不会出现"前端字段名和后端字段名不一致"的灾难**。

**C. 规则与执行解耦**
rules/*.yaml 只定义"要查什么、违反时怎样、谁来查"。
执行器有三种：内置 Python、外部 script、调 Claude agent。可任选其一。

**D. 每个项目独立 SQLite + 文件目录**
跨项目零耦合。备份 = zip 一个项目目录。导出/导入 = 拖拽一个 zip。

**E. LLM Provider 接口必须抽象**
代码不写死调 OpenAI/Anthropic SDK。任何节点切 provider 只改 NodeConfig，不改业务代码。

---

## 3. 技术选型

### 3.1 选型一览

| 层 | 选型 | 理由 |
|---|---|---|
| 前端框架 | Next.js 14 + React 18 + TypeScript | 教研内部网页足够；服务端渲染对教程嵌入友好；TS 让 schema 类型直接复用 |
| UI 组件库 | shadcn/ui + Tailwind | 体积小、可改、表单组件齐全；不绑死 Material/Antd |
| 表单 | react-hook-form + ajv | ajv 直接吃 JSON Schema，零适配代码 |
| 后端框架 | Python FastAPI | 与 ppt-master / scripts/*.py 同语言，零互操作成本；自动 OpenAPI 文档 |
| 任务队列 | Celery + Redis（或 RQ） | 视频/图片是长任务，必须异步；Celery 生态足够成熟 |
| 数据库 | SQLite（v1） → PostgreSQL（外销云端时） | v1 单机部署最省心；schema 可平迁 |
| LLM SDK | 自封装 LLMProvider 接口 + LiteLLM | LiteLLM 已内置 DeepSeek/Claude/GPT 适配，但我们包一层做超时/重试/降级 |
| 配置 | Pydantic Settings + YAML | workflow.yaml / rules/*.yaml 用 PyYAML 直读，类型靠 Pydantic 校验 |
| 部署 | Docker Compose（v1 内部）→ K8s（外销） | 内部用 docker-compose up 即可 |
| CI/CD | GitHub Actions（或 Gitea） | schema/rules YAML 落库前跑 lint |
| 日志 | structlog + JSON | 错误日志要能被一键打包反馈 |
| 监控 | OpenTelemetry → 内部 Grafana（外销时上） | v1 内部用日志够，外销时上 |

### 3.2 不选什么 + 理由

| 不选 | 原因 |
|---|---|
| Django | ORM 过重，FastAPI 对结构化 schema 友好 |
| Vue / Svelte | React + Next 在 AI 产品赛道生态最厚 |
| MongoDB | 我们已经字段化了，关系型 + JSON 列足够 |
| Kafka | 单租户、长任务，Redis + Celery 够 |
| LangChain | 我们的工作流是 DAG 不是 Agent；LangChain 抽象太重 |
| 自训模型 | v1 不做 fine-tune；飞轮做 few-shot 检索就够 |

---

## 4. 模块拆解

### 4.1 模块依赖图

```
        [config_loader]
              │
        [storage_layer] ───┐
              │            │
        [state_engine]     │
              │            │
        [rule_executor] ───┤
              │            │
        [llm_provider] ────┤
              │            │
        [async_task]       │
              │            │
              └────► [api_layer (FastAPI)]
                          │
              ┌───────────┴───────────┐
              │                       │
        [frontend]               [supervisor_agent]
```

### 4.2 模块清单（按开发顺序）

#### M0: config_loader（配置加载层）
- **职责**：加载并校验 workflow.yaml / rules/*.yaml / schemas/*.json
- **输入**：本目录的所有规范文件
- **输出**：内存中的 WorkflowConfig 单例
- **关键代码**：
  - `WorkflowConfig.load_from_dir("半自动化工作流/")`
  - YAML schema 校验（防写错）
  - 启动时报告冲突（如 rules/index.yaml 引用但文件不存在）
- **估时**：3 人日
- **依赖**：无

#### M1: storage_layer（存储层）
- **职责**：SQLite + 文件系统的统一接口
- **关键 API**：
  - `ProjectStore.create(meta) -> project_id`
  - `ProjectStore.get_node_versions(project_id, node_id)`
  - `ProjectStore.write_version(version) -> version_id`
  - `ProjectStore.set_current(node_id, version_id)`
  - `AssetStore.save_binary(project_id, version_id, file)`
  - `AssetStore.read_binary(asset_id)`
- **SQLite schema**：每个项目独立 db，表结构按 schema.md 第 13.2 节
- **启动检查**：integrity check + 磁盘空间预警
- **估时**：5 人日
- **依赖**：M0

#### M2: state_engine（状态引擎）
- **职责**：读 workflow.yaml，按 transitions 跑状态机
- **关键 API**：
  - `StateEngine.start_node(project_id, node_id)`
  - `StateEngine.transition(project_id, node_id, event)`
  - `StateEngine.cascade_invalidate(project_id, node_id)` — 上游变更触发下游降级
  - `StateEngine.evaluate_skip(project_id, node_id, config)`
- **关键设计**：
  - 状态转换原子化（事务）
  - state_transition_log 表必写
  - 程序崩溃恢复：启动时按日志对账 status
- **估时**：5 人日
- **依赖**：M1

#### M3: rule_executor（规则执行器）
- **职责**：按 trigger_node + trigger_event 索引规则、跑 check、返回结果
- **执行器实现**：
  - `BuiltinExecutor` — Python 内置检查函数（jsonpath / foreach / 简单断言）
  - `ScriptExecutor` — 调用 scripts/*.py，按 exit_code 判定
  - `AgentExecutor` — 调 Claude 跑 supervisor prompt
- **关键 API**：
  - `RuleExecutor.run_rules(project_id, node_id, event) -> RuleResult`
  - `RuleResult.hard_blocks: list, warnings: list, info: list`
- **关键设计**：
  - hard_block 短路（任一命中即停）
  - warning 全跑，UI 一次性展示
  - 规则结果写 rule_result_log 表（飞轮用）
- **估时**：8 人日
- **依赖**：M0, M1, M2

#### M4: llm_provider（LLM 抽象层）
- **职责**：屏蔽不同 provider，统一调用接口
- **关键 API**：
  - `LLMProvider.complete(prompt, schema, params) -> dict`
  - `LLMProvider.with_provider(name)` — 切 provider
  - `LLMProvider.estimate_cost(prompt, params) -> float` — 调用前预估
- **实现细节**：
  - 用 LiteLLM 兜底协议层
  - 顶层包一层做超时/重试/降级
  - 失败自动切 fallback（每节点的 NodeConfig 定义）
  - 输出 JSON 后用 ajv 校验 schema，不通过自动重试 1 次
- **provider 适配的工作量**：
  - DeepSeek: 已有 OpenAI 兼容接口，直接 LiteLLM
  - Claude: 直接 LiteLLM
  - GPT: 直接 LiteLLM
  - 重点是 **prompt 跨 provider 验证**（每个节点都要在 default + fallback 上跑通）
- **估时**：5 人日（不含 prompt 调优）
- **依赖**：M0

#### M5: async_task（异步任务系统）
- **职责**：视频生成、批量出图、PPT 装配等长任务
- **关键 API**：
  - `TaskQueue.submit(task_type, payload) -> task_id`
  - `TaskQueue.get_status(task_id)`
  - `TaskQueue.cancel(task_id)`
- **关键设计**：
  - 6 段视频并发，每段独立任务
  - 失败可单独重试，不重跑成功的
  - 部分失败可接受
  - 用户可关网页，完成后通过 SSE/邮件通知
  - 提交前必跑 R015 三连门禁
- **估时**：6 人日
- **依赖**：M2, M3

#### M6: supervisor_agent（逐页审查智能体）
- **职责**：PPT 第 3 步逐页审查
- **关键 API**：
  - `Supervisor.review_page(page, page_index, prev_summary, applicable_rules) -> ReviewResult`
- **实现细节**：
  - 调 Claude，注入 prompts/supervisor/page_reviewer.md
  - 输入按文档约定结构
  - 输出固定 JSON（passed / hard_blocks / warnings / suggestions）
  - hard_block 触发自动重生（通过 LLM Provider 调用 node_03 生成 prompt）
- **估时**：4 人日
- **依赖**：M3, M4

#### M7: api_layer（FastAPI）
- **职责**：HTTP API + SSE
- **核心 endpoint**：
  - `POST /projects` 创建项目
  - `GET /projects/{id}` 项目元数据
  - `GET /projects/{id}/manifest` 节点状态总览
  - `POST /projects/{id}/nodes/{node_id}/generate` 触发 AI 生成
  - `POST /projects/{id}/nodes/{node_id}/edit` 用户编辑
  - `POST /projects/{id}/nodes/{node_id}/approve` 用户批准
  - `POST /projects/{id}/nodes/{node_id}/redo` 重做
  - `GET /projects/{id}/nodes/{node_id}/versions` 版本历史
  - `POST /projects/{id}/nodes/{node_id}/versions/{vid}/set_current` 回滚
  - `GET /sse/projects/{id}` 状态流（前端用 EventSource 订阅）
  - `POST /projects/{id}/feedback` 反馈
  - `GET /users/{id}/profile` 偏好画像
- **OpenAPI**：FastAPI 自动生成，前端 react-query 配合 openapi-generator 自动生成 client
- **估时**：8 人日
- **依赖**：M0-M6

#### M8: frontend（前端）
- **职责**：网页用户界面
- **核心页面**：
  - `/` 项目列表 + 创建新项目
  - `/projects/[id]` 项目工作台 + 9 步进度
  - `/projects/[id]/nodes/[node_id]` 节点工作区（字段表单 / Markdown 编辑器 / 重做面板）
  - `/projects/[id]/feedback` 反馈弹窗（第二次进入时触发）
  - `/profile` 偏好画像
  - `/projects/[id]/errors` 错误打包反馈
- **组件库**：
  - shadcn/ui
  - 自动表单生成器（JSON Schema → React Hook Form）
  - 异步任务进度条 + SSE 订阅
  - 文件上传（角色字典参考图、对标 PPT）
- **估时**：15 人日
- **依赖**：M7（API 先行）

#### M9: scripts_integration（现有脚本整合）
- **职责**：把现有 ppt-master 和 scripts/*.py 接进来
- **现有脚本**：
  - ppt-master 工具链（SVG 生成、PPTX 导出、QA）
  - workflow_contract_gate.py / videogen_batch_jobs.py / workflow_enforcement_gate.py
  - final_delivery_gate.py
  - audit_student_visible_text.py / audit_six_package_consistency.py / audit_delivery_contracts.py
  - svg_quality_checker.py
- **关键设计**：脚本路径在 rules/index.yaml 的 executors 配置中，不写死代码
- **估时**：6 人日
- **依赖**：M3, M5

#### M10: error_handling（错误处理）
- **职责**：实现 P0 错误处理清单
- **必做**：
  - AI 自动重试（指数退避）
  - 异步任务断点续跑
  - 软删除 + 30 天回收站
  - 全局错误日志 + 一键打包
  - 状态可见 UI（>2 秒必须有进度）
  - provider 自动降级 + UI 透明提示
- **估时**：穿插各模块，估 5 人日
- **依赖**：M2, M5, M7

#### M11: flywheel（飞轮）
- **职责**：偏好画像采集 + few-shot 检索
- **关键 API**：
  - `Flywheel.record_approve(user_id, node_id, version_id)`
  - `Flywheel.record_post_approve_edit(user_id, node_id, diff)`
  - `Flywheel.record_override(user_id, rule_id)`
  - `Flywheel.fetch_samples(user_id, node_id, top_n=3)` — 检索注入 prompt
  - `Flywheel.get_profile(user_id)` — 可视化数据
- **估时**：4 人日
- **依赖**：M1, M3

---

## 5. 三个月里程碑

### 第 1 月：骨架打通

**目标**：能创建项目，能从第 0 步表单走到第 1 步教案的 approve

**完成模块**：M0, M1, M2, M4（最小可用）, M7（最小可用）, M8（最小可用）

**交付物**：
- docker-compose up 能跑起来
- 网页能创建项目、填第 0 步表单
- 触发 DeepSeek 生成教案，按 schema 校验后展示
- 用户能编辑或重做、approve 进入第 2 步
- 状态机正确响应、SQLite 落盘

**验收**：完成最小可爱用例的第 0-1 步

### 第 2 月：PPT 主链路 + 字段化审查

**目标**：教案 → 总装方案 → 页面脚本 → 视觉资产 → PPTX，端到端跑通 PPT 分支

**完成模块**：M3, M5, M6, M9（部分），M11（初版）

**交付物**：
- 第 2、3 步字段化表单 + AI 生成 + 逐页审查智能体 + 编辑/重做
- 第 5A 步异步出图（含失败重试）
- 第 7 步调 ppt-master 生成可编辑 PPTX + PDF + contact sheet
- 飞轮采集 approved / 编辑 / override 数据
- 错误处理 P0 完成

**验收**：能产出一份完整 PPTX，含视觉资产，通过 R001-R032 规则的硬约束

### 第 3 月：视频分支 + 收尾 + 上线

**目标**：导入视频分支完整跑通，最终交付门禁，内部用户试用

**完成模块**：M5（完整）, M9（完整）, M10（完整）, M11（完整）

**交付物**：
- 角色字典模块（多视角 + 服装锁定 + 禁真人）
- 第 4B / 4C / 5B 字段化
- 第 6 步分镜 + 首帧测试机制
- 第 8 步 6 段并发 + 拼接 + 中文男声 TTS（待 TTS 选型）
- 第 9 步最终交付门禁（接现有脚本）
- 反馈弹窗（课件到手 + 第二次使用）
- 偏好画像页面（飞轮可视化）
- 内部 5 位教研员试用 + 收集反馈

**验收**：端到端完成一节"认识周长"这样的真实课题，含 PPT + 视频，通过 final_delivery_gate.py --mode final

---

## 6. 估时汇总

| 模块 | 人日 |
|---|---|
| M0 config_loader | 3 |
| M1 storage_layer | 5 |
| M2 state_engine | 5 |
| M3 rule_executor | 8 |
| M4 llm_provider | 5 |
| M5 async_task | 6 |
| M6 supervisor_agent | 4 |
| M7 api_layer | 8 |
| M8 frontend | 15 |
| M9 scripts_integration | 6 |
| M10 error_handling | 5 |
| M11 flywheel | 4 |
| **小计** | **74 人日** |
| Prompt 跨 provider 调优 | 10 |
| 集成联调 + bug 修复 | 15 |
| QA + 文档 | 8 |
| **总计** | **107 人日 ≈ 5-6 人月** |

**人员配比建议**：
- 全栈 1 名（主导架构、Python 后端）
- 前端 1 名（Next.js + 表单驱动）
- AI 接入 0.5 名（prompt 调优、跨 provider 测试）
- DevOps 0.2 名（部署、监控）

**实际节奏**：3 人团队、3 个月可交付 v1 内部可用版。

---

## 7. 关键设计决策（必须 follow，不要重新发明）

### 7.1 workflow.yaml 是状态机真源

不要在代码里硬编码 9 步流程。状态引擎读 workflow.yaml 动态构建。改流程改 yaml 即可。

### 7.2 不要绕过 schema 校验

LLM 输出必须 ajv 校验通过才能写入 node_versions。校验失败自动重试 1 次。
**前端表单字段也必须由 schema 渲染**，不要手写 form。

### 7.3 hard_block 真的 hard block

R001-R006 这些红线，**不给 UI 任何 override 入口**。
代码层面也要确保用户找不到方式绕过（包括直接编辑 SQLite 文件后再 approve）。

### 7.4 上游变更下游全降级

不要做"智能影响分析"。v1 就是简单粗暴：上游 current 切换 → 下游 approved → needs_review。

### 7.5 异步任务一定要持久化

视频生成 5 分钟，用户关浏览器是常态。任务状态必须落 SQLite，重启可恢复。

### 7.6 错误必须被产品消化

不要把 stack trace 抛给用户。每个 try/catch 都要想清楚"用户看到什么、能做什么、有没有损失"。

### 7.7 LLM Provider 抽象层

任何业务代码不要直接 import openai / anthropic。统一走 LLMProvider 接口。

### 7.8 不要在 v1 做的

- 多人协作 / 节点锁
- diff 预览面板
- 影响范围智能分析
- 跨项目复用
- fine-tune
- 智能体对话流 UI

参见 v1_产品决策记录.md 第 17 章完整清单。

---

## 8. 风险点和兜底

### R-01 LLM 输出 JSON 格式不稳定（高）
- 现象：DeepSeek 在长 prompt 下偶尔输出 markdown 包装的 JSON
- 兜底：解析器加 markdown 剥离 + ajv 校验失败自动重试 1 次 + 仍失败切 fallback provider

### R-02 视频生成 API 不稳定（高）
- 现象：omni_flash 排队、超时、内容审核驳回
- 兜底：6 段并发 + 失败单独重试 + 首帧测试机制（先出几毛钱的图，确认 prompt 再调几块钱的视频）+ 部分失败可接受

### R-03 跨 provider prompt 质量不一致（中）
- 现象：DeepSeek 跑通的 prompt 切到 GPT 质量崩
- 兜底：每个节点必须在 default + fallback 两个 provider 都跑通后才合并
- 责任：AI 接入 0.5 人专职 prompt 调优

### R-04 ppt-master 集成复杂度（中）
- 现象：现有 ppt-master 是个独立工具链，输入/输出契约不清
- 兜底：先按"调用 CLI + 读输出文件"对接，不深度集成。ppt-master 内部演进对我们透明。

### R-05 中文 TTS 选型未定（中）
- 影响：第 8 步无法跑通
- 兜底：第 1 月内必须选型完成。候选：阿里云 / 火山引擎 / 腾讯云语音 / Azure TTS
- 决策标准：男声音质 + SSML 控制 + 价格 + 中国大陆可用性

### R-06 SQLite 并发写（低）
- 现象：单项目多标签同时编辑可能锁库
- 兜底：v1 检测到第二标签提示"建议关闭"。不做悲观锁。

### R-07 教研员对 13 字段嫌多（中）
- 现象：填表负担大
- 兜底：默认值要尽量填好，AI 一键生成所有字段，用户只看不爽的格改。**绝对不能让用户从零开始填 13 个空字段**。

### R-08 飞轮冷启动（低）
- 现象：第一个项目没有历史样本可注入
- 兜底：fallback 到"按 schema 默认生成"，不报错

### R-09 磁盘空间（低）
- 现象：视频/图片堆积撑满硬盘
- 兜底：启动检查 + 阈值预警 + 用户可一键归档老项目

### R-10 现有 9 个门禁脚本路径硬编码（中）
- 现象：scripts/*.py 可能引用了具体 Windows 路径
- 兜底：M9 阶段第一件事是审一遍所有脚本，把硬编码路径改成参数；改不动的提需求给 scripts 维护方

---

## 9. 开发流程

### 9.1 代码仓库

建议结构：
```
ai-youjiao-product/
  apps/
    web/                  # Next.js
    api/                  # FastAPI
  packages/
    workflow-config/      # workflow.yaml + schemas + rules（这是产品的"宪法"）
    prompts/              # prompt 模板
  scripts/                # 现有 ppt-master / 门禁脚本
  docker-compose.yml
```

**`packages/workflow-config/`** 直接软链到本目录 `半自动化工作流/`，或 git submodule。
**workflow.yaml 改动必须走 PR**，需要产品 + 教学法负责人 review。

### 9.2 CI 检查

- workflow.yaml 用 yaml schema 校验
- rules/*.yaml 用 yaml schema 校验
- schemas/*.json 用 metaschema 校验
- rules/index.yaml 中引用的文件必须存在
- prompts 中变量必须能 resolve（{{xxx}} 不能孤立）

### 9.3 测试

- 单元测试：每模块 ≥ 70% 覆盖
- 集成测试：跑通 1-2 个完整 e2e 用例
- 不做 100% 覆盖（v1 阶段时间不够）

### 9.4 部署

- v1 内部：Docker Compose 一台机器
- 用户在浏览器访问 `http://内网域名`
- SQLite 落本机文件系统，每天 rsync 备份到 NAS

---

## 10. 验收清单

### v1 上线必过的用例

**用例 1：最小可爱**
> 创建项目"认识周长"→ 填表单 → 第 1 步教案 → 编辑 → approve → 第 2 步 → ... → 第 9 步交付 → 拿到 PPTX + 视频 + 反馈弹窗

**用例 2：回头修复**
> 走到第 4B 步时回去改第 1 步教案 → 第 2、3、4B 步下游 approved 全部正确变红 → 逐个重审走完 → 最终交付

**用例 3：异常容错**
> 6 段视频第 3 段 omni_flash 超时 → 自动重试 → 仍失败 → UI 显示其余 5 段已完成、第 3 段可单独重试 → 用户手动重试成功 → 拼接 → 通过最终门禁

**用例 4：飞轮初见**
> 同一用户做完两个项目 → 第三个项目第 1 步教案生成时，prompt 自动注入前两次的 approved 片段 → 偏好画像页面显示风格分布

**用例 5：合规守护**
> 用户在 character_dict 试图把 banned_keywords 改空 → 保存被拒（R004） → 用户在 storyboard model_prompt 删掉"中文男声"句 → 保存被拒（R043）

### 验收时一定要查的

- [ ] 所有红线规则在代码中不可绕过
- [ ] 错误处理 P0 清单完成
- [ ] schema 校验在前端 + LLM 输出 + 数据库写入三层都有
- [ ] workflow.yaml 改一行能立刻生效
- [ ] 异步任务可以关浏览器再回来
- [ ] 整个项目目录 zip 后能在另一台机器还原

---

## 11. 不在 v1 范围（但开发要为其留口子）

| 项 | 留什么口子 |
|---|---|
| 多人协作 | node_versions 加 `owner_user_id` 字段 |
| 云端 SaaS | 存储层接口抽象（不假设 SQLite） |
| fine-tune | 飞轮数据从 v1 就完整采集 |
| 对话流智能体 | LLM Provider 接口里加 `chat` 方法 |
| 教程内嵌 | 前端组件预留 `<TutorialHint />` 槽位 |
| 紧急模式 | project_meta 已有 deadline_at 字段 |
| 跨项目复用 | assets 表加 `is_reusable` 字段 |
| 视频深度字段化 | storyboard schema 加 `extensions` JSON 字段 |

---

## 12. 沟通

- **产品决策**：参见 `v1_产品决策记录.md`，有疑问找产品
- **规范变更**：改 `半自动化工作流/` 任何文件走 PR
- **教学法判断**：找教学法负责人（待定）
- **API 选型**：找产品 + 全栈共同决策

---

## 13. 变更记录

| 日期 | 改动 | 备注 |
|---|---|---|
| 2026-06-19 | 初版 | 交付开发团队 |
