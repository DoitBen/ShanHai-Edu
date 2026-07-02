# Task 8 — DS 组件系统重构（3 个核心页面）

> 任务背景：VLM 审计指出"按钮不统一、卡片不对齐、缺乏高级感"。前一轮任务（task 7）通过 globals.css 自定义类（`card-unified` / `btn-cta-primary` / `pill-unified` / `gap-sm/md/lg/xl` 等）实现了视觉统一。本轮改用更彻底的方案：直接使用 React 组件层级的 DS 组件（`DSButton` / `DSCard` / `DSSectionTitle` / `DSBadge` / `DSPill` / `DSEmptyState` / `DSProgress` / `DSStatusDot`），让"统一"从 className 约束升级为组件 API 约束，杜绝后续误用。
>
> 3 个文件全部修改完成，业务逻辑（useState / handlers / async）零改动，仅替换 UI 组件 + 调整 className。

## 产出文件

| # | 文件 | DS 组件使用次数 | 主要改动 |
|---|------|----------------|---------|
| 1 | `src/components/screens/AdminMediaWorkbenchScreen.tsx` | 57 处 | 全面重构 |
| 2 | `src/components/screens/DashboardScreen.tsx` | 50 处 | 全面重构 |
| 3 | `src/components/video-workflow/VideoComposerPanel.tsx` | 25 处 | 全面重构 |
| 合计 | — | **132 处** | — |

## 关键改动汇总

### 1. AdminMediaWorkbenchScreen.tsx

#### 按钮统一化（DSButton + 内置 anchor 样式常量）
- 页头"刷新"按钮：`<Button variant="outline" className="btn-cta-secondary btn-md gap-sm">` → `<DSButton variant="secondary" size="md">`
- 图片 CTA：`<Button className="btn-cta-primary btn-lg mt-5 w-full gap-sm font-semibold">` → `<DSButton variant="primary" size="lg" className="mt-6 w-full font-semibold">`
- 加入视频参考篮按钮：`<Button variant="outline" className="btn-cta-secondary btn-md gap-sm">` → `<DSButton variant="secondary" size="md">`
- 视频 CTA：`<Button className="btn-cta-primary btn-lg shrink-0 gap-sm">` → `<DSButton variant="primary" size="lg" className="shrink-0">`
- RunList 同步按钮：`<Button variant="outline" size="sm" className="btn-cta-secondary btn-sm gap-sm t-caption">` → `<DSButton variant="secondary" size="sm" className="t-caption">`
- RunList 下载按钮（asChild anchor）：`<Button asChild size="sm" className="btn-cta-primary btn-sm gap-sm t-caption">` → `<a href={...} className={cn(DS_ANCHOR_PRIMARY_SM, "t-caption")}>`
- AssetList 下载按钮（asChild anchor）：`<Button asChild variant="outline" size="sm" className="btn-cta-secondary btn-sm">` → `<a href={...} className={DS_ANCHOR_SECONDARY_SM}>`

> **关键决策**：DSButton 渲染原生 `<button>`，不支持 asChild。对于必须渲染为 `<a>` 的下载链接，定义文件顶部常量 `DS_ANCHOR_PRIMARY_SM` 和 `DS_ANCHOR_SECONDARY_SM`，内联 DSButton primary/secondary sm 的完整 className（含 hover 上移、阴影变化），保证视觉与 DSButton 完全一致。

#### 卡片统一化（DSCard + h-full 等高）
- 6 个主 Card（图片生成 / 图片结果 / 视频生成 / 任务队列 / 素材库 / 历史任务）：`<Card className="card-unified card-pad-md card-equal">` → `<DSCard className="h-full">`
- 任务队列 Card（原 p-4）：→ `<DSCard className="h-full p-4">`（用 p-4 覆盖 DSCard 默认 p-5）
- StatusTile 卡片：→ `<DSCard hover={false} className="h-full p-4">`（状态卡不需要 hover 升起）

#### 网格 items-stretch
- 状态卡片网格 `mt-6 grid gap-4 md:grid-cols-4 items-stretch` ✓
- 图片 tab 左右栏 `grid gap-6 xl:grid-cols-[0.9fr_1.1fr] items-stretch` ✓
- 视频 tab 左右栏 `grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px] items-stretch` ✓
- 素材 tab 左右栏 `grid gap-6 xl:grid-cols-[1fr_1fr] items-stretch` ✓

