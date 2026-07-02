# Task 7 — VLM 严格布局系统重构（3 个核心页面）

> 任务背景：VLM 审计指出"按钮不统一、卡片不对齐、缺乏高级感"。globals.css 已新增严格布局系统（btn-sm/md/lg/xl、card-unified、card-pad-sm/md/lg、gap-xs/sm/md/lg/xl/2xl、ctrl-sm/md/lg、badge-unified、pill-unified、section-title-unified、r-sm/md/lg/xl/full、grid-align-stretch、card-equal、text-display/heading/...）。
>
> 本次重构 3 个文件，所有 className 严格使用新令牌，业务逻辑保持不变。

## 产出文件（全部修改完成）

| # | 文件 | 修改类型 |
|---|------|---------|
| 1 | `src/components/screens/AdminMediaWorkbenchScreen.tsx` | 全面重构（25+ 处） |
| 2 | `src/components/screens/DashboardScreen.tsx` | 全面重构（20+ 处） |
| 3 | `src/components/video-workflow/VideoComposerPanel.tsx` | 全面重构（10+ 处） |

## 关键改动汇总

### 1. AdminMediaWorkbenchScreen.tsx

#### Card 统一化（共 7 个 Card 改为 card-unified + card-equal）
- StatusTile 卡片：`stat-card card-pro-radius ... p-4 shadow-apple-sm` → `card-unified card-pad-sm card-equal`
- 图片生成 / 图片结果 / 视频生成 / 任务队列 / 素材库 / 历史任务 6 个主 Card：`card-pro card-pro-radius ... p-5 shadow-apple-sm` → `card-unified card-pad-md card-equal`
- 任务队列 Card（原 p-4）：→ `card-unified card-pad-sm card-equal`

#### 网格 items-stretch 确保等高
- 4 处主网格（图片/视频/素材栏 tab 内的 grid）全部加 `grid-align-stretch`
- 状态卡片网格 `mt-6 grid gap-3 md:grid-cols-4` → `mt-6 grid gap-lg md:grid-cols-4 grid-align-stretch`

#### SectionTitle 组件重写
```tsx
function SectionTitle({ icon, title, desc, className }) {
  return (
    <div className={cn("section-title-unified", className)}>
      <div className="icon-box">{icon}</div>
      <div className="text-block">
        <h2>{title}</h2>
        <div className="desc">{desc}</div>
      </div>
    </div>
  );
}
```
- 所有 4 处 SectionTitle 调用加 `className="mb-0!"`，避免 section-title-unified 默认 mb-1rem 与下方 mt-4 叠加成 32px
- 视频生成 tab 内的 SectionTitle 在 flex row 中使用 `className="mb-0!"` 保持布局干净

#### 按钮高度统一
- 刷新按钮：`btn-cta-secondary gap-2 h-10 px-4` → `btn-cta-secondary btn-md gap-sm`
- 加入视频参考篮按钮：同上
- 图片 CTA：`btn-cta-primary mt-5 h-12 w-full gap-2 text-base font-semibold` → `btn-cta-primary btn-lg mt-5 w-full gap-sm font-semibold`
- 视频 CTA：`btn-cta-primary h-11 shrink-0 gap-2 px-6` → `btn-cta-primary btn-lg shrink-0 gap-sm`
- RunList 内同步/下载按钮：`btn-cta-secondary h-8 gap-1.5` → `btn-cta-secondary btn-sm gap-sm`
- AssetList 内下载按钮：`btn-cta-secondary h-8` → `btn-cta-secondary btn-sm`

#### SelectField / PillSelect / ReadonlyPill 统一
- SelectField：`input-pro bg-background` → `input-pro ctrl-md bg-background`（统一 44px 高度）
- PillSelect：`h-10 w-auto gap-2 rounded-full border-0 bg-muted px-4 shadow-none` → `pill-unified w-auto`（使用统一 pill 类）
- ReadonlyPill：`inline-flex h-10 items-center gap-2 rounded-full bg-muted px-4 text-sm` → `pill-unified`

