# 山海教育 ProMax 工作台 —— 工作交接日志

> 单一共享工作日志，所有 Agent 在开始工作前必读，完成后追加新段落。

## 项目概览

- **品牌**：山海教育（产品全称：山海教育 - AI幼教ProMax可视化工作台）
- **第一阶段**：只做前端骨架与视觉皮肉，不接真实 API / 模型 / 外部资源，全部 mock 本地。
- **单页架构**：受沙箱限制，用户只能看到 `/` 路由。整个工作台用 Zustand 管理"屏幕视图"（dashboard / new-project / project / config / logs / scripts），在 `src/app/page.tsx` 渲染 `<AppShell/>`，AppShell 按登录态与 screen 状态切换不同 Screen 组件。
- **演示账号**：`admin / shanhai2026`（管理员）；`teacher / shanhai2026`（教师，隐藏配置/日志/脚本）。

## 设计系统（必须严格遵守）

### 色彩
- 背景 `--background: #f6f5f1`（暖纸白，克制不刺眼）
- 卡片 `--card: #ffffff`
- 主文字 `--foreground: #23272e`；次文字 `--muted-foreground: #6b727c`
- 边框 `--border: #e4e1d9`（暖浅灰）
- **主色 `--primary: #2d4356`**（深青灰 / 低饱和，非强蓝）→ 仅用于主按钮、当前状态、聚焦环
- **古铜金 `--bronze: #9c7c4e`**（点缀色，仅用于品牌星标/重要强调，不大面积使用）
- 状态色（低饱和）：`--success #4f6b59` / `--warning #9a7340` / `--info #45627a` / `--destructive #9a4747`
- 状态映射见 `src/components/common/StatusBadge.tsx`：`StatusBadge`（阶段状态）、`ProjectStatusBadge`（项目状态）、`ToneBadge`（自定义）

### 字体层级（仅 3 级）
- `.t-title` 页面标题 1.625rem / 600
- `.t-module` 模块标题 1.0625rem / 600
- `.t-body` 正文 0.875rem / 400
- 辅助 `.t-caption` 0.75rem、`.t-overline` 0.6875rem 大写带字距（用于分组小标题）
- 纯系统字体栈，零远程依赖。

### 视觉规范
- 留白充足，信息密度低；卡片少，边框轻，阴影用 `.shadow-soft` / `.shadow-lift`
- **禁止**：Emoji、大面积渐变、卡片套卡片、强蓝主色、花哨插画、外部 CDN 字体/图标/图片
- 滚动条用 `.scroll-fine`
- 品牌背景纹理可用 `.bg-topo`（极淡等高线）或 `.bg-grid`

### 响应式断点
- 390px：单列、侧栏收起为抽屉、表单单列、表格转卡片、操作按钮不挤压、禁止横向溢出
- 768px：两列以内
- 1280px：标准工作台（侧栏 256px + 主体）
- 1440px：增加留白，不铺满

### 布局骨架
- `src/components/layout/AppShell.tsx`：登录态判断 → LoginScreen / 工作台（Sidebar + TopBar + main + sticky footer）
- `Sidebar.tsx`：桌面固定 256px；移动端用 `Sheet` 抽屉
- `TopBar.tsx`：面包屑 + 通知 + 用户菜单（切换角色/退出）
- footer 必须粘底（`mt-auto`），内容超长时被自然推下

## 数据与状态

- 类型：`src/lib/types.ts`
- 14 节点工作流定义：`src/lib/workflow.ts`（`STAGE_DEFS`、状态标签 `STAGE_STATUS_LABEL`、状态色 `STAGE_STATUS_TONE`、`nextStageKey`、`makeEmptyStages`）
- mock 数据：`src/lib/mock-data.ts`（3 个项目 demo-001/002/003、每项目 14 节点完整数据、9 套视频方案 `MOCK_VIDEO_PLANS`、教材解析 `MOCK_TEXTBOOK_PARSE`、PPT 方案、系统状态 `MOCK_SYSTEM_STATUS`、待处理 `MOCK_PENDING_ITEMS`、脚本 `MOCK_SCRIPTS`、日志 `MOCK_STAGE_LOGS`）
- Zustand store：`src/lib/store.ts`
  - `useAppStore`：user / screen / activeProjectId / projects / stagesByProject / videoPlansByProject / draft
  - 动作：`login` `logout` `switchRole` `go(screen)` `openProject(id)` `approveStage` `rejectStage` `runStage`(模拟1.4s异步) `saveStageInput` `acceptVideoPlan` `setDraft` `resetDraft` `commitDraftToProject`
  - 草稿默认值 `EMPTY_DRAFT`、登录初始化 `initAuth()`

## 已完成

- [x] 品牌资产：`public/logo.png`（上传logo）、`public/favicon.svg`（自绘山海书SVG标记）
- [x] `src/components/brand/Logo.tsx`：`LogoMark`（inline SVG 山峰+海浪+星）、`Logo`（标记+字标）、`LogoWordmark`
- [x] `src/app/globals.css`：完整设计 token（色彩/字体层级/状态色/工具类）
- [x] `src/app/layout.tsx`：品牌元数据、favicon、纯系统字体、Toaster
- [x] `src/lib/types.ts` `workflow.ts` `mock-data.ts` `store.ts`
- [x] `src/components/common/StatusBadge.tsx` `StateViews.tsx`
- [x] `src/components/layout/Sidebar.tsx` `TopBar.tsx` `AppShell.tsx`

## 进行中 / 待办

- [ ] **Task 3**：LoginScreen + DashboardScreen（由主代理完成，作为视觉语言参考）
- [ ] **Task 4a**（子代理A）：NewProjectScreen 5 步工作流
- [ ] **Task 4b**（子代理B）：ProjectWorkspaceScreen 指挥台
- [ ] **Task 4c**（子代理C）：ConfigScreen + LogsScreen + ScriptsScreen
- [ ] **Task 5**：agent-browser 端到端 QA + 修复
- [ ] **Task 6**：创建 15 分钟 webDevReview cron