#### SectionTitle → DSSectionTitle
- 删除文件内 `SectionTitle` 局部组件定义
- 所有 4 处调用替换为 `<DSSectionTitle icon={...} title={...} desc={...} />`
- 视频生成 tab 内 SectionTitle 在 flex row 中使用 `className="mb-0"` 保持布局

#### ToneBadge → DSBadge
- 视频生成顶部 ToneBadge：`<ToneBadge tone={providerReady.video ? "success" : "neutral"}>` → `<DSBadge variant={providerReady.video ? "success" : "neutral"}>`
- RunList 状态 ToneBadge：`<ToneBadge tone={run.status === "failed" ? "warning" : ...}>` → `<DSBadge variant={badgeVariant}>`
  - tone 映射：`warning` → `variant="warning"`；`success` → `variant="success"`；`neutral` → `variant="neutral"`；`danger` → `variant="error"`
- HistoryList 状态 ToneBadge：同上映射

#### EmptyState → DSEmptyState
- 5 处 EmptyState 全部替换为 DSEmptyState（isAdmin 拒绝 / AssetGrid 空 / RunList 等待 / AssetList 空 / HistoryList 空）
- 用 `className="mt-6"` / `className="mt-4"` 控制与上方内容的间距

#### PillSelect / ReadonlyPill → DSPill 包装
- `ReadonlyPill`：完全用 `<DSPill>` 重写 — `<DSPill><span>{icon}</span><span>{value}</span></DSPill>`
- `PillSelect`：用 `<DSPill className="w-auto p-0">` 包装 `<Select>`，SelectTrigger 设为 `h-10 w-auto border-0 bg-transparent px-0 shadow-none focus:ring-0 focus-visible:ring-0`（让 SelectTrigger 透明，视觉完全由外层 DSPill 提供）

#### 模板标签 → DSPill 视觉语言
- 10 个图片/视频模板按钮（原 `<button className="pill-unified h-8!">`）→ 使用 `DS_PILL_BTN_H8` 常量
- `DS_PILL_BTN_H8` 内联 DSPill 的视觉类（`inline-flex h-8 items-center gap-3 rounded-full px-4 text-xs font-medium transition-all duration-300 ease-apple bg-muted text-foreground hover:bg-muted/70 hover:border-border border border-transparent cursor-pointer focus-ring`）
- **关键决策**：DSPill 渲染 `<span>`，不支持 onClick / type / 焦点环。模板按钮需要可点击 + 键盘可访问，故直接用 `<button>` 元素 + DSPill 的 className 等价物，而非包裹（包裹会产生嵌套交互元素，且 hover 状态无法从外层 button 透传到内层 span）。

#### StatusTile 用 DSCard + DSBadge 重写
- 旧：`<Card className="card-unified card-pad-sm card-equal">` + stat-value-* 颜色类
- 新：`<DSCard hover={false} className="h-full p-4">` + `<DSBadge variant={badgeVariant}>{value}</DSBadge>`
- tone → badgeVariant 映射：`success` / `info` / `warning` / `neutral` 一一对应

#### RunList 状态视觉
- 状态圆点：原 `<span className={cn("h-2 w-2 shrink-0 rounded-full", dotClass)}>` → `<DSStatusDot status={dotStatus} />`
  - status 映射：`completed` → `"completed"`；`failed` → `"failed"`；processing/queued → `"active"`；其他 → `"pending"`
- 进度条：原 `<div className="progress-pro"><div className="progress-pro-bar" style={{ width: ... }} /></div>` → `<DSProgress value={run.progress || 0} variant="default" />`
- 状态徽章：ToneBadge → DSBadge（如上）

#### 间距统一
- `gap-sm` (8px) → `gap-3` (12px)
- `gap-md` (12px) → `gap-3` (12px)
- `gap-lg` (16px) → `gap-4` (16px)
- `gap-xl` (24px) → `gap-6` (24px)
- 所有 `space-y-sm` / `space-y-2` → `flex flex-col gap-3` 或 `space-y-3`
- 所有 `gap-1.5` → `gap-3`

#### 圆角统一
- `r-lg` / `r-xl` / `r-md` / `r-full` → `rounded-lg` / `rounded-xl` / `rounded-md` / `rounded-full`（统一用 Tailwind 原生类，与 DS 组件内部使用一致）

#### 移除的导入
- `Button`（不再使用，全部 DSButton 或 anchor）
- `Card`（不再使用，全部 DSCard）
- `Input`（未使用）
- `EmptyState`（不再使用，全部 DSEmptyState）
- `ToneBadge`（不再使用，全部 DSBadge）
- `Play`（未使用）