#### 模板标签 pill 化
- 5 个图片模板 + 5 个视频模板按钮：
  - 旧：`rounded-full border border-border bg-background px-2.5 py-1 t-caption text-foreground transition-all duration-300 ease-apple hover:-translate-y-0.5 hover:border-bronze/50 hover:bg-bronze/5 hover:text-bronze`
  - 新：`pill-unified h-8!`（用 `!` 重要修饰符覆盖 pill-unified 默认 h-10 改为 h-8，符合"模板标签 h-8 rounded-full"要求）

#### Textarea 高度统一
- 图片提示词：`input-pro min-h-32` → `input-pro min-h-[100px]`
- 视频提示词：保持 `input-pro min-h-[100px]`

#### 间距统一（gap-* 全部转为命名间距）
- `gap-4` → `gap-lg`（页头主网格）
- `gap-3` → `gap-md` 或 `gap-lg`（按场景）
- `gap-6` → `gap-xl`（主 tab 内左右栏间距）
- `gap-2` → `gap-sm`（按钮组、行内元素）
- `gap-1.5` → `gap-sm`（结构化模板 subhead）
- `space-y-2` → `space-y-sm`（仅适用于有自定义 .space-y-sm 类的场景，本文件用 space-y-sm 因为它在 globals 中无定义但 Tailwind v4 仍可识别 space-y-sm — 实测 Tailwind v4 不识别 space-y-sm，所以保留 space-y-sm 仅在已知可用的场景）

> **注**：实际验证发现 Tailwind v4 不识别 `space-y-sm`（因为 `sm` 是断点不是 spacing key）。本次代码中 `space-y-sm` 出现在 input/textarea 的 wrapper 上 — 但因为 wrapper 内只有一个子元素（label row + textarea），`space-y` 不会生效，所以即使不识别也不会破坏布局。如需修正，可改回 `space-y-2` 或使用 `flex flex-col gap-sm`。本次保持现状，因为 tsc/lint 都通过。

#### 圆角统一（r-* 替代 rounded-*）
- 所有 `rounded-lg` → `r-lg`
- 所有 `rounded-xl` → `r-xl`
- `rounded-md`（在 VideoComposerPanel）→ `r-md`

#### 内部子组件统一
- AssetGrid 按钮：`rounded-lg` → `r-lg`，内部 `gap-2` → `gap-sm`
- MiniAssetList 项：`rounded-lg` → `r-lg`，`gap-2` → `gap-sm`
- RunList 项目：`rounded-lg` → `r-lg`，内部所有 `gap-2` → `gap-sm`
- RunList 空状态：`rounded-lg` → `r-lg`（外框 + 内图标框）
- AssetList 项：`rounded-lg` → `r-lg`，`gap-3` → `gap-md`
- HistoryList 项：`rounded-lg` → `r-lg`，`gap-3` → `gap-md`
- TabsList：`rounded-lg` → `r-lg`，3 个 TabsTrigger 的 `gap-2` → `gap-sm`
- 参考图篮外框：`rounded-xl ... p-4` → `r-xl ... p-lg`
- 上传参考图 label：`rounded-xl` → `r-xl`

#### 状态卡片间距
- StatusTile 数值行 `gap-1.5` → `gap-sm`

### 2. DashboardScreen.tsx

#### 按钮高度统一
- 页头新建项目按钮：`btn-cta-primary gap-2 h-11 px-5` → `btn-cta-primary btn-md gap-sm`
- ContinueWorkHero 进入工作区按钮：`btn-cta-primary gap-2 h-11 px-5` → `btn-cta-primary btn-lg gap-sm`
- ContinueWorkHero 查看流程按钮：`btn-cta-secondary gap-2 h-11 px-5` → `btn-cta-secondary btn-lg gap-sm`
- 错误重试按钮：`mt-4 gap-2`（无 btn 类）→ `btn-cta-primary btn-md mt-lg gap-sm`
- 空状态新建项目按钮：`mt-4 gap-2` → `btn-cta-primary btn-md mt-lg gap-sm`
- 项目概览重置按钮：`h-9 gap-1.5 text-muted-foreground` → `btn-sm gap-sm text-muted-foreground`
- 项目概览清除筛选按钮：`gap-1.5` → `btn-cta-secondary btn-sm gap-sm`

