# Task 6 — 剩余 10 个前端业务组件设计令牌优化（小云雀规范）

## 产出文件（全部修改完成）

| # | 文件 | 修改类型 |
|---|------|---------|
| 1 | `src/components/screens/LoginScreen.tsx` | 部分修改 |
| 2 | `src/components/layout/TopBar.tsx` | 部分修改 |
| 3 | `src/components/layout/AppShell.tsx` | 部分修改 |
| 4 | `src/components/project/ProjectCard.tsx` | 部分修改（移除 motion.div） |
| 5 | `src/components/command-palette/CommandPalette.tsx` | 部分修改 |
| 6 | `src/components/common/StateViews.tsx` | 重构 EmptyState/ErrorState |
| 7 | `src/components/common/StatusBadge.tsx` | 部分修改（3 个 Badge 加过渡） |
| 8 | `src/components/common/PageTransition.tsx` | 部分修改（ease-apple 曲线） |
| 9 | `src/components/brand/Logo.tsx` | 部分修改（LogoMark 加阴影） |
| 10 | `src/components/theme/ThemeToggle.tsx` | 部分修改（hover-lift） |

## 关键改动汇总

### 1. LoginScreen.tsx
- 用户名/密码 Input：加 `input-pro`，移除 `focus-visible:ring-amber-500/[0.30]`，加 `focus-visible:bg-white/[0.08]!` 保留深色主题下输入框透明背景（覆盖 input-pro 的 `:focus-visible { background: var(--background) }`）
- 登录按钮：加 `btn-cta-primary`，用 `!` 重要修饰保留品牌金色渐变（`bg-[linear-gradient(...)]!`、`text-white!`、`shadow-[...gold-glow...]!`），移除 `transition-transform hover:scale-[1.01] active:scale-[0.99]`（由 btn-cta-primary 接管 hover 升起）
- 演示账号容器：加 `shadow-apple-sm`
- DemoAccountButton：`transition-colors` → `hover-lift shadow-apple-sm`

### 2. TopBar.tsx
- 移动端菜单按钮：加 `transition-all duration-300 ease-apple hover:-translate-y-0.5`
- 桌面搜索框：加 `input-pro`，`transition-colors` → `transition-all duration-300 ease-apple`，移除 `rounded-md`（由 input-pro 的 0.5rem 接管）
- 移动端搜索按钮：加 `transition-all duration-300 ease-apple hover:-translate-y-0.5`
- 通知按钮：加 `transition-all duration-300 ease-apple hover:-translate-y-0.5`
- 头像触发按钮：`transition-colors` → `transition-all duration-300 ease-apple`，加 `hover:-translate-y-0.5`

### 3. AppShell.tsx
- authReady 加载态：加 `loading-dot` 呼吸圆点（`<span className="loading-dot" />`）
- ScreenLoading 卡片：`shadow-soft` → `shadow-apple-sm`，加 `transition-all duration-300 ease-apple`
- ScreenLoading 进度条：`bg-primary/50` → `bg-gradient-to-r from-primary to-bronze anim-pulse-soft`

### 4. ProjectCard.tsx
- 移除 `motion` 导入与 `motion.div` 包裹（避免与 card-pro 的 hover transform 叠加 -3px+-2px=-5px 过头），改为普通 `<div className="h-full">`
- 主 Card：加 `card-pro card-pro-radius shadow-apple-sm`，移除 `transition-shadow hover:shadow-lift focus-within:shadow-lift`（由 card-pro 接管）
- ProjectCardMinimal 按钮：`transition-colors` → `transition-all duration-300 ease-apple`，加 `shadow-apple-sm hover:-translate-y-0.5`

### 5. CommandPalette.tsx
- DialogContent：`shadow-lift` → `shadow-apple`（模态弹层用最深阴影）
- CommandInput：加 `input-pro`（保留 `border-0 focus:ring-0`，input-pro 的 `:focus-visible` box-shadow 提供古铜聚焦光晕）
- CommandEmpty：重构为 `empty-state-pro` 结构（`icon-wrap` + `title` + `desc`），图标用 Search
- CommandRow 列表项：加 `nav-item-pro`（hover 时 translateX(2px) 微反馈）

### 6. StateViews.tsx
- EmptyState：重构为 `empty-state-pro` 结构（`icon-wrap` + `title` + `desc`），移除自定义 `flex flex-col items-center ... gap-3 py-12` 布局
- ErrorState：同样重构为 `empty-state-pro`，icon-wrap 用 `bg-destructive/10! text-destructive!` 重要修饰覆盖默认 muted 背景
- LoadingState：保持不变（Loader2 旋转已足够）

