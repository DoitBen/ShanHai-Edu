# Task 5 — 13 个文件前端优化重新应用（小云雀规范设计令牌）

## 产出文件（全部修改完成）

| # | 文件 | 修改类型 |
|---|------|---------|
| 1 | `src/components/layout/Sidebar.tsx` | 部分修改 |
| 2 | `src/components/screens/DashboardScreen.tsx` | 部分修改 |
| 3 | `src/components/screens/NewProjectScreen.tsx` | 部分修改 |
| 4 | `src/components/screens/ProjectWorkspaceScreen.tsx` | 部分修改（含全文 shadow-soft 替换） |
| 5 | `src/components/screens/ConfigScreen.tsx` | 部分修改 |
| 6 | `src/components/screens/LogsScreen.tsx` | 部分修改 |
| 7 | `src/components/screens/ScriptsScreen.tsx` | 部分修改 |
| 8 | `src/components/screens/AdminWorkflowScreen.tsx` | 部分修改 |
| 9 | `src/components/screens/AdminTextbookLibraryScreen.tsx` | 部分修改 |
| 10 | `src/components/video-workflow/VideoWorkflowWorkbench.tsx` | **完整重写** |
| 11 | `src/components/video-workflow/VideoAssetPanel.tsx` | 部分修改 |
| 12 | `src/components/video-workflow/VideoComposerPanel.tsx` | **完整重写** |
| 13 | `src/components/video-workflow/VideoRunHistoryPanel.tsx` | **完整重写** |

## 关键改动汇总

### 1. 通用设计令牌替换（9 个屏幕文件）
- 全文 `shadow-soft` → `shadow-apple-sm`
- 页头副标题 `mt-2 t-body text-muted-foreground` → `mt-3 h-page-subtitle`
- Dashboard/NewProject 页头标题 `t-title` → `h-page-title`
- ProjectWorkspace 的 WorkspaceHeader 项目名 `mt-2 t-title` → `mt-2 h-page-title`
- SectionHeader / SectionLabel：`t-overline text-bronze` → `t-overline font-bold text-bronze`，`t-module` → `t-module font-semibold text-foreground`，`mt-0.5` → `mt-1`
- ConfigScreen / LogsScreen 所有 `SelectTrigger className="h-11 w-full bg-card"` → `input-pro h-11 w-full bg-card`
- LogsScreen 搜索框加 `input-pro`，刷新/导出按钮 `gap-2` → `btn-cta-secondary gap-2 h-10`

### 2. Sidebar.tsx
- 导航项间距 `space-y-0.5` → `space-y-1.5`
- 激活态 `bg-sidebar-accent text-sidebar-accent-foreground font-medium` → `nav-item-active-pro`
- 按钮加 `nav-item-pro` 类，`transition-colors` → `transition`
- 系统状态区：`text-success` → `stat-value-success`，`text-info` → `stat-value-info`，`font-medium` → `font-semibold`，进度条 `bg-bronze/70` → `bg-bronze` + `transition-all duration-500 ease-apple`，整卡片加 `shadow-apple-sm`

### 3. DashboardScreen.tsx
- 新建项目按钮：`gap-2` → `btn-cta-primary gap-2 h-11 px-5`
- ContinueWorkHero 标题 `text-2xl font-semibold` → `text-[1.625rem] font-bold leading-tight tracking-tight`
- 项目属性行改为 `t-caption`，首项加 `font-medium text-foreground/80`
- 下一步动作框：渐变背景 + hover 升起 + 字体强化
- 进度条改为渐变 div（`bg-gradient-to-r from-primary to-bronze`）
- 进入工作区/查看流程按钮分别 `btn-cta-primary`/`btn-cta-secondary h-11 px-5`
- StageMiniRail 圆圈三态用 `stage-node-done`/`stage-node-current`/`stage-node-pending`
- PendingRow 卡片化（`card-pro`）+ 高优先级徽章加 AlertTriangle 图标 + 「高优先级」文字
- LightStat 卡片加 `stat-card ... shadow-apple-sm`，值用 `stat-value-*` 类，独立 iconTone 变量