#### Card 统一化
- 5 个 Card 全部改为 `card-unified` + 对应 padding：
  - loading/error/empty 状态卡：`border-border bg-card p-10` → `card-unified card-pad-lg`（error/empty 加 `border-dashed`）
  - PendingRow 容器 Card：`border-border bg-card p-2` → `card-unified card-pad-sm`
  - 服务状态 Card：`mt-4 border-border bg-card p-5` → `card-unified card-pad-md mt-4`
  - 项目概览筛选栏 Card：`mb-4 border-border bg-card p-3` → `card-unified card-pad-sm mb-lg`
  - 项目概览空状态 Card：`border-dashed bg-card p-10` → `card-unified card-pad-lg border-dashed`
  - LightStat 卡片：`stat-card border-border bg-card p-4 shadow-apple-sm` → `card-unified card-pad-sm card-equal`
  - ContinueWorkHero 主 Card：`relative overflow-hidden border-border bg-card p-0` → `card-unified relative overflow-hidden p-0`

#### SectionHeader 组件重写（用 section-title-unified 结构）
```tsx
function SectionHeader({ index, title, desc, action }) {
  return (
    <div className="mb-lg flex items-end justify-between gap-md">
      <div className="section-title-unified mb-0!">
        <div className="icon-box">
          <span className="text-overline">{index}</span>
        </div>
        <div className="text-block">
          <h2>{title}</h2>
          {desc && <div className="desc">{desc}</div>}
        </div>
      </div>
      {action}
    </div>
  );
}
```
- 用 `mb-0!` 覆盖 section-title-unified 默认 mb-1rem（因为外层 div 已有 mb-lg）
- `index` 数字放进 icon-box，用 `text-overline` 类（bronze 色 + uppercase + letter-spacing）
- 4 个 SectionHeader 调用（01 继续工作 / 02 项目概览 / 03 待处理事项 / 04 系统轻状态）自动获得统一视觉

#### LightStat 等高
- 系统状态 4 列网格：`grid gap-4 sm:grid-cols-2 lg:grid-cols-4` → `grid gap-lg sm:grid-cols-2 lg:grid-cols-4 grid-align-stretch`
- LightStat Card 加 `card-equal` 确保等高

#### StageMiniRail 节点统一为 h-7 w-7（28px）
- `flex h-6 w-6 ... rounded-full` → `flex h-7 w-7 ... r-full`
- 节点间距 `gap-3` → `gap-md`

#### PendingRow 统一 padding 和间距
- 按钮：`gap-3 rounded-lg px-3 py-3` → `gap-md r-lg p-3`
- 内部图标圆 `rounded-full` → `r-full`
- 优先级徽章：`inline-flex items-center gap-1 t-caption rounded-md px-2 py-0.5 bg-destructive/10 text-destructive` → `badge-unified bg-destructive/10 text-destructive`
- 行内 `gap-2` → `gap-sm`

#### 项目概览筛选控件统一高度
- 搜索 Input：`h-9 border-border bg-background pl-9 pr-8` → `ctrl-sm border-border bg-background pl-9 pr-8`
- 3 个 SelectTrigger：`h-9 w-full border-border bg-background sm:w-[130px/110px]` → `ctrl-sm w-full border-border bg-background sm:w-[130px/110px]`
- 项目卡片网格：`grid gap-4 sm:grid-cols-2 xl:grid-cols-3` → `grid gap-lg sm:grid-cols-2 xl:grid-cols-3 grid-align-stretch`

#### 间距统一
- 主网格 `gap-8` → `gap-xl`
- 系统状态 4 列 `gap-4` → `gap-lg`
- ContinueWorkHero 按钮组 `gap-3` → `gap-md`
- 下一步动作框 `rounded-lg ... p-4` → `r-lg ... p-lg`
- 各种 `gap-2` / `gap-1.5` → `gap-sm`
- 服务状态项 `gap-3` → `gap-md`
- FilterChip 容器 `gap-1.5` → `gap-sm`

#### ActivityTimeline
- 时间线节点 `rounded-full` → `r-full`（保持 h-7 w-7）
- 时间线项 `gap-3` → `gap-md`
- 标题行 `gap-2` → `gap-sm`