---
Task ID: 1
Agent: 主代理
Task: 项目地基 —— 品牌资产、设计系统、类型/mock/store、布局骨架

Work Log:
- 读取三份需求文档与 logo，用 VLM 分析品牌气质（深蓝/湖蓝/金），按文档"主色不要太蓝"调整为深青灰+古铜金方案
- 复制 logo 到 public/logo.png；自绘 inline SVG 品牌 favicon 与 LogoMark 组件
- 重写 globals.css：暖纸白底 + 深青灰主色 + 低饱和状态色 + 3 级字体层级 + 工具类
- 重写 layout.tsx：纯系统字体、山海教育品牌元数据、favicon
- 建立 types.ts / workflow.ts（14节点）/ mock-data.ts（3项目+9视频方案+教材解析+PPT+日志+系统状态+待处理）/ store.ts（Zustand 全量状态与动作）
- 建立 common 组件：StatusBadge / ProjectStatusBadge / ToneBadge / EmptyState / LoadingState / ErrorState
- 建立布局骨架：Sidebar（含系统轻状态卡片）/ TopBar（面包屑+用户菜单）/ AppShell（登录态+移动端抽屉+sticky footer）

Stage Summary:
- 设计系统已定型，所有后续 Screen 必须复用上述 token、字体层级类、StatusBadge、common 组件、shadcn/ui
- 单页视图路由通过 `useAppStore` 的 `screen` 字段切换；项目工作区需先 `openProject(id)`
- mock 数据全部就绪，子代理直接 import 使用，勿再造数据

---
Task ID: 3
Agent: 主代理
Task: LoginScreen + DashboardScreen，建立视觉语言参考

Work Log:
- 构建 LoginScreen：左深青灰品牌叙事区（Logo + 标语 + 山海线条SVG装饰 + 数据统计）+ 右登录表单；演示账号快捷填充；移动端单列居中品牌头
- 构建 DashboardScreen：4 区块（继续工作Hero / 项目概览 / 待处理事项 / 系统轻状态）；ContinueWorkHero 含下一步动作卡片 + 阶段迷你轨；ProjectCard 可复用卡片；待处理事项列表带优先级；系统轻状态4卡片 + 服务状态（仅管理员）
- 创建可复用 ProjectCard / ProjectCardMinimal
- VLM 评审通过：高级克制大气、布局清晰、留白适中

Stage Summary:
- 视觉语言已定型，子代理必须严格对齐：SectionHeader（编号+标题+描述）、Card 边框 border-border、字体层级类 t-title/t-module/t-body/t-caption/t-overline、StatusBadge/ToneBadge、留白充足
- 服务器守护技巧（重要）：沙箱会在 bash 调用结束时清理后台进程，必须用**双 fork 守护进程**启动：`( setsid node node_modules/.bin/next dev -p 3000 > dev.log 2>&1 < /dev/null & ) &`，普通 `nohup & disown` 无效
- agent-browser 必须通过网关端口 81 访问（`http://localhost:81/`），不能直连 3000；curl 可直连 3000 验证
- 已验证：登录 admin/shanhai2026 → dashboard 4 区块正常渲染

---
Task ID: 4a
Agent: full-stack-developer
Task: NewProjectScreen 5步工作流向导

Work Log:
- 读 worklog / 需求 5.3+7+8 / DashboardScreen+LoginScreen+Sidebar / types+store+workflow+mock-data，对齐视觉语言与数据契约
- 整体覆盖 `src/components/screens/NewProjectScreen.tsx`（约 760 行）：页头 + Stepper + 5 张 StepCard + 底部操作栏
- 状态设计：`currentStep`（展开步骤）+ `maxStep`（最远到达）+ `parseConfirmed`（解析确认）本地 state；草稿字段绑定 store `draft`/`setDraft`
- Stepper：横向 5 圆圈，已完成 ✓、当前实心 primary、未开始浅灰；移动端 `overflow-x-auto scroll-fine`；点击已完成步骤可回看，未开始锁定
- StepCard：当前步骤展开表单，其他折叠为摘要行（done 可点切换）；状态徽标「进行中/已完成/未开始」
- Step1 基本信息：项目名 Input + 学科/年级/教材版本/册次/课型 5 个 Select（h-11）
- Step2 教材上传与内容（整体模块）：拖拽样式 label + hidden file input（记录文件名）+ Textarea + 「开始解析」→ 1.2s 模拟解析进度 → 解析结果预览（学科/年级/版本/册次/课题/核心知识点/教学目标摘要/教学重点/教学难点）+ 「确认解析结果」「重新解析」「重置」
- Step3 视频设计导入（克制，不抢视觉）：视频用途 Select + 预计时长 Select + 5 Checkbox 多选 + 数量/主题/受众 Input + 创意要求 Textarea + 术语提示「课程锚点」「课堂落点问题」
- Step4 PPT 配置：风格 Select + 页数 Input + 结构 Input
- Step5 路径与约束：输出路径 Input + 安全模式 Switch + 约束说明 Textarea + Separator + 配置摘要（12 项前 4 步关键信息回显）+ 「创建项目」主按钮
- 底部操作栏：保存草稿 / 上一步 / 下一步（step5 替换为「创建项目」）+ 当前步骤就绪状态
- 创建项目流程：校验 5 步全通过 → `commitDraftToProject()` 拿 id → toast 成功 → 220ms 后 `openProject(id)` 进工作区
- 严格复用设计 token：`.t-title/.t-module/.t-body/.t-caption/.t-overline`、Card `border-border bg-card`、Input `h-11 bg-card`、StatusBadge 色调；无 Emoji、无渐变、无卡片套卡片、无强蓝