### 4. NewProjectScreen.tsx
- 返回首页按钮：`gap-1.5 self-start text-muted-foreground` → `btn-cta-secondary gap-1.5 self-start h-9`
- StepCircle 三态：`bg-success/15 text-success ring-1 ring-success/30` → `stage-node-done font-bold transition-all duration-300 ease-apple` 等
- StepCard 展开时 `shadow-soft` → `shadow-apple-sm`
- 底部操作栏：`shadow-soft` → `shadow-apple-sm`，步骤数字加 `<span className="font-semibold text-foreground">{currentStep}</span>`，就绪状态加 `font-medium` 和 ✓/⚠ 符号（CheckCircle2 / AlertTriangle），4 个按钮分别加 `btn-cta-secondary`/`btn-cta-primary` + `h-10`/`px-5`
- 新增导入 `AlertTriangle`

### 5. ProjectWorkspaceScreen.tsx
- 全文 `shadow-soft` → `shadow-apple-sm`
- WorkspaceHeader 项目名 `mt-2 t-title` → `mt-2 h-page-title`
- 底部 3 列改为 `rounded-lg border border-border bg-gradient-to-br from-muted/30 to-transparent p-3.5 transition-all duration-300 ease-apple hover:border-bronze/30 hover:shadow-apple-sm`
- 总进度条改为 `progress-pro` + `progress-pro-bar`
- UserStepRail：按钮加 `nav-item-pro`，圆圈三态用 `stage-node-*`，`font-semibold` → `font-bold`
- WorkspaceTaskCard 头部：`t-overline text-muted-foreground/70` → `t-overline text-bronze`，`t-module` → `text-[1.125rem] font-bold leading-tight text-foreground`，`t-body text-muted-foreground` → `h-page-subtitle`
- 2 个 primary action 按钮 `gap-2` → `btn-cta-primary gap-2 h-11 px-5`
- 可回看依据材料框：`rounded-md ... bg-muted/20 p-3` → `rounded-lg ... bg-gradient-to-br from-muted/30 to-muted/10 p-3 transition-all duration-300 ease-apple hover:border-bronze/30`，标签 `t-caption font-medium text-foreground` → `t-overline text-muted-foreground/70`，查看按钮加 `btn-cta-secondary`
- SectionLabel：`t-overline text-bronze` → `t-overline font-bold text-bronze`，`t-module` → `t-module font-semibold text-foreground`，`mt-0.5` → `mt-1`

### 6. AdminTextbookLibraryScreen.tsx Metric 组件
- `rounded-md border border-border bg-background p-3` → `stat-card rounded-lg border border-border bg-card p-3 shadow-apple-sm`
- `mt-1 t-module` → `mt-1.5 t-module font-bold text-foreground`
- AssetLine 保持不变（任务仅要求 Metric）

### 7. VideoWorkflowWorkbench.tsx（重写）
- 新增 `estimateEta(run, config)` 函数：基于模型 + 进度反推剩余秒数（10s 视频约 60s 总时长）
- 新增 `formatEta(seconds)` 格式化
- 顶部活动任务状态条（非阻塞）：`bg-gradient-to-r from-primary/[0.06] to-bronze/[0.04]` + `shadow-apple-sm` + 双层 pulse 圆点（ping + pulse-soft）+ `progress-pro` 渐变进度条 + ETA 文字 + 立即同步按钮（`btn-cta-secondary`）
- 三栏布局改为 `xl:grid-cols-[280px_minmax(0,1fr)_360px]` + `lg:grid-cols-[240px_minmax(0,1fr)_320px]`，md 及以下用 Tabs
- Tabs 加图标：Images/Wand2/History，h-11，rounded-lg