### 2. DashboardScreen.tsx

#### 按钮统一化
- 页头"新建项目"：`<Button className="btn-cta-primary btn-md gap-sm">` → `<DSButton variant="primary" size="md">`
- 错误重试：`<Button className="btn-cta-primary btn-md mt-lg gap-sm">` → `<DSButton variant="primary" size="md" className="mt-6">`
- 空状态新建：同上
- ContinueWorkHero "进入工作区"：`<Button className="btn-cta-primary btn-lg gap-sm">` → `<DSButton variant="primary" size="lg">`
- ContinueWorkHero "查看流程"：`<Button variant="outline" className="btn-cta-secondary btn-lg gap-sm">` → `<DSButton variant="secondary" size="lg">`
- 项目概览重置按钮：`<Button variant="ghost" size="sm" className="btn-sm gap-sm text-muted-foreground">` → `<DSButton variant="ghost" size="sm" className="text-muted-foreground">`
- 项目概览清除筛选：`<Button variant="outline" size="sm" className="btn-cta-secondary btn-sm gap-sm">` → `<DSButton variant="secondary" size="sm">`

#### 卡片统一化
- 5 个状态卡（loading / error / empty / PendingRow 容器 / 服务状态 / 筛选栏 / 项目空状态 / LightStat / ContinueWorkHero 主 Card）全部改为 DSCard
- 状态卡用 `hover={false}` 关闭 hover 升起效果（状态信息不需要交互反馈）
- LightStat 用 `<DSCard className="h-full p-4">` 确保等高

#### SectionHeader → DSSectionTitle
- 删除文件内 `SectionHeader` 局部组件定义
- 4 处调用替换为 `<DSSectionTitle icon={<span className="text-xs font-bold text-bronze">0X</span>} title={...} desc={...} action={...} />`
- index 数字放进 icon slot，用 `text-bronze` 保持品牌色调

#### LightStat 用 DSCard + DSProgress 重写
- 旧：`<Card className="card-unified card-pad-sm card-equal">` + `<Progress value={progress} className="mt-2 h-1 bg-muted" />`
- 新：`<DSCard className="h-full p-4">` + `<DSProgress value={progress} variant={progressVariant} className="mt-3" />`
- variant 映射：success tone → `"success"`；warning tone → `"warning"`；其他 → `"default"`

#### PendingRow 用 DSBadge
- 高优先级徽章：`<span className="badge-unified bg-destructive/10 text-destructive">` → `<DSBadge variant="error"><AlertTriangle />高优先级</DSBadge>`

#### ServiceStatus 用 DSBadge
- 原 `<ToneBadge tone={m.tone}>{m.label}</ToneBadge>` → `<DSBadge variant={m.variant}>{m.label}</DSBadge>`
- status → variant 映射：`ok` → `"success"`；`degraded` → `"warning"`；`down` → `"error"`

#### StageMiniRail 用 DSStatusDot
- 在"进行中"标签前加 `<DSStatusDot status={dotStatus} />`，让当前阶段有动态圆点反馈
- dotStatus 计算：done → `"completed"`；current → `"active"`；pending → `"pending"`
- 阶段节点（h-7 w-7 圆形）保留原 stage-node-* 类（这些是步骤指示器，不是状态点，与 DSStatusDot 用途不同）

#### ContinueWorkHero 进度条
- 原 `<div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-gradient-to-r from-primary to-bronze" style={{ width: `${project.progress}%` }} /></div>`
- 新：`<DSProgress value={project.progress} className="mt-3" />`（DSProgress 内置 h-1.5 + 渐变）

#### 网格 items-stretch
- 双栏布局 `mt-10 grid gap-6 lg:grid-cols-3 items-stretch` ✓
- 系统状态 4 列 `grid gap-4 sm:grid-cols-2 lg:grid-cols-4 items-stretch` ✓
- 项目卡片网格 `grid gap-4 sm:grid-cols-2 xl:grid-cols-3 items-stretch` ✓

#### 间距统一
- `gap-lg` → `gap-4`
- `gap-md` → `gap-4`（部分场景）/ `gap-3`（按钮内）
- `gap-xl` → `gap-6`
- `gap-sm` → `gap-3`
- `space-y-3.5` → `space-y-4`（活动时间线）
- `gap-x-8 gap-y-3` 保留（axis-specific 不在统一范围）

#### 移除的导入
- `Card` / `Button` / `Progress` / `Separator` / `ArrowUpRight` / `EmptyState` / `ToneBadge`

