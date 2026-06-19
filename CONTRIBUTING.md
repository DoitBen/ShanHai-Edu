# 贡献指南

ShanHai-Edu 是有"宪法"的项目。在写代码前请先读：

1. `README.md` — 项目入口
2. `docs/PRD.md` — 产品决策
3. `docs/TECH_ROADMAP.md` — 技术路线和模块拆解
4. `workflow/README.md` — 工作流总览
5. `workflow/workflow.yaml` — 调度总枢纽（最重要）

## 修改原则

### 不能擅自修改的（必须走产品决策）

- 9 步流程结构（`workflow/workflow.yaml > nodes`）
- 状态机（`workflow/workflow.yaml > states / transitions`）
- 产品红线（`workflow/workflow.yaml > hard_constraints`）
- 词表（动作 / 页面类型 / 核心素养）
- 红线规则 R001-R006

### 可以提 PR 修改的

- 添加新字段（schemas/*.json）
- 添加新规则（rules/R{nnn}.yaml + index.yaml）
- 改 prompt（prompts/）
- 写代码（apps/）

### 修改规则 / schema / workflow.yaml 必须

- 改一处，相关引用都要同步检查
- workflow.yaml 改动必须 review（产品 + 教学法负责人）
- 写明 `legacy_source` 让规则可追溯（如果是来自原历史规范）

## 提 PR 流程

1. 从 main 拉新分支：`git checkout -b feat/xxx` 或 `fix/xxx`
2. 改完跑本地校验（详见 docs/TECH_ROADMAP.md 第 9.2 节 CI 检查）
3. PR 描述要说明：改了什么、为什么改、影响哪些下游
4. 至少 1 个 reviewer 通过才合并

## Commit 规范

格式：`<type>(<scope>): <subject>`

- `type`: feat / fix / docs / refactor / test / chore / spec
- `scope`: 模块名（workflow / schemas / rules / prompts / api / web / docs）
- 例：
  - `feat(rules): add R025 info density limit`
  - `fix(schemas): correct character_dict required fields`
  - `docs(history): add 08_v1_kickoff.md`

## 历史文档不动

`history/` 目录的文件是决策档案，**不要修改历史**。
要补充新的决策记录，按时间顺序加新文件（如 `08_v1_kickoff.md`）。

## 红线（不可被任何 PR 推翻）

1. 中文男声 + 禁英文配音
2. 禁真人未成年
3. 完整视频必须多分镜拼接
4. 候选不能伪装终版
5. 角色字典禁 photorealistic
6. 数学事实必须进可编辑文本层

详见 `workflow/workflow.yaml > hard_constraints`。
