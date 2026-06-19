# state_machine.md — 状态机

版本：v1
角色：定义节点状态、转换规则、连锁失效逻辑。后端状态引擎按此实现。

## 状态枚举

| 状态 | 含义 | 下游可读？ |
|---|---|---|
| `not_started` | 尚未开始 | 否 |
| `drafted` | AI 已生成草稿，未提交审查 | 否 |
| `needs_review` | 已提交审查，等待用户 approve | 否 |
| `approved` | 已确认，下游可读 | **是** |
| `blocked` | 缺资料 / 接口受限 / 质量不达标 | 否 |
| `skipped` | 用户主动跳过该节点 | **是（等价 approved，下游视为通过）** |

`approved` 和 `skipped` 是仅有的两个"下游可读"状态。其他状态下游不得读取。

## 状态转换规则

```
[not_started]
    │
    │ AI 首次生成
    ↓
[drafted]
    │
    │ 提交给用户审查
    ↓
[needs_review]
    │
    ├─ 用户编辑 ──→ [drafted]   （编辑产生新版本，回到 drafted）
    ├─ 用户重做 ──→ [drafted]   （AI 重做产生新版本，回到 drafted）
    ├─ 用户 approve ──→ [approved]
    └─ 用户标记阻断 ──→ [blocked]

[approved]
    │
    ├─ 上游变更 ──→ [needs_review]   （连锁失效降级）
    ├─ 用户主动编辑 ──→ [drafted]
    └─ 用户主动重做 ──→ [drafted]

[blocked]
    │
    └─ 用户解除阻断 ──→ [drafted]

[skipped]
    │
    └─ 用户取消跳过 ──→ [not_started]
```

## 转换的触发源

| 转换 | 触发源 |
|---|---|
| not_started → drafted | AI 自动生成或用户首次进入节点 |
| drafted → needs_review | AI 生成完成 / 用户保存编辑 |
| needs_review → approved | 用户点 approve（必须先通过规则检查，见 `rules.md`） |
| needs_review → drafted | 用户重做 / 用户继续编辑 |
| approved → needs_review | 上游版本变更（连锁失效） |
| approved → drafted | 用户主动重做或编辑（绕过 needs_review） |
| 任何 → blocked | 用户手动 / 规则强阻断（hard_block 级规则命中） |
| not_started → skipped | 配置驱动（如 `needs_intro_video=false` 时第 4B-6 整条分支） |
| skipped → not_started | 用户取消跳过 |

## 版本与状态的关系

- 每次 drafted → needs_review 产生一个新 node_version 记录
- approve 时只是把 node_version.is_current=true 标记并把状态变 approved，不产生新版本
- 历史版本永久保留（除非项目硬删除）
- 回滚 = 把旧版本 is_current 改 true，旧版本状态自动变为 approved，新版本状态降级为 needs_review

## 连锁失效（核心机制）

### 触发条件

任一节点的 current 版本变化（上游 approved → 上游变更 → 上游回到 needs_review/drafted，或上游 current 指针切到其他版本）时，下游所有 `approved` 节点自动降级为 `needs_review`。

### 降级范围

按节点依赖图传播：

```
节点 1 教案
   │
   ├─→ 节点 1.5 选择集（PPT 分支不依赖此节点）
   ├─→ 节点 2 PPT 总装方案
   └─→ （间接传播到所有后续节点）

节点 1.5 选择集
   │
   ├─→ 节点 4B 视频文稿
   └─→ （间接传播到 4C/5B/6/8）

节点 2 PPT 总装方案
   │
   └─→ 节点 3 PPT 页面脚本
        │
        ├─→ 节点 5A PPT 视觉资产
        └─→ 节点 7 PPT 装配

节点 4C 视频剧本
   │
   ├─→ 节点 5B 视频资产
   └─→ 节点 6 分镜脚本
        │
        └─→ 节点 8 视频生成
```

### 降级规则