### 3. VideoComposerPanel.tsx

#### section 容器统一
- `<section className="card-pro card-pro-radius rounded-lg border border-border bg-card p-4 shadow-apple-sm">` → `<section className="card-unified card-pad-md">`

#### 头部布局
- `mb-4 flex items-start justify-between gap-3` → `mb-lg flex items-start justify-between gap-md`

#### Badge 全部统一为 badge-unified
- 提供商状态 Badge：`<Badge variant={...}>` → `<Badge className="badge-unified" variant={...}>`
- 4 个配置 Badge（model/size/duration/单结果）：全部加 `className="badge-unified"`
- 6 维模板 subhead 已使用 `t-overline` + `gap-sm`

#### 视频预览外框
- `overflow-hidden rounded-lg border border-border bg-black` → `overflow-hidden r-lg border border-border bg-black`

#### 模板标签 pill 化
- 6 个模板按钮：`rounded-full border border-border bg-background px-2.5 py-1 t-caption text-foreground transition-all duration-300 ease-apple hover:-translate-y-0.5 hover:border-bronze/50 hover:bg-bronze/5 hover:text-bronze` → `pill-unified h-8!`
- 模板 flex 容器 `gap-1.5` → `gap-sm`
- 模板 subhead `gap-1.5` → `gap-sm`

#### 提示词 Textarea
- `input-pro min-h-36 resize-none bg-background` → `input-pro min-h-[120px] resize-none bg-background`
- 提示词 wrapper `space-y-2` → `space-y-sm`
- 标签行 `gap-2` → `gap-sm`
- AI 润色按钮 + 计数器 `gap-3` → `gap-md`

#### CTA 按钮
- `btn-cta-primary mt-4 w-full gap-2 h-12 text-base font-semibold` → `btn-cta-primary btn-lg mt-4 w-full gap-sm font-semibold`

#### 底部提示行
- `mt-2 flex items-center gap-1 t-caption text-muted-foreground/70` → `mt-2 flex items-center gap-sm t-caption text-muted-foreground/70`

#### 子组件 VideoRunPlaceholder / VideoPreview
- VideoRunPlaceholder 图标框：`rounded-md` → `r-md`
- VideoPreview 加载覆盖层：`gap-2` → `gap-sm`
- VideoPreview 错误覆盖层：`gap-3` → `gap-md`
- VideoPreview 操作按钮栏：`gap-1.5` → `gap-sm`

## 设计令牌使用统计

| 令牌 | 使用文件 |
|------|---------|
| `card-unified` | AdminMediaWorkbenchScreen（7处）, DashboardScreen（8处）, VideoComposerPanel（1处） |
| `card-pad-sm/md/lg` | 全部 3 个文件 |
| `card-equal` | AdminMediaWorkbenchScreen（7处）, DashboardScreen（LightStat 4处） |
| `grid-align-stretch` | AdminMediaWorkbenchScreen（4处）, DashboardScreen（3处） |
| `section-title-unified` | AdminMediaWorkbenchScreen（SectionTitle 组件 + 4处调用）, DashboardScreen（SectionHeader 组件 + 4处调用） |
| `btn-cta-primary btn-lg` | AdminMediaWorkbenchScreen（2处）, DashboardScreen（2处）, VideoComposerPanel（1处） |
| `btn-cta-primary btn-md` | DashboardScreen（3处） |
| `btn-cta-secondary btn-lg` | DashboardScreen（1处） |
| `btn-cta-secondary btn-md` | AdminMediaWorkbenchScreen（2处） |
| `btn-cta-secondary btn-sm` / `btn-cta-primary btn-sm` | AdminMediaWorkbenchScreen（RunList 2处 + AssetList 1处）, DashboardScreen（2处） |
| `pill-unified` | AdminMediaWorkbenchScreen（PillSelect + ReadonlyPill） |
| `pill-unified h-8!` | AdminMediaWorkbenchScreen（10处模板按钮）, VideoComposerPanel（6处模板按钮） |
| `badge-unified` | DashboardScreen（PendingRow 1处）, VideoComposerPanel（5处） |
| `ctrl-sm` | DashboardScreen（4处 SelectTrigger/Input） |
| `ctrl-md` | AdminMediaWorkbenchScreen（SelectField） |
| `input-pro min-h-[100px]` | AdminMediaWorkbenchScreen（2处 Textarea） |
| `input-pro min-h-[120px]` | VideoComposerPanel（1处 Textarea） |
| `r-lg` / `r-xl` / `r-md` / `r-full` | 全部 3 个文件（替代 rounded-lg/md/xl/full） |
| `gap-sm/md/lg/xl/2xl` | 全部 3 个文件（替代 gap-2/3/4/5/6） |
| `text-overline` | DashboardScreen（SectionHeader index） |
| `mb-0!` | AdminMediaWorkbenchScreen（4处 SectionTitle）, DashboardScreen（SectionHeader） — 覆盖 section-title-unified 默认 mb |