### 3. VideoComposerPanel.tsx

#### section 容器统一
- `<section className="card-unified card-pad-md">` → `<DSCard>`（DSCard 默认 p-5，与原 card-pad-md 的 1.25rem 接近）

#### 头部 Badge
- 提供商状态 Badge：`<Badge className="badge-unified" variant={...}>` → `<DSBadge variant={config.provider_ready ? "success" : "error">{...}</DSBadge>`
- 4 个配置 Badge（model/size/duration/单结果）：`<Badge className="badge-unified" variant="outline">` → `<DSBadge variant="neutral">`

#### 视频预览外框
- 保留 `overflow-hidden rounded-lg border border-border bg-black`（rounded-lg 与 DSCard 内部 rounded-xl 不冲突，因为这是预览框不是 Card）

#### 模板标签
- 6 个模板按钮：原 `<button className="pill-unified h-8!">` → `<button className={DS_PILL_BTN_H8}>`
- 使用与 AdminMediaWorkbenchScreen 相同的 `DS_PILL_BTN_H8` 常量，保证两个文件视觉完全一致

#### VideoRunPlaceholder 用 DSEmptyState
- 旧：自定义 `<div className="flex aspect-video w-full items-center justify-center bg-muted anim-float">` + 内嵌图标框 + 标题 + 进度条
- 新：`<DSEmptyState icon={...} title={statusLabel(run)} className="aspect-video w-full rounded-none border-0 bg-muted" action={run ? (<div>...<DSProgress />...</div>) : undefined} />`
- DSEmptyState 不接受 `children`，故把进度条放进 `action` slot
- `className` 覆盖默认 border/dashed/rounded，让它适配 16:9 视频预览框

#### VideoPreview 操作按钮
- 重新加载按钮：`<Button type="button" size="sm" variant="secondary">` → `<DSButton type="button" variant="secondary" size="sm">`
- 下载源文件按钮（asChild anchor）：`<Button type="button" size="sm" variant="secondary" asChild><a href={...}>` → `<a href={...} className={DS_ANCHOR_SECONDARY_SM}>`
- 全屏按钮：`<Button type="button" size="sm" variant="secondary" className="gap-1 bg-background/90">` → `<DSButton type="button" variant="secondary" size="sm" className="bg-background/90">`
- 全屏下载按钮（asChild anchor）：同上映射为 anchor

#### CTA 按钮
- `<Button className="btn-cta-primary btn-lg mt-4 w-full gap-sm font-semibold" disabled={submitDisabled} aria-disabled={submitDisabled} onClick={...}>` → `<DSButton variant="primary" size="lg" className="mt-4 w-full font-semibold" disabled={submitDisabled} aria-disabled={submitDisabled} onClick={...}>`
- DSButton 内置 `gap-2`，无需额外 gap 类

#### 间距统一
- `gap-sm` → `gap-3`
- `gap-md` → `gap-4`
- `space-y-sm` → `flex flex-col gap-3`

#### 移除的导入
- `Button` / `Badge`（全部替换为 DSButton / DSBadge）
- `DSPill`（最终未直接使用 — 改用 DS_PILL_BTN_H8 常量在 button 上，因为模板标签需要可点击）

## 关键设计决策

### 1. DSButton vs Anchor
DSButton 渲染 `<button>`，不支持 asChild。对于必须渲染为 `<a>` 的下载链接，定义文件顶部常量 `DS_ANCHOR_PRIMARY_SM` 和 `DS_ANCHOR_SECONDARY_SM`，内联 DSButton primary/secondary sm 的完整 className。这保证视觉一致性，同时保留 `<a>` 的下载语义（`href` + `download`）。

### 2. DSPill vs Clickable Pill
DSPill 渲染 `<span>`，不支持 `onClick` / `type` / `disabled` / 焦点环。对于需要可点击的模板标签按钮，直接用 `<button>` 元素 + DSPill 的 className 等价物（`DS_PILL_BTN_H8` 常量）。这保证：
- 可访问性（键盘聚焦 + Enter 触发）
- 视觉与 DSPill 完全一致
- 不会产生嵌套交互元素（button 内 span）

对于纯展示的 ReadonlyPill，直接用 `<DSPill>`。

### 3. PillSelect 包装策略
PillSelect 是 shadcn Select + pill 样式。用 `<DSPill className="w-auto p-0">` 包装整个 `<Select>`，SelectTrigger 设为透明（`border-0 bg-transparent px-0 shadow-none focus:ring-0`），让外层 DSPill 提供视觉，内层 SelectTrigger 只负责点击触发下拉。这避免了在 SelectTrigger 上重复定义 pill 样式。