Stage Summary:
- 产出文件：`src/components/screens/NewProjectScreen.tsx`（唯一修改）
- Lint：`npx eslint src/components/screens/NewProjectScreen.tsx` 0 错 0 警（项目整体 `bun run lint` 仅有 LoginScreen 1 个 pre-existing 警告，非本任务引入）
- agent-browser 端到端验证通过：登录 → 新建项目 → 填名 → 解析教材 → 确认 → 视频/PPT/路径配置 → 创建项目 → 自动进入项目工作区（面包屑显示新项目名）；`agent-browser errors` 空；dev.log 无运行时错误
- 截图：`/home/z/my-project/download/03-newproject.png`（step5 配置摘要+创建按钮）+ step1/step2-parsed/step3/step4 过程截图
- 关键决策：parseConfirmed 用本地 state（draft 类型无此字段）；底部操作栏非 sticky（避免与全局 sticky footer 重叠）；Stepper 移动端横向滚动；StepCard 用 div+border 渲染解析结果/配置摘要（避免卡片套卡片）

---
Task ID: 4b
Agent: full-stack-developer
Task: ProjectWorkspaceScreen 指挥台

Work Log:
- 读 worklog / 需求 5.4+6+9 / 重建指令项目工作区要求 / DashboardScreen+ProjectCard / types+workflow+store+mock-data+StatusBadge+StateViews，对齐视觉语言与数据契约
- 整体覆盖 `src/components/screens/ProjectWorkspaceScreen.tsx`（约 870 行，唯一修改文件）：顶部 Header + 中部 WorkflowRail + 详情区 5 Tab + 视频方案卡片 + 底部 StageActions
- 组件结构拆分为外层 `ProjectWorkspaceScreen`（查 project、空态分流）+ 内层 `ProjectWorkspace`（`key={project.id}` 重挂载，状态自然重置）；内层内聚所有子组件：WorkspaceHeader / WorkflowRail / InputTab / RunTab / ResultTab / EvidenceTab / LogsTab / VideoPlanGrid / VideoPlanCard / TermRow / StageActions
- 关键设计：**零 useEffect** —— 通过 `key={project.id}` 让 React 在切换项目时重挂载内层；切换节点/确认通过/进入下一步都用事件处理器内同步 `setSelectedKey + setTab + setInputDraft`，避免 `react-hooks/set-state-in-effect` 错误（Task 4a 中 LoginScreen 触发的同一规则）
- 顶部 Header：返回按钮 + 项目名（t-title）+ 学科/年级/教材版本+册次/课型 meta 行 + ProjectStatusBadge；下方 3 列 grid：当前阶段 / 总进度（数字+Progress）/ 下一步动作
- WorkflowRail：14 节点横向排列（`overflow-x-auto scroll-fine` + `min-w-max`），每节点 88×88px button，纵向堆叠「编号圆点 + 短标题 + 分支 overline」；状态色映射：已通过=success+✓、运行中=primary+Loader2 spin+脉冲点、失败/阻塞=destructive+AlertTriangle、待确认/待输入/就绪=warning、未开始=muted；选中态 `border-primary bg-primary/[0.04] shadow-soft`；节点间细线连接器（已通过段 bg-success/50，未完成段 bg-border）；分支标签着色（common=灰、video=info、ppt=bronze）保持克制
- 详情区 5 Tab（TabsList 横向 `overflow-x-auto scroll-fine`）：
  - 输入：Textarea 绑定 inputDraft + 待输入时 warning 提示 + 保存输入按钮
  - 运行：StatusBadge + 状态文案 + 耗时 + 开始运行/重新生成按钮；运行中显示 LoadingState
  - 结果：普通节点显示 result 文本（whitespace-pre-wrap）；**video-script 节点特殊**：渲染 VideoPlanGrid 9 张方案卡片
  - 证据：文件列表（FileText 图标 + 文件名）
  - 日志：`max-h-96 overflow-y-auto scroll-fine`，时间+level 图标+消息；level 色 info=muted、warn=warning、error=destructive、success=success
- VideoPlanCard（克制设计）：header row（#rank 排序 + 分数 + 类型 + 已采纳 badge）+ t-module 标题 + Separator + 5 个 TermRow（吸睛点/课程锚点/课堂落点问题/不提前讲解的内容/接入教案的位置）+ Separator + 推荐理由 + 底部 actions（采纳/编辑/对比）；rank===1 加"推荐"角标（bronze）；采纳后卡片 `border-primary/40 bg-primary/[0.02] ring-1 ring-primary/20` + 按钮变"已采纳" disabled；网格 `grid lg:grid-cols-2`
- StageActions（Card 内底部，border-t bg-muted/20）：左组 保存+重新生成 / 右组 退回修改+进入下一步+确认通过（primary）；按 status 启用/禁用：not_started 仅保存可用、running 全部禁用且显示 spin、pending_confirm/ready 全部可用、approved 确认通过禁用、failed/blocked 确认通过禁用
- 状态流转实测：demo-001 video-script（pending_confirm）→ 点"确认通过" → approveStage → 节点变 ✓ + selectedKey 切到 video-assets + tab 重置到输入 + 进度 42%→36%（5/14 重算）+ 下一步动作变"进入「视频资产」" + 确认通过/进入下一步按钮 disabled（新阶段 input_required）
- demo-003 failed 验证：当前阶段视频生成（failed）→ 节点轨第 8 节点显示 AlertTriangle+destructive + 详情区 StatusBadge "失败" + 日志 Tab 显示 4 条日志（含 2 条 error）+ 确认通过 disabled、进入下一步 enabled
- 采纳方案实测：demo-001 video-script 结果 Tab 点第二张卡片"采纳" → 卡片变高亮（border-primary + ring）+ 按钮变"已采纳" disabled + toast"已采纳该方案"
- 严格复用设计 token：`.t-title/.t-module/.t-body/.t-caption/.t-overline`、Card `border-border bg-card shadow-soft`、StatusBadge/ToneBadge 色调；无 Emoji、无渐变、无卡片套卡片（详情 Tab 内容直接在 Card 内，VideoPlanCard 是同级 grid 不算套卡片）、无强蓝主色
- 响应式：容器 `max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8`；WorkflowRail `overflow-x-auto scroll-fine`（移动端横向滚动 14 节点）；TabsList `overflow-x-auto`；按钮组 `flex flex-wrap`；Header 3 列 `sm:grid-cols-3`；视频方案 `lg:grid-cols-2`