### 8. VideoAssetPanel.tsx
- section 加 `card-pro card-pro-radius rounded-lg shadow-apple-sm`
- 上传按钮 `variant="outline" gap-1.5` → `btn-cta-primary gap-1.5 h-9`
- 已选区强化：`border-dashed` → `border-2 border-dashed` + 渐变背景 + `transition-all duration-300 ease-apple hover:border-bronze/40` + scroll-fine + 空状态双行文案
- 素材卡片：`rounded-md` → `rounded-lg` + `card-pro` + 选中态 `ring-2 ring-primary/25 shadow-apple-sm` + hover `border-bronze/40` + 图片 hover scale 1.04 + ease-apple
- 文件名加 `font-medium text-foreground`
- 空素材库占位卡片用 `empty-state-pro`

### 9. VideoComposerPanel.tsx（重写）
- 新增 `PROMPT_TEMPLATES` 六维结构化模板：主体/动作/运镜/氛围/画质/节奏
- 新增 AI 润色功能 `polishPrompt()`：检测缺失维度并自动补充，800ms 模拟延迟，toast 反馈
- 字数三色计数器 `promptLengthTone(length, max)`：
  - 灰色：< 10 字（提示补充细节）
  - 黄色（warning）：< 200 字（略简短）或 > 2000 字（偏长）
  - 绿色（success）：200-2000 字（合适）
  - 红色（destructive）：> 5000 字（已超限）
- CTA 强化：`btn-cta-primary w-full gap-2 h-12 text-base font-semibold` + `credits-hint` 显示「≈15 积分」
- 全屏预览：用 `Dialog` 实现，`max-w-[1200px]` 黑底，含 Expand 图标按钮
- 呼吸动画：placeholder 用 `anim-float`，processing 状态进度条用 `anim-pulse-soft`
- 卡片整体加 `card-pro card-pro-radius shadow-apple-sm`
- 提示词 Textarea 加 `input-pro`
- 模板按钮：圆角胶囊 + ease-apple hover 升起 + bronze 高亮
- 新增底部 Zap 提示行（无 disabledReason 时显示）

### 10. VideoRunHistoryPanel.tsx（重写）
- 状态圆点 pulse：`statusDotClass(run)` 返回 `bg-primary anim-pulse-soft` 等四态
- 进度条改为 `progress-pro` + `progress-pro-bar`，active 状态加 `anim-pulse-soft`
- 扫描光效：active 状态卡片顶部 1px 渐变线条 + `anim-pulse-soft`
- ETA 剩余秒数：`estimateEta(run)` + Clock 图标 + bronze 文字
- 空状态：用 `empty-state-pro`（Film 图标 + 标题 + 描述）
- 卡片选中态：`ring-2 ring-primary/15 shadow-apple-sm`，active 态 `border-primary/30 shadow-apple-sm`
- 滚动区：`overflow-y-auto scroll-fine` + maxHeight 限制
- 底部状态汇总：3 列网格显示「已完成 / 进行中 / 失败」计数，分别用 success/primary/destructive 强调色
- 按钮统一 `btn-cta-secondary` / `btn-cta-primary`
- section 加 `card-pro card-pro-radius shadow-apple-sm`

## 验证结果
- **tsc --noEmit --skipLibCheck**：✓ 0 errors
- **eslint**（13 个文件）：✓ 0 errors, 0 warnings
- **next build**：✓ Compiled successfully in 4.7s, TypeScript finished in 7.4s, 4 static pages generated

## 注意事项
1. `globals.css` 与 `AdminMediaWorkbenchScreen.tsx` 未做任何改动（按要求保持原样）
2. VideoComposerPanel 的字数计数器与 AI 润色使用前端模拟，无后端依赖
3. VideoWorkflowWorkbench 的 ETA 估算为前端经验值（10s 视频约 60s 生成），实际以后端 progress 为准
4. ProjectWorkspaceScreen.tsx 中 `Progress` 组件仍在多处使用（如 SubStatusList 等），未删除导入