### 4. DSCard padding 覆盖
DSCard 内置 `p-5`。对于需要不同 padding 的场景（如任务队列 p-4、状态卡 p-4），用 `className="p-4"` 覆盖。`cn()` 使用 `tailwind-merge`，后传入的 `p-4` 会覆盖先传入的 `p-5`。

### 5. DSCard hover={false}
状态卡、loading 卡、error 卡、筛选栏卡等"信息展示型"卡片不需要 hover 升起效果（避免误以为可点击），统一用 `hover={false}` 关闭。交互型卡片（如 ContinueWorkHero、ProjectCard）保留默认 `hover={true}`。

### 6. DSStatusDot 在 StageMiniRail 的用法
StageMiniRail 的步骤节点（h-7 w-7 圆形 + 数字/checkmark）是步骤指示器，与 DSStatusDot（h-2 w-2 状态点）用途不同，保留原 stage-node-* 类。在"进行中"文字前加 `<DSStatusDot status="active" />` 提供动态反馈，满足"用 DSStatusDot 替代圆点"的要求。

### 7. gap-sm (8px) → gap-3 (12px) 的取舍
任务要求所有间距统一为 12/16/24px。原 `gap-sm` (8px) 全部提升到 `gap-3` (12px)。在少数紧凑场景（如按钮内 icon+text）会有 4px 视觉膨胀，但换来全站间距一致性，符合"高级感 = 克制 + 统一"的设计哲学。DSButton 内部已内置 `gap-2` (8px) 用于 icon+text，这部分不动（属于组件内部细节）。

## 验证结果

- **tsc --noEmit --skipLibCheck**：✓ 0 errors（exit 0）
- **eslint**：✓ 0 errors, 0 warnings（exit 0）
- **业务逻辑**：所有 useState / useEffect / handlers / async 函数均未改动
- **DS 组件使用统计**：
  - AdminMediaWorkbenchScreen：57 处
  - DashboardScreen：50 处
  - VideoComposerPanel：25 处
  - 合计：132 处

## 后续注意事项

1. **ProjectCard 未重构**：`src/components/project/ProjectCard.tsx` 仍使用原 `<Card>` + `card-pro` 类。本任务范围只含 3 个核心文件，ProjectCard 暂不动。它的外层 div 已有 `h-full`，配合 DashboardScreen 项目网格的 `items-stretch` 可正常等高。如后续需要彻底统一，可将 ProjectCard 也改用 DSCard。

2. **globals.css 自定义类保留**：原 task 7 引入的 `card-unified` / `btn-cta-primary` / `pill-unified` / `gap-sm/md/lg/xl` / `r-lg/xl/full` / `section-title-unified` / `badge-unified` / `card-pad-sm/md/lg` / `card-equal` / `grid-align-stretch` / `ctrl-sm/md` / `btn-sm/md/lg` 等类仍保留在 globals.css 中。本任务的 3 个文件已不再使用它们，但其他文件可能仍在用。**不要删除这些类定义**，否则会破坏其他页面。

3. **stage-node-* 类保留**：`stage-node-done` / `stage-node-current` / `stage-node-pending` 仍用于 StageMiniRail 的步骤节点视觉。这些是步骤指示器专用类，不属于本任务的"按钮/卡片/badge/pill"统一范围。

4. **DSCard 默认 p-5 vs 原 card-pad-md (1.25rem=20px)**：DSCard 默认 p-5 = 1.25rem = 20px，与原 card-pad-md 完全一致，无需额外覆盖。原 card-pad-sm (0.875rem=14px) 和 card-pad-lg (1.75rem=28px) 用 `p-3.5` / `p-7` 覆盖（但本任务实际只用了 p-4 和 p-5/p-10 覆盖）。

5. **DSButton 不支持 variant="outline"**：原 `<Button variant="outline">` 需映射到 `<DSButton variant="secondary">`（透明 + 边框）。这是设计系统的统一决策：secondary 即 outline 风格。

6. **`<a>` 下载链接的可访问性**：`DS_ANCHOR_PRIMARY_SM` / `DS_ANCHOR_SECONDARY_SM` 包含 `focus-ring` 类，保证键盘聚焦时有可见的 outline。但 `<a>` 没有 `type="button"`，HTML 规范上 `<a>` 不需要 type 属性。