### 7. StatusBadge.tsx
- StatusBadge / ProjectStatusBadge / ToneBadge 三个 Badge 统一加 `transition-all duration-300 ease-apple`
- 保留现有 `TONE_CLASS`（Tailwind 工具类组合，已是 badge-status 模式的等价实现，且自动适配深色模式）

### 8. PageTransition.tsx
- framer-motion `ease` 从 `[0.4, 0, 0.2, 1]`（标准 ease）→ `[0.16, 1, 0.3, 1]`（ease-apple 苹果曲线）
- `duration` 从 `0.24` → `0.28`（配合新曲线微调）

### 9. Logo.tsx
- LogoMark SVG：当 `withBg` 为 true 时加 `shadow-apple-sm rounded-[22%]`
- `rounded-[22%]` 精确匹配 rect 的 `rx=14/64≈21.875%`，使 box-shadow 跟随圆角而非方形包围盒
- 所有使用 LogoMark 的位置（Sidebar / TopBar / AppShell footer）自动获得品牌阴影

### 10. ThemeToggle.tsx
- 触发按钮：`transition-colors` → `transition-all duration-300 ease-apple`，加 `hover:-translate-y-0.5`
- 保留 `hover:bg-muted hover:text-foreground` 颜色反馈

## 设计令牌使用统计

| 令牌 | 使用文件 |
|------|---------|
| `shadow-apple-sm` | LoginScreen, AppShell, ProjectCard, CommandPalette(Logo) |
| `shadow-apple` | CommandPalette (模态) |
| `ease-apple` | TopBar, AppShell, ProjectCard, StatusBadge, ThemeToggle, PageTransition |
| `btn-cta-primary` | LoginScreen |
| `input-pro` | LoginScreen, TopBar, CommandPalette |
| `card-pro` / `card-pro-radius` | ProjectCard |
| `nav-item-pro` | CommandPalette |
| `empty-state-pro` | StateViews, CommandPalette |
| `loading-dot` | AppShell |
| `anim-pulse-soft` | AppShell |
| `hover-lift` | LoginScreen (DemoAccountButton) |
| `hover:-translate-y-0.5` | TopBar, ProjectCard, ThemeToggle（手动实现 hover-lift 以保留 background-color 过渡） |

## 关于 `!` 重要修饰符

Tailwind v4 的重要修饰符为后缀 `!`（如 `bg-white/[0.08]!`）。本次在以下场景使用：
- **LoginScreen 输入框**：`focus-visible:bg-white/[0.08]!` 覆盖 `input-pro:focus-visible { background: var(--background) }`（避免深色登录页上输入框聚焦时变白底）
- **LoginScreen 按钮**：`bg-[linear-gradient(...)]!` / `text-white!` / `shadow-[...]!` 覆盖 `btn-cta-primary` 的深蓝背景/前景色/阴影，保留品牌金色渐变
- **StateViews ErrorState**：`bg-destructive/10! text-destructive!` 覆盖 `empty-state-pro > .icon-wrap` 的默认 muted 背景

原因：自定义工具类（`.input-pro`、`.btn-cta-primary`、`.empty-state-pro`）在 `@layer utilities` 中声明位置晚于 Tailwind 生成的工具类，同特异性下后者会被覆盖，需用 `!important` 强制优先。

## 验证结果

- **tsc --noEmit --skipLibCheck**：✓ 0 errors（exit 0）
- **eslint**：✓ 0 errors, 0 warnings
- **next build**：✓ Compiled successfully in 4.9s, TypeScript finished in 7.6s, 4 static pages generated

## 注意事项

1. LoginScreen 登录按钮保留品牌金色渐变（用 `!` 覆盖 btn-cta-primary 的深蓝背景），因为登录页是深色品牌主页，深蓝按钮在深蓝背景上对比度不足
2. ProjectCard 移除了 framer-motion 的 `motion.div` 包裹，因为 card-pro 的 CSS `:hover { transform: translateY(-2px) }` 已提供 hover 升起，叠加 motion 的 `y: -3` 会导致 -5px 过头
3. StatusBadge 保留 TONE_CLASS（Tailwind 工具类组合）而非改用 inline style，因为 Tailwind 的 `bg-info/10` 等会自动适配深色模式（CSS 变量），inline style 难以同等优雅地处理
4. Logo 的 `rounded-[22%]` 为任意值百分比，Tailwind v4 支持；精确匹配 SVG rect 的 rx=14/64≈21.875%
5. 未修改 globals.css（延续 Task 5 的约束），未修改任何 ui/*.tsx 或 *.ts 逻辑文件