| 上游变化类型 | 下游处理 |
|---|---|
| 上游 approved → drafted/needs_review | 所有下游 approved → needs_review |
| 上游 approved → approved（current 切换到其他版本） | 所有下游 approved → needs_review |
| 上游 approved 不变，只是 metadata 改 | 不触发降级 |
| 上游 approved → skipped | 不触发降级（只是断开分支） |
| 上游 skipped → not_started | 触发该分支重新进入 not_started |

### 降级不删除内容

- 下游的 current 版本内容**保留**，只是状态变 needs_review
- 用户可选择"仍然 approve"（如果判断没受影响）
- 用户可选择"AI 重做"或"手动编辑"

## v1 不做的连锁机制（推到 v2+）

- diff 预览面板（v2）
- 影响范围智能分析（v2，AI 告诉用户具体哪几段下游受影响）
- 批量应用 / 全部接受（v3，按依赖序自动重生 + 自动 approve）

v1 简单粗暴：上游一变，下游全降级，用户挨个重审。这是安全兜底，绝不会偷偷过期。

## hard_block 强阻断机制

`rules.md` 中 `severity=hard_block` 的规则命中时：

1. 当前节点状态 → `blocked`
2. **不允许 approve**，不允许进入下一步
3. UI 显示阻断原因（来自规则定义）
4. 用户必须修复（编辑 / 重做）后才能解除

hard_block 来源：产品红线（角色字典禁用关键词、视频英文配音检测、单段冒充终版等）。

## warning 软警告机制

`rules.md` 中 `severity=warning` 的规则命中时：

1. 当前节点状态不变
2. UI 红字提示
3. **允许用户 override approve**
4. override 记录到 `user_preference_profile.overridden_rules` 用于飞轮

## skipped 状态的传播

第 0 步配置触发的批量 skipped：

| 配置 | 影响节点 |
|---|---|
| `needs_intro_video=false` | 第 1.5 / 4B / 4C / 5B / 6 / 8 全部置 skipped |
| `embed_video_in_ppt=false` | 第 7 步不读取视频产物（视频可独立交付） |

skipped 节点对收尾门禁的影响：

- 第 9 步 `final_delivery_gate.py` 检查时，skipped 节点视为"通过"
- 但不能所有视频分支节点都 skipped 还宣称"完整教学视频已交付"，必须配合 `intro_video_type=short_10_15s` 或 `needs_intro_video=false` 一致才合法

## 状态的持久化

- 当前状态写到 `node_versions.status` 字段
- 状态变化事件写到 `state_transition_log` 表（用于审计、飞轮、错误恢复）

### state_transition_log 字段

| 字段 | 类型 |
|---|---|
| transition_id | string |
| project_id | string |
| node_id | string |
| from_status | enum |
| to_status | enum |
| trigger | enum（ai_generate / user_edit / user_redo / user_approve / cascade_invalidate / hard_block / config_change） |
| triggered_at | datetime |
| triggered_by_user_id | string |
| version_id_before | string |
| version_id_after | string |

## 异常恢复

### 程序崩溃 / 网络断

如果状态转换中途崩溃：

- 状态变更必须是 atomic 写入（先写 state_transition_log + 更新 node_versions.status，事务提交）
- 启动时检查"最近一次 transition 是否有对应的 status 更新"，不一致则按 transition_log 修复

### 用户在 needs_review 时离开

- 状态保持 needs_review，下次回来直接进审查界面
- 自动保存的草稿编辑不丢失

### 多标签同时修改同一节点

v1 简单做：检测到第二标签打开同一项目时提示"建议只开一个窗口"。不做悲观锁、不做实时同步。

## 与门禁脚本的关系

现有 9 个门禁脚本不在状态机内运行，作为 rules.md 的执行器之一。状态引擎调用规则，规则的实现可以是：

- 内置 Python 检查函数
- 调用现有 `scripts/*.py` 门禁
- 调用审查智能体（Claude）

状态机本身不关心规则怎么实现，只关心规则返回的 pass / warning / hard_block 结果。
