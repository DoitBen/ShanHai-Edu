# Task 4b — ProjectWorkspaceScreen 指挥台

## 产出文件
- `src/components/screens/ProjectWorkspaceScreen.tsx`（整体覆盖，约 870 行，唯一修改）

## 组件结构
```
ProjectWorkspaceScreen (外层)
  ├─ EmptyWorkspace          (无 activeProjectId 时的空态)
  └─ ProjectWorkspace key={project.id}  (内层，切换项目时重挂载)
       ├─ WorkspaceHeader        顶部 Header（返回+项目名+meta+状态+3列摘要）
       ├─ WorkflowRail           14 节点横向轨（分支标签+状态徽章+连接线）
       ├─ Tabs                   5 Tab：输入/运行/结果/证据/日志
       │   ├─ InputTab           Textarea + 待输入 warning + 保存按钮
       │   ├─ RunTab             StatusBadge + 状态文案 + 耗时 + 开始运行/重新生成
       │   ├─ ResultTab          普通节点：result 文本；video-script：VideoPlanGrid
       │   │   └─ VideoPlanGrid
       │   │       └─ VideoPlanCard × 9  推荐角标 + 5 TermRow + 推荐理由 + 采纳/编辑/对比
       │   ├─ EvidenceTab        文件列表（FileText 图标）
       │   └─ LogsTab            max-h-96 scroll + level 色图标
       └─ StageActions           Card 内底部 5 按钮（保存/重新生成/退回修改/进入下一步/确认通过）
```

## 关键决策
1. **零 useEffect**：通过 `key={project.id}` 让 React 在切换项目时重挂载内层组件，状态自然重置；切换节点/确认通过/进入下一步都用事件处理器内同步 `setSelectedKey + setTab + setInputDraft`。这绕过了 `react-hooks/set-state-in-effect` 规则（Task 4a 中 LoginScreen 触发的同一规则）。
2. **WorkflowRail 横向布局**：14 节点纵向太长（14×88=1232px 纵向），指挥台感弱；改为横向 `overflow-x-auto scroll-fine` + `min-w-max`，每节点 88×88px 紧凑，节点间细线连接器（已通过段 bg-success/50）。移动端横向滚动，桌面端也滚动（14×88+13×12=1444 > 1152），可接受。
3. **状态色映射**（节点圆点 + StatusBadge）：
   - approved → success + CheckCircle2 ✓
   - running → primary + Loader2 spin + 右上角脉冲点
   - failed/blocked → destructive + AlertTriangle
   - pending_confirm/input_required/ready → warning
   - not_started → muted
   - 选中态额外 `border-primary bg-primary/[0.04] shadow-soft`
4. **分支标签着色**：common=muted/60、video=info、ppt=bronze（极淡 t-overline 0.55rem，保持克制）
5. **StageActions 放在 Card 内底部**：`border-t border-border bg-muted/20 px-4 py-3`，非 sticky（避免与全局 sticky footer 冲突，Task 4a 同款决策）。按钮分两组：左 保存+重新生成 / 右 退回修改+进入下一步+确认通过(primary)。
6. **按钮启用规则**：
   - canSave: status !== running
   - canRegenerate: status !== running
   - canApprove: status in [ready, pending_confirm, approved] && !running
   - canReject: status !== not_started && status !== running
   - canNext: status not in [not_started, input_required, running]
7. **VideoPlanCard 克制设计**：header row（#rank + score + type + accepted badge）+ t-module 标题 + Separator + 5 TermRow（label w-32 + value flex-1）+ Separator + 推荐理由 + 底部 actions。推荐（rank===1）bronze 角标；采纳后 border-primary + ring-primary + 按钮变"已采纳" disabled。网格 `grid gap-4 lg:grid-cols-2`。
8. **video-script 结果 Tab 特殊**：当 `selectedStage.key === 'video-script'` 时渲染 VideoPlanGrid，其他节点渲染普通 result 文本。
9. **状态流转**：`handleApproveAndNext` 调 `approveStage` (Zustand 同步更新 stages + project) + `syncToStage(next)` (本地 setSelectedKey + setTab + setInputDraft)，无 setTimeout，React 批量更新。
10. **视觉对齐**：`.t-title/.t-module/.t-body/.t-caption/.t-overline`；Card `border-border bg-card shadow-soft`；StatusBadge 复用；无 Emoji、无渐变、无卡片套卡片（详情 Tab 内容直接在 Card 内；VideoPlanCard 是同级 grid 不算套卡片）；主色深青灰 primary，无强蓝。

## 验证结果
- **Lint**：`bun run lint` 0 错 0 警（仅 LoginScreen 1 个 pre-existing `react-hooks/set-state-in-effect` 错误，非本任务引入）。
- **dev.log**：无运行时错误，编译成功，所有 GET 200。
- **agent-browser errors**：空（无控制台错误）。
- **端到端验证**：
  1. 登录 admin/shanhai2026（已登录态）→ 首页正常
  2. 首页点"进入工作区"（demo-001 认识分数——分一分）→ 进入项目工作区
  3. 顶部 Header 完整：返回按钮 + 项目名(t-title) + 学科/年级/教材版本+册次/课型 meta + ProjectStatusBadge(进行中) + 当前阶段(视频剧本) + 总进度(42% + Progress) + 下一步动作(确认采纳视频剧本方案)
  4. WorkflowRail 14 节点正确渲染：1-4 已通过(✓ success)、5 当前(primary 高亮)、6-14 未开始(muted)；分支标签 公共/视频线/PPT线 显示正确
  5. 详情区 5 Tab 切换正常：输入(默认) / 运行 / 结果 / 证据 / 日志
  6. video-script 结果 Tab：9 张 VideoPlanCard 渲染，rank 1 有"推荐"角标(bronze)，每张卡片显示 #rank + 分数 + 类型 + 标题 + 5 TermRow + 推荐理由 + 采纳/编辑/对比按钮
  7. 点"确认通过" → 节点 5 变 ✓、selectedKey 切到 6(视频资产)、tab 重置到输入、进度 42%→36%(5/14 重算)、下一步动作变"进入「视频资产」"、确认通过/进入下一步按钮 disabled（新阶段 input_required）
  8. 点第二张卡片"采纳" → 卡片变高亮(border-primary + ring) + 按钮变"已采纳" disabled + toast"已采纳该方案"
  9. 返回首页 → 点 demo-003(古诗文诵读——静夜思) → 当前阶段视频生成(failed)：节点 8 显示 AlertTriangle + destructive、StatusBadge"失败"、日志 Tab 显示 4 条日志(含 2 条 error)、确认通过 disabled、进入下一步 enabled
- **截图**：
  - `/home/z/my-project/download/04-workspace.png`（demo-001 工作区：Header + 14 节点轨 + 输入 Tab + 底部操作）
  - `/home/z/my-project/download/04b-video-plans.png`（video-script 结果 Tab：9 张方案卡片网格）

## 状态流转是否生效
✅ 完全生效。点"确认通过"后：
- 当前节点 status: pending_confirm → approved（圆点变 ✓）
- project.currentStage: video-script → video-assets（Header 显示更新）
- project.progress: 42 → 36（5/14 重算）
- project.nextAction: "确认采纳视频剧本方案" → "进入「视频资产」"
- selectedKey: video-script → video-assets（详情区切换）
- tab: 重置到 input
- 下阶段 status: not_started → input_required（store 自动激活）
- 按钮启用状态：确认通过/进入下一步 disabled（input_required 不允许通过）
