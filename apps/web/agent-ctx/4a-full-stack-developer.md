# Task 4a — NewProjectScreen 5 步工作流向导

## 产出文件
- `src/components/screens/NewProjectScreen.tsx`（整体覆盖，约 760 行）

## 关键决策
1. **状态管理**：`currentStep`（当前展开步骤）+ `maxStep`（最远到达步骤）用本地 React state；`parseConfirmed`（解析确认标志）也用本地 state，因为 `NewProjectDraft` 类型未定义该字段，且属于 UI 临时状态。草稿本身绑定 store 的 `draft` / `setDraft`。
2. **步骤状态语义**：
   - `step === currentStep` → current（进行中）
   - `step <= maxStep && step !== currentStep` → done（已完成，可回看）
   - `step > maxStep` → todo（未开始，锁定不可点）
3. **Stepper 交互**：点击已完成步骤切换展开；点击未开始步骤 toast 提示「请先完成当前步骤」。
4. **StepCard 折叠/展开**：所有 5 张卡片同时可见；当前步骤展开表单，其他步骤折叠为摘要行（点击 done 状态的卡片头部可回看）。
5. **教材解析**：`parseStatus` 三态 idle/parsing/done；点击「开始解析」→ setDraft parsing → setTimeout 1.2s → setDraft done + MOCK_TEXTBOOK_PARSE + toast；「确认解析结果」按钮设置 parseConfirmed=true 才允许下一步；「重新解析」重置 parseConfirmed 并重跑；「重置」回到 idle。
6. **创建项目**：第 5 步显示「创建项目」主按钮（替换「下一步」），校验全部 5 步通过后调用 `commitDraftToProject()` 拿到新 id，toast 成功，220ms 后 `openProject(id)` 进入工作区。
7. **文件上传**：`<label>` 包 hidden `<input type=file>`，内含一个 `pointer-events-none` 的视觉 Button（点击穿透到 label），同时支持 onDrop 拖拽；只记录文件名到 `draft.textbookFileName`。
8. **视觉对齐**：严格复用 `.t-title/.t-module/.t-body/.t-caption/.t-overline`；Card `border-border bg-card`；输入框统一 `h-11 bg-card`；标签 `t-body font-medium`；无 Emoji、无渐变、无卡片套卡片（解析结果/配置摘要用 `div + border-border bg-muted/20`，非 Card 组件）；主色为深青灰 `primary`。
9. **底部操作栏**：非 sticky（避免与全局 sticky footer 重叠），用 `Card` 样式容器；包含「保存草稿」「上一步」「下一步」/「创建项目」+ 当前步骤就绪状态文字。
10. **响应式**：容器 `max-w-[1100px]`；Stepper `overflow-x-auto scroll-fine`（移动端横向滚动）；表单 `grid sm:grid-cols-2 lg:grid-cols-3`；页头/底部栏 `flex-col sm:flex-row`。

## 验证结果
- **Lint**：`npx eslint src/components/screens/NewProjectScreen.tsx` → 0 errors, 0 warnings（项目整体 `bun run lint` 仅有 LoginScreen 的 1 个 pre-existing `react-hooks/set-state-in-effect` 警告，非本任务引入）。
- **dev.log**：无运行时错误，编译成功。
- **agent-browser 端到端**：
  1. 登录 admin/shanhai2026（已登录态）
  2. 点侧栏「新建项目」→ Stepper 5 步显示，步骤 1 展开，2-5 折叠为「未开始」
  3. 填项目名「认识周长——围一圈」→「下一步」→ 步骤 1 折叠为摘要（已完成），步骤 2 展开
  4. 点「开始解析」→ 进度条显示「正在解析教材结构…」→ 1.2s 后显示解析结果预览（学科/年级/版本/册次/课题/核心知识点 4 条/教学目标摘要/教学重点 2 条/教学难点 2 条）
  5. 点「确认解析结果」→ 显示「已确认，可进入下一步」→「下一步」→ 步骤 3 展开
  6. 视频设计导入：5 个 Checkbox（3 个默认选中）、数量、主题、受众、时长、创意要求、术语提示（课程锚点 / 课堂落点问题）→「下一步」
  7. PPT 配置：风格/页数/结构 →「下一步」
  8. 路径与约束：输出路径、安全模式 Switch、约束说明、配置摘要（12 项回显）→「创建项目」
  9. toast「项目已创建，正在进入工作区」→ 自动跳转项目工作区，面包屑显示「认识周长——围一圈」，侧栏「当前项目」显示新项目名
- **截图**：`/home/z/my-project/download/03-newproject.png`（step5 含配置摘要与创建按钮）+ step1/step2-parsed/step3/step4 过程截图
- **agent-browser errors**：空（无控制台错误）