Stage Summary:
- 产出文件：`src/components/screens/ProjectWorkspaceScreen.tsx`（唯一修改，约 870 行）
- Lint：`bun run lint` 0 错 0 警（仅 LoginScreen 1 个 pre-existing `react-hooks/set-state-in-effect` 错误，非本任务引入）
- agent-browser 端到端验证通过：登录 admin/shanhai2026 → 首页点"进入工作区"（demo-001）→ 顶部信息完整（项目名/学科年级版本册次课型/状态徽章/当前阶段/总进度/下一步动作/返回按钮）→ 14 节点轨正确渲染（公共/视频线/PPT线 分支标签，已通过✓，当前 5 高亮）→ 5 Tab 切换正常 → video-script 结果 Tab 显示 9 张方案卡片（推荐角标+全部字段+采纳/编辑/对比按钮）→ 点"确认通过"状态流转生效（节点变✓、切换到 video-assets、进度更新、按钮启用状态正确）→ 切换 demo-003 验证 failed 节点（danger 色 AlertTriangle + 失败徽章 + 错误日志 + 确认通过 disabled）
- `agent-browser errors` 空；dev.log 无运行时错误
- 截图：`/home/z/my-project/download/04-workspace.png`（demo-001 工作区顶部+节点轨+输入 Tab）+ `/home/z/my-project/download/04b-video-plans.png`（video-script 结果 Tab 9 张方案卡片）
- 关键决策：(1) `key={project.id}` 重挂载避免 effect 同步状态，绕过 react-hooks/set-state-in-effect 规则；(2) 状态流转用事件处理器内同步 `setSelectedKey+setTab+setInputDraft`，零 useEffect；(3) WorkflowRail 横向 `overflow-x-auto` 而非纵向（14 节点纵向太长，指挥台感更强）；(4) StageActions 放在 Card 内底部（border-t bg-muted/20）而非独立 sticky（避免与全局 sticky footer 冲突，Task 4a 同款决策）；(5) VideoPlanCard 用 TermRow（label w-32 + value flex-1）而非 table，更克制；(6) 推荐角标用 bronze 色（品牌点缀色），采纳后用 primary 色高亮

---
Task ID: 4c
Agent: full-stack-developer
Task: ConfigScreen + LogsScreen + ScriptsScreen

Work Log:
- 读 worklog（Task 1/3/4a/4b 视觉语言 + 设计系统 + 守护进程技巧 + agent-browser 网关端口 81）/ 需求 5.5+5.6 / DashboardScreen 参考实现 / types+mock-data+store+workflow+StatusBadge+StateViews，对齐数据契约与视觉语言
- 整体覆盖 `src/components/screens/ConfigScreen.tsx`（约 460 行）：页头 + 4 个 SectionHeader 分区
  - 01 模型配置：6 行 Table（教材解析/视频剧本/视频生成/PPT方案/PPTX生成/教案完善模型），状态 ToneBadge（就绪 success / 占位 warning / 未配置 neutral）
  - 02 安全模式：Switch + 当前模式说明卡片（开启/关闭不同文案）+ toast 反馈
  - 03 全局参数：4 个表单字段（并发数 Input number + 超时 Select + 重试次数 Input number + 输出格式 Select），h-11 bg-card，参数说明 caption，保存按钮 toast
  - 04 密钥状态：3 行 Table（API密钥/存储密钥/模型密钥），凭据用 `••••••••••••3a9f` 遮挡，眼睛图标可切换显示（演示用，显示 `shanhai_demo_key`），状态 ToneBadge（已配置 success / 未配置 neutral），最后更新时间
- 整体覆盖 `src/components/screens/LogsScreen.tsx`（约 380 行）：页头 + 筛选器卡片 + 日志列表卡片
  - 顶部筛选 4 字段：阶段 Select（STAGE_DEFS 14 项 title）+ 级别 Select（全部/info/warn/error/success）+ 项目 Select（来自 projects）+ 搜索 Input（带 Search 图标）；网格 lg:grid-cols-4，移动端单列堆叠
  - 筛选结果计数 + 重置筛选按钮
  - 日志列表：桌面用 Table（时间/级别/项目·阶段/消息 4 列），移动端转卡片列表（级别色 + 时间 + 消息 + 项目·阶段）；级别用色 info=neutral灰、warn=warning、error=destructive、success=success，配 Info/AlertTriangle/XCircle/CheckCircle2 图标
  - 右上角操作：刷新（toast 已刷新）+ 导出（toast 演示版暂不支持导出，仅管理员可见）
  - 局部 buildLogRows 把 MOCK_STAGE_LOGS 扩展为带项目/阶段信息：info/success/warn 归 demo-001 视频剧本，error 归 demo-003 视频生成
- 整体覆盖 `src/components/screens/ScriptsScreen.tsx`（约 290 行）：页头 + 脚本列表卡片
  - 桌面 Table 7 列：脚本名/类型 ToneBadge/状态 ToneBadge/耗时/最后运行/备注/操作（详情+重跑）；移动端转卡片（脚本名 + 类型/状态徽章 + 耗时/最后运行 grid + 备注 + 详情/重跑按钮）
  - 类型 ToneBadge：解析 info、生成 brand、归档 neutral；状态 ToneBadge：成功 success、失败 danger、待运行 warning
  - 操作：详情（toast 查看脚本名详情，演示版暂不提供脚本详情页）+ 重跑（toast 已请求重跑，待运行状态 disabled）
  - 底部说明演示版脚本均为 mock 记录
- 权限收敛：ConfigScreen 非 admin 仅展示安全模式 + EmptyState「教师视角不展示系统配置」；ScriptsScreen 非 admin 直接 EmptyState；LogsScreen 非 admin 可访问但隐藏导出按钮（业务相关，教师可查日志）。Sidebar 已对 adminOnly 项过滤，但 switchRole 时仍可能停留在该屏，因此屏内再次判定 user.role 兜底
- 严格复用设计 token：容器 `mx-auto w-full max-w-[1440px] px-4 py-6 lg:px-8 lg:py-8`、SectionHeader（编号 bronze + t-module + t-caption 描述，复用 DashboardScreen 同款风格）、Card `border-border bg-card shadow-soft`、字体层级 `.t-title/.t-module/.t-body/.t-caption/.t-overline`；无 Emoji、无渐变、无卡片套卡片、无强蓝主色