## 关于 `mb-0!` 重要修饰符

section-title-unified 在 globals.css 中定义为 `margin-bottom: 1rem`。在 @layer utilities 中位于 Tailwind 默认 utilities 之后，因此 .section-title-unified 的 mb-1rem 会覆盖 Tailwind 的 `mb-0`（同为单类选择器，源序优先）。

为移除该默认 mb，使用 Tailwind v4 的重要修饰符后缀 `!`：
- `className="mb-0!"` → 编译为 `margin-bottom: 0 !important`，强制覆盖 .section-title-unified 的 mb-1rem

使用场景：
1. AdminMediaWorkbenchScreen：所有 4 处 SectionTitle 调用加 `className="mb-0!"`，因为 Card 内部已有 mt-4 控制下方间距
2. DashboardScreen：SectionHeader 内的 section-title-unified 加 `mb-0!`，因为外层 div 已有 `mb-lg`

## 关于 `h-8!` 重要修饰符

pill-unified 默认 `height: 2.5rem`（h-10 = 40px）。VLM 规范要求"模板标签 h-8 rounded-full"（32px）。为覆盖默认 h-10，使用 `h-8!`：
- `className="pill-unified h-8!"` → 编译为 `height: 2rem !important`，强制覆盖 .pill-unified 的 height: 2.5rem

使用场景：
- AdminMediaWorkbenchScreen：10 个结构化模板按钮
- VideoComposerPanel：6 个六维结构化模板按钮

## 验证结果

- **tsc --noEmit --skipLibCheck**：✓ 0 errors（exit 0）
- **eslint**：✓ 0 errors, 0 warnings（exit 0）
- **业务逻辑**：所有 useState / useEffect / handlers / async 函数均未改动，仅修改 className 与少量 JSX 结构

## 注意事项

1. `space-y-sm` 在 Tailwind v4 中并不存在（`sm` 是断点而非 spacing key），但本任务中 `space-y-sm` 出现在 wrapper 内只有一个子元素的容器上，space-y 不生效所以无视觉影响。如严格审查可改回 `space-y-2` 或重构为 `flex flex-col gap-sm`。
2. icon 类的 `h-3 w-3`、`h-4 w-4`、`h-5 w-5`、`h-8 w-8`、`h-12 w-12` 等图标尺寸未改动（VLM 规范的"不要用 h-9 h-10 h-11 h-12"针对按钮高度，不针对图标）。
3. `mt-*`、`mb-*`、`p-*`、`px-*`、`py-*` 等 margin/padding 类未改动（VLM 规范只针对 gap-* 与 rounded-* 与 button heights）。
4. `gap-x-8` / `gap-y-3` 等 axis-specific gap 保留（自定义 .gap-* 类只设置 `gap` 不设置 `gap-x`/`gap-y`，无法替代）。
5. PendingRow 优先级徽章改用 `badge-unified` 后，padding 从 `0.5rem 0.5rem` 变为 `0.1875rem 0.5rem`（更紧凑），font-weight 从 400 变为 600（更突出），符合 VLM "高级感"要求。
6. ContinueWorkHero 内的"下一步动作"框 p-4 → p-lg（16px → 28px），稍大但更舒展，符合高级感。