Stage Summary:
- 产出文件：`src/components/screens/ConfigScreen.tsx`、`LogsScreen.tsx`、`ScriptsScreen.tsx`（仅这 3 个文件，无其他改动）
- Lint：`npx eslint` 对 3 个文件 0 错 0 警；项目整体 `bun run lint` 仍仅 LoginScreen 1 个 pre-existing `react-hooks/set-state-in-effect` 错误（非本任务引入）
- agent-browser 端到端验证通过：
  - admin 视角：配置中心 → 4 个 Section 完整渲染（6 模型行 / Switch + 模式说明 / 4 全局参数 / 3 密钥行）→ 日志 → 4 筛选器 + 7 条日志表格 + 刷新/导出按钮 → 脚本 → 7 列表格 + 5 脚本行 + 详情/重跑按钮（待运行行重跑 disabled）
  - 教师视角（switchRole 兜底）：配置中心 → 仅安全模式 Switch + EmptyState 教师视角不展示系统配置 → 日志 → 4 筛选器 + 7 条日志（无导出按钮）→ 脚本 → EmptyState 教师视角不展示脚本记录
  - 交互验证：导出按钮触发 toast「演示版暂不支持导出」、级别筛选选 error → 共 1 条·全部 7 条（视频生成失败那条）、搜索框输「关键帧」→ 共 1 条、详情按钮触发 toast「查看「教材解析脚本」详情 / 演示版暂不提供脚本详情页」
  - 响应式：390px viewport 配置中心/日志/脚本均单列堆叠不溢出，表格转卡片列表（logs/scripts 均验证）
  - `agent-browser errors` 空；`agent-browser console` 仅 Fast Refresh / HMR 日志；dev.log 仅 200 响应无运行时错误
- 截图：`/home/z/my-project/download/05-config.png`（admin 配置中心 4 区块）+ `05b-config-teacher.png`（教师 EmptyState）+ `05c-config-mobile.png`（390px 移动端）+ `06-logs.png`（admin 日志表格）+ `06b-logs-teacher.png`（教师日志无导出）+ `06c-logs-mobile.png`（移动端卡片）+ `07-scripts.png`（admin 脚本表格）+ `07b-scripts-teacher.png`（教师 EmptyState）
- 关键决策：(1) 配置中心模型/密钥用 Table（信息密度高，行列清晰），全局参数用 Grid 双列卡片（表单字段不宜用 Table）；(2) 密钥遮挡用 `••••••••3a9f` 末 4 位明文 + Eye/EyeOff 切换显示演示密钥，不展示任何真实凭据；(3) LogsScreen 把 MOCK_STAGE_LOGS 在组件内 buildLogRows 扩展项目/阶段信息（不动 mock-data.ts），按 level === 'error' 归到 demo-003 视频生成失败，其余归 demo-001 视频剧本；(4) LogsScreen 教师可访问但简化（隐藏导出按钮），符合「日志不算系统底层配置」的需求；(5) ScriptsScreen 待运行行重跑按钮 disabled，符合「待运行」语义；(6) 桌面 Table + 移动 ul 卡片双渲染（hidden md:block / md:hidden），避免横向滚动条

---
Task ID: 5
Agent: 主代理
Task: 端到端 QA + lint 清理 + 响应式验证

Work Log:
- 修复 LoginScreen 的 react-hooks/set-state-in-effect lint 错误（移除 effect 内 setError，改为 onChange 内 clearError）
- bun run lint 全绿（0 错 0 警）
- agent-browser 全流程验证：登录→首页4区块→项目工作区(14节点轨/5Tab/9视频方案/采纳/确认通过状态流转)→新建项目5步工作流(基本信息→教材解析模拟→视频设计→PPT→路径约束→创建项目进入工作区)→配置中心(4模块)→日志(筛选)→脚本(表格)
- 教师角色验证：侧栏隐藏配置/日志/脚本，配置中心显示 EmptyState
- 响应式验证：390px / 1280px / 1440px 均无横向溢出；移动端侧栏抽屉正常打开/关闭
- sticky footer 验证：内容超长时自然下推，短页面粘底
- 禁忌词扫描：src/ 内无 Z.ai Code Scaffold / nextjs_tailwind_shadcn_ts / AI-youjiao-promax
- Emoji 扫描：src/ 内无 Emoji
- VLM 评审：登录页+首页"高级克制大气"；工作区+新建项目"指挥台特征明显，信息层级清晰，留白充足"
- dev.log 无运行时错误，全 200

Stage Summary:
- 第一阶段交付完成：可独立运行的 mock 工作台，全流程可演示，无外部依赖
- 服务器守护：必须用双 fork `( setsid node node_modules/.bin/next dev -p 3000 > dev.log 2>&1 < /dev/null & ) &`，普通 nohup 会被沙箱清理
- 网关：用户预览走 http://localhost:81（Caddy 代理到 3000）；agent-browser 也走 81
- 截图归档：/home/z/my-project/download/qa-*.png 共 13 张覆盖全部场景
- 待办：创建 15 分钟 webDevReview cron 持续优化

## 当前项目状态
- 稳定可演示。所有验收标准已满足（见需求文档第12节）。
- 下阶段可做：接真实 API、真实模型调用、真实文件解析；增加更多交互细节；暗色主题完善。

## 未解决问题/风险
- 服务器进程在沙箱中需双 fork 守护，若被清理需重启（cron 会处理）
- next-themes ThemeProvider 未接入（sonner 的 useTheme 用默认值，可工作但暗色切换未实现）—— 第一阶段聚焦亮色，可接受
- 视频方案"编辑/对比"按钮为 toast 占位（第一阶段要求，非缺陷）

---
Task ID: 6 (cron rev1)
Agent: 主代理 (webDevReview 巡检)
Task: 持续优化第1轮 —— QA巡检 + 暗色主题 + 命令面板 + 视频方案对比 + 证据预览

## 项目当前状态判断
- 服务器稳定运行（双fork守护，1440/390px 均无溢出，dev.log 无错误）
- 第一阶段6页面全部可演示，lint 全绿
- 本轮无 bug 需修复，进入新功能开发

## 本轮已完成的修改

### 1. 暗色主题（next-themes ThemeProvider）
- 新增 `src/components/theme/ThemeProvider.tsx`：包裹 next-themes，attribute="class" defaultTheme="light" enableSystem
- 新增 `src/components/theme/ThemeToggle.tsx`：DropdownMenu 切换浅色/深色/跟随系统，带当前选中标记，避免水合用 mounted 守卫
- `layout.tsx`：用 ThemeProvider 包裹 children，sonner 自动跟随主题
- `LoginScreen.tsx`：品牌区改用固定品牌色（inline style `#2d4356` 底 + `#f7f6f1` 字），BrandScene SVG 路径用固定色，确保暗色下登录页品牌质感一致
- 全站组件无硬编码颜色（仅 shadcn overlay 的 bg-black/50 暗色下也合适），暗色 token 已在 globals.css 预置，直接生效

### 2. 全局命令面板（⌘K）
- store 加 `commandOpen` / `setCommandOpen` / `toggleCommand`
- 新增 `src/components/command-palette/CommandPalette.tsx`：基于 shadcn Command + Dialog
  - 4 分组：导航（首页/新建项目/配置/日志/脚本，按角色过滤）/ 项目（3个demo，可搜索名/学科/年级/阶段）/ 外观（浅色/深色/跟随系统）/ 账户（切换角色/退出）
  - 底部状态栏：↑↓选择 / ↵执行 / 山海教育工作台
  - 搜索支持 label+desc+keywords 多字段匹配
- `TopBar.tsx`：搜索按钮改为命令面板触发器，桌面显示"搜索… ⌘K"样式按钮，移动端保留图标按钮；新增 ThemeToggle
- `AppShell.tsx`：渲染 CommandPalette + 全局 keydown 监听 ⌘K/Ctrl+K；footer 提示"按 ⌘K 打开命令面板"

### 3. 视频方案对比功能（ProjectWorkspaceScreen）
- 内层组件加 `compareIds` / `compareOpen` 状态
- VideoPlanGrid：顶部新增"对比(N)"按钮（≥2启用变 primary）+ 重新生成按钮；每张卡片顶部加 Checkbox"加入对比"（最多3套，超出 toast 警告）
- VideoPlanCard：选中态 `border-primary/50 ring-1 ring-primary/20`；移除卡片内"对比"按钮（统一到顶部）
- 新增 `VideoPlanCompareDialog`：并排表格对比 8 字段（类型/分数/吸睛点/课程锚点/课堂落点问题/不提前讲解/接入教案位置/推荐理由），sticky 首列，bestScore 高亮（success 色+星），底部每列"采纳此方案"按钮
- 移除原"演示版暂不支持对比"toast，对比流程闭环

### 4. 证据文件预览（ProjectWorkspaceScreen）
- 内层组件加 `previewFile` 状态
- EvidenceTab：文件列表改为可点击 button，显示文件类型图标（JSON/图片/PDF/日志）+ 标签 + Maximize2 悬停图标
- 新增 `EvidencePreviewDialog`：文件名+类型标签+下载按钮（toast 占位）+ 模拟内容预览（JSON 格式化 / 日志带时间戳 / PDF/图片 占位说明）+ "演示环境预览为模拟数据"提示
- 新增辅助函数 `getFileMeta`（按扩展名返回图标+色调+标签）和 `mockPreviewContent`（按类型返回模拟内容）

## 验证结果
- `bun run lint` 全绿（0 错 0 警）
- agent-browser 端到端验证：
  - 暗色主题：切换生效（html class=dark），VLM 评审"暗色配色高级克制，文字对比度足够，无明显视觉问题"
  - 命令面板：⌘K 打开 → 搜索"春天"过滤出项目 → 选中导航到该项目工作区 ✓
  - 视频对比：video-script 结果 Tab → 勾选2张卡片 → "对比(2)"按钮启用 → 打开对比 Dialog 显示8字段表格 + bestScore高亮 + 采纳按钮 ✓
  - 证据预览：textbook-parse 证据 Tab → 3个可点击文件 → 点 JSON 打开预览 Dialog 显示格式化内容 ✓
  - 登录页品牌区暗色下保持深青灰质感（固定色）
  - 390px 移动端无横向溢出
  - dev.log 无运行时错误，禁忌词/Emoji 扫描干净
- VLM 评审新功能："符合高级克制风格，信息分层明确，表格+卡片对比清晰"
- 截图：rev1-01 至 rev1-22 共22张覆盖全部场景（亮/暗/移动/各功能）

## 未解决问题/风险
- 命令面板的 G D / G N 快捷键（shortcut 显示）尚未实现实际按键监听，仅展示提示
- 证据预览 JSON 未做语法高亮（VLM 建议，非必须）
- next-themes 已接入但暗色下个别 shadcn 组件（如 ScrollArea）可能需微调，当前观察无明显问题
- 视频方案"编辑"仍为 toast 占位（第一阶段要求）

## 建议下一阶段优先事项
1. 实现 G D / G N / G C 等单键导航快捷键（命令面板已展示提示）
2. 日志页/脚本页接入命令面板快速跳转
3. 项目工作区加"返回顶部"+节点轨键盘左右切换
4. 首页项目概览加筛选/排序（按状态/学科/更新时间）
5. 视频方案对比 Dialog 加"差异高亮"（标记各方案独特字段）
6. 暗色主题打磨：Sidebar 在暗色下可加更深的层次
7. 全站微交互动效（framer-motion 页面切换、卡片 hover lift）

---
Task ID: 7 (cron rev2)
Agent: 主代理 (webDevReview 巡检第2轮)
Task: 持续优化第2轮 —— 单键导航快捷键 + 首页项目筛选排序 + framer-motion动效 + 暗色Sidebar层次打磨

## 项目当前状态判断
- 服务器稳定运行，lint 全绿，dev.log 无错误
- 上一轮（rev1）功能全部回归正常（命令面板/暗色/视频对比/证据预览）
- 本轮无 bug，进入新功能开发

## 本轮已完成的修改

### 1. 单键导航快捷键（G+键序列）
- 新增 `src/hooks/use-global-shortcuts.ts`：
  - ⌘K/Ctrl+K 打开命令面板（输入框内也生效）
  - g d/n/c/l/s/p 单键序列导航（800ms 内按第二键，输入框内不触发，命令面板打开时不触发）
  - Escape 关闭命令面板/移动端抽屉
  - 角色过滤：g c/l/s 仅管理员可用
- AppShell 用 `useGlobalShortcuts()` 替换原 ⌘K 监听
- Sidebar NAV 项加 shortcut 字段（G D/G N/G P/G C/G L/G S），导航按钮右侧显示快捷键 kbd 徽标（lg+ 显示）；"当前项目"项显示项目名替代快捷键
- 实测：g+n→新建项目、g+d→首页、g+c→配置中心均生效

### 2. 首页项目概览筛选与排序
- DashboardScreen 新增 `ProjectOverview` 子组件：
  - 搜索框（项目名/学科/年级/负责人，带清除按钮）
  - 状态筛选（全部/进行中/待确认/阻塞/失败/已完成/草稿）
  - 学科筛选（动态从项目提取）
  - 排序（最近更新/进度/名称）
  - 激活筛选标签（FilterChip，可单独移除）+ 重置按钮
  - 筛选结果计数"共 N 个 · 显示 M 个"
  - 空结果 EmptyState + 清除筛选按钮
- 实测：搜索"春天"→1个；状态选"阻塞"→1个；重置→3个

### 3. framer-motion 页面切换动效 + 卡片 hover 微交互
- 新增 `src/components/common/PageTransition.tsx`：AnimatePresence mode="wait"，opacity+8px上移，240ms，ease [0.4,0,0.2,1]；key=screen+activeProjectId 确保切项目也触发
- AppShell main 内容外包 PageTransition
- ProjectCard 用 motion.div whileHover y:-3（20ms）+ 顶部品牌色细线 hover 从左展开（w-0→w-full，300ms）+ hover 阴影升 shadow-soft→shadow-lift
- 动效克制：仅 opacity/y，无弹性无旋转，符合设计规范

### 4. 暗色 Sidebar 层次打磨
- 品牌区左侧加品牌色竖指示条（h-7 w-[3px] bg-primary，纯色非渐变）
- 选中导航项加左侧品牌色指示条（h-5 w-[3px] bg-primary）+ 选中文字加 font-medium
- 系统状态卡片："系统"标题改"系统轻状态"；存储项加古铜金进度条（bg-bronze/70，h-1）；卡片 padding 加至 p-3.5
- VLM 评审暗色 Sidebar："品牌色指示条强化识别，选中项指示条醒目，存储进度条清晰，层次分明改善"

## 验证结果
- `bun run lint` 全绿（0 错 0 警）
- agent-browser 端到端验证：
  - 单键快捷键：g+n→新建项目 ✓、g+d→首页 ✓、g+c→配置中心 ✓
  - 项目筛选：搜索"春天"→1个、状态"阻塞"→1个、重置→3个 ✓
  - 页面切换动效：导航无错误，HMR 正常
  - 暗色 Sidebar：品牌指示条+选中指示条+存储进度条均清晰
  - 暗色工作区：无运行时错误
  - 390px 移动端：无横向溢出
  - 禁忌词/Emoji 扫描干净，dev.log 无错误
- VLM 最终评审："高级克制大气，亮色清新与暗色沉稳互补，视觉一致性通过统一色彩体系保障，细节层次清晰，符合专业教育工具调性"
- 截图：rev2-01 至 rev2-16 共16张

## 未解决问题/风险
- framer-motion AnimatePresence mode="wait" 在 HMR 时偶发 Fast Refresh full reload（非运行时错误，生产无影响）
- 单键快捷键在 agent-browser 自动化测试中需先 click body 聚焦（真实用户无此问题）
- 视频方案"编辑"仍为 toast 占位（第一阶段要求）

## 建议下一阶段优先事项
1. 项目工作区节点轨键盘左右切换（←/→ 切换节点）
2. 视频方案对比 Dialog 差异高亮（标记各方案独特字段）
3. 日志页/脚本页接入命令面板快速跳转
4. 证据预览 JSON 语法高亮
5. 首页"继续工作"Hero 加最近活动时间线
6. 全站 focus-visible 焦点环统一审计
7. 配置中心密钥状态加"最后使用时间"

---
Task ID: 8 (cron rev3)
Agent: 主代理 (webDevReview 巡检第3轮)
Task: 持续优化第3轮 —— 节点轨键盘切换 + 首页活动时间线 + JSON语法高亮 + 对比差异高亮

## 项目当前状态判断
- 服务器稳定运行，lint 全绿，dev.log 无错误
- 上一轮（rev2）功能全部回归正常（快捷键/筛选/动效/暗色Sidebar）
- 本轮无 bug，进入新功能开发

## 本轮已完成的修改

### 1. 项目工作区键盘 ←/→ 切换节点 + 1-5 切换 Tab
- ProjectWorkspace 内层组件加 useEffect 键盘监听：
  - ←/→ 按 order 顺序切换节点（goToStageByOffset）
  - 1/2/3/4/5 切换 输入/运行/结果/证据/日志 Tab
  - 输入框内不触发，对比/预览 Dialog 打开时不触发，带修饰键不触发
- Tab 标签加数字快捷键 kbd 角标（sm+ 显示）
- 流程节点区 SectionLabel 右侧加 KeyboardHint 组件（← → 切换节点）
- 新增 KeyboardHint 可复用组件（kbd 样式 + label）
- 实测：→ 从视频剧本切到视频资产、← 回到视频剧本、3 切结果 Tab、5 切日志 Tab ✓

### 2. 首页继续工作 Hero 加最近活动时间线
- types.ts 新增 ActivityItem 类型（kind: approve/reject/generate/parse/adopt/comment/upload）
- mock-data.ts 新增 MOCK_RECENT_ACTIVITIES（5条活动：生成方案/确认通过/生成失败/生成PPT/采纳教案）
- DashboardScreen 新增 ActivityTimeline 组件：
  - 时间线竖线连接（最后一个不显示）
  - 圆形图标按 kind 着色（approve=success/reject=destructive/generate=info/adopt=bronze）
  - 标题 + 时间 + 描述 + 可点击的项目·阶段链接（跳转工作区）
  - 按 projectId 过滤（Hero 内显示当前项目活动）
- ContinueWorkHero 右侧在"阶段进度"下方加"最近活动"时间线区
- VLM 评审："时间线视觉克制清晰，与阶段进度层次协调，信息层级明确"

### 3. 证据预览 JSON 语法高亮
- ProjectWorkspaceScreen 新增 highlightJson（正则 tokenize）：
  - key 用 primary 色、string 用 success 色、number 用 bronze 色、boolean/null 用 info 色、标点用 muted
  - 按行处理，保留缩进
- 新增 highlightLog：日志按 INFO/WARN/ERROR/SUCCESS 级别着色
- 新增 HighlightedPreview 组件：按扩展名分发（json→高亮/log→级别着色/其他→纯文本）
- EvidencePreviewDialog 的 pre 内容替换为 <HighlightedPreview/>
- 实测：JSON 预览 18 个着色 span，key/string/number 区分明显
- VLM 评审："key/string/number/boolean 区分明显，配色克制协调，可读性良好"

### 4. 视频方案对比 Dialog 差异高亮
- VideoPlanCompareDialog 加 isUnique 函数：判断某方案某文本字段值是否在所有对比方案中唯一
- 独特值单元格：border-l-2 border-l-bronze/60 + bg-bronze/[0.04] + "独特"角标
- 对比表格底部加图例栏：说明"独特"(该方案独有内容) + "最高分"(推荐分数最高) 含义
- 实测：3 方案对比显示 45 个 bronze 元素（独特标记+图例），图例清晰
- VLM 评审："差异高亮清晰易辨，配色克制未过度使用色彩，图例简洁辅助理解"

## 验证结果
- `bun run lint` 全绿（0 错 0 警）
- agent-browser 端到端验证：
  - 键盘切换：→ 切下一节点、← 切上一节点、1-5 切 Tab ✓
  - 活动时间线：首页 Hero 右侧显示 5 条活动（生成/确认/失败/PPT/采纳）✓
  - JSON 语法高亮：证据预览 18 个着色 span，key/string/number 区分 ✓
  - 对比差异高亮：3 方案对比显示独特标记 + 古铜金左边框 + 图例 ✓
  - 暗色主题：所有新功能在暗色下无运行时错误
  - 390px 移动端：无横向溢出
  - 禁忌词/Emoji 扫描干净，dev.log 无错误
- 截图：rev3-01 至 rev3-11 共11张

## 未解决问题/风险
- 键盘 ←/→ 在 agent-browser 自动化测试中需先 click body 聚焦（真实用户无此问题）
- JSON 语法高亮为正则实现，对极复杂嵌套 JSON 可能不够完美（mock 数据足够）
- 视频方案"编辑"仍为 toast 占位（第一阶段要求）

## 建议下一阶段优先事项
1. 日志页/脚本页接入命令面板快速跳转
2. 配置中心密钥状态加"最后使用时间"
3. 全站 focus-visible 焦点环统一审计
4. 首页"待处理事项"加批量处理操作
5. 项目工作区节点轨加"返回当前阶段"按钮（长流程时快速定位）
6. 活动时间线加"查看全部"展开/收起
7. 暗色主题：对比 Dialog 表格在暗色下行间距可微调

---
Task ID: 25 (用户反馈 - 深浅色主题修复)
Agent: 主代理
Task: 系统性修复深浅色主题对比度和层次问题

## 需求
用户反馈"深浅色主题都没做好"。VLM 诊断：深色对比度不足、边框太淡、muted-foreground 不清晰、层次扁平。

## 已完成的修改（globals.css token 优化）

### 深色 token 全面提升对比度
- --background #161a20→#0f1318（更深，卡片层次更突出）
- --foreground #e9e7e1→#f0ede6（文字更亮）
- --card #1d222a→#1a1f26（与背景拉开层次）
- --muted-foreground #9aa0ab→#b8bec8（次文字对比度大幅提升）
- --border #2a3038→#2e3540（边框更可见）
- --sidebar #14181e→#0c0f14（更深，与卡片区分）
- --sidebar-foreground #d8d5cd→#e8e5dd（侧栏文字更亮）
- --sidebar-border #232830→#1e2329（与背景协调）
- 状态色全部提亮：success #6f8a78→#8aaa98, warning #b98a4e→#d4a058, info #6f8aa3→#8eaac4, destructive #b05a5a→#d06868
- primary #c9a36a→#d4af76（金色更亮）

### 浅色 token 微调
- --muted-foreground #6b727c→#5c636e（次文字更深更清晰）
- --border #e4e1d9→#ddd9d0（边框更可见）

## 验证结果
- bun run lint 全绿
- VLM 评审：8 分（"浅色清晰协调，深色对比度改善，文字/边框/卡片层次清晰"）
- 390px 移动端无溢出
- 浅色/深色切换正常

## 核心改善
- 深色模式：背景更深(#0f1318) + 文字更亮(#f0ede6) + 边框更可见(#2e3540) + 次文字更清晰(#b8bec8)
- 浅色模式：次文字更深(#5c636e) + 边框更可见(#ddd9d0)
- 层次：background < sidebar < muted < card < border 五级清晰
