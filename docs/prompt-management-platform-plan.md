# Prompt 管理平台实施方案（B 档落地）

**版本**：v1.0
**日期**：2026-06-21
**裁决**：首席系统架构师 + 用户
**状态**：已批准，立即下发实施

---

## 一、为什么做这件事

### 1.1 当前事故

- `apps/api/app/services.py._build_prompt`（L571-633）把所有节点 prompt 硬编码在 Python 字符串中。
- `workflow/prompts/{node_id}/{provider}.md` 目录下 7 个 prompt 文件**完全没有被后端读取**。
- 直接后果：2026-06-21 升级 `node_01_lesson_plan/deepseek.md` 到 v1.1（加两层结构、加锚点定义）**根本没生效**，线上跑的还是 `services.py` 里的旧版字符串。

### 1.2 这件事的代价

- 教学法负责人 / 产品 / 管理员**无法独立改 prompt**，每次都要工程师改代码 → 部署。
- 工作流文档（`workflow/prompts/`）与实际行为持续漂移，越改越远。
- 跨 provider 切换（DeepSeek/Claude/GPT）的 prompt 矩阵无法落地。
- A/B 测试和 prompt 灰度发布完全不可能。
- prompt 改坏了只能 git revert，不是切版本号。

### 1.3 用户身份边界（不可触碰）

- **普通用户（李雪老师 P01）**：只能体验我们设定好的工作流，**看不到 prompt 管理后台**，**不能修改任何 prompt**。
- **管理员（教学法负责人 / 首席系统架构师）**：通过独立后台界面修改 prompt，需登录 + 角色校验。
- 角色分离硬约束：用户态前端代码包内**不得**出现 prompt 编辑组件，避免误暴露。

---

## 二、目标方案：B 档（文件 + 数据库覆盖 + 管理后台 UI）

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────┐
│  workflow/prompts/{node_id}/{provider}.md（Git 默认版）  │
│  ↓ 部署时 seed 进数据库（仅当库内尚无该节点+provider 记录）│
├─────────────────────────────────────────────────────────┤
│  prompt_versions 表（运行时真源）                        │
│  - 多版本留痕                                           │
│  - 可灰度 / 可回滚 / 可对比                              │
│  ↓                                                      │
│  PromptRegistry（后端运行时缓存 + TTL 失效）              │
│  ↓                                                      │
│  services._build_prompt(node_id, provider)               │
│    → PromptRegistry.get(node_id, provider)               │
│      ① 优先取数据库 active 版本                          │
│      ② 库内缺失 → 读 workflow/prompts/ 文件作为 fallback │
│      ③ 文件也缺失 → 抛 PROMPT_TEMPLATE_MISSING           │
└─────────────────────────────────────────────────────────┘

管理员后台（独立 /admin/prompts 路由 + 权限门禁）：
  - 列表：所有节点 × provider × 当前 active 版本
  - 编辑器：Markdown 编辑 + 变量预览 + 旁挂"测试生成"
  - 版本：每次保存生成新版本号；可对比；可回滚
  - 灰度：支持 active / draft / canary（按比例）
```

### 2.2 数据模型（新增 SQLite 表）

```sql
CREATE TABLE prompt_templates (
  template_id TEXT PRIMARY KEY,           -- 形式 lesson_plan@deepseek
  node_id TEXT NOT NULL,
  provider TEXT NOT NULL,                  -- deepseek/claude/gpt/...
  description TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(node_id, provider)
);

CREATE TABLE prompt_versions (
  version_id TEXT PRIMARY KEY,             -- UUID
  template_id TEXT NOT NULL,
  version_number INTEGER NOT NULL,         -- 1, 2, 3...
  body TEXT NOT NULL,                      -- prompt 正文（含 {{var}} 占位符）
  variables_json TEXT NOT NULL,            -- 声明的变量列表
  status TEXT NOT NULL,                    -- draft / active / canary / archived
  canary_percent INTEGER DEFAULT 0,        -- canary 时百分比
  source TEXT NOT NULL,                    -- file_seed / admin_edit
  source_file_path TEXT,                   -- 来自 file_seed 时记录文件路径
  notes TEXT,                              -- 修改说明（管理员填）
  created_by TEXT NOT NULL,                -- 管理员账号
  created_at TEXT NOT NULL,
  activated_at TEXT,                       -- 进入 active 时间
  FOREIGN KEY (template_id) REFERENCES prompt_templates(template_id)
);

CREATE INDEX idx_prompt_versions_lookup ON prompt_versions(template_id, status);

CREATE TABLE prompt_usage_log (
  log_id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  project_id TEXT,                         -- 触发哪个项目
  node_id TEXT NOT NULL,
  invoked_at TEXT NOT NULL,
  -- 不记录 prompt 全文，避免 PII / 密钥泄漏
  -- 飞轮信号在 user_preference_profile 已有，不重复
  success INTEGER NOT NULL
);
```

**关键设计：active 唯一性约束**
- 同一 `(node_id, provider)` 下，`status=active` 的版本**有且仅有 1 个**。
- 切换 active 时，旧 active 自动转 `archived`，新版本进 active；原子事务。

### 2.3 后端 PromptRegistry 组件

```python
# apps/api/app/prompt_registry.py（新增）

class PromptRegistry:
    """运行时 prompt 模板解析器，单例。"""

    def __init__(self, store: PromptStore, file_root: Path, cache_ttl_seconds: int = 30):
        self._store = store
        self._file_root = file_root  # workflow/prompts/
        self._cache: dict[str, CachedPrompt] = {}
        self._cache_ttl = cache_ttl_seconds

    def get(self, node_id: str, provider: str) -> PromptTemplate:
        """按 (node_id, provider) 取当前生效 prompt。

        优先级：
        1. DB active 版本（含 canary 路由）
        2. workflow/prompts/{node_id}/{provider}.md 文件
        3. 抛 PROMPT_TEMPLATE_MISSING
        """

    def render(self, template: PromptTemplate, context: dict) -> str:
        """变量替换（{{var}} → value），缺失变量抛 PROMPT_VARIABLE_MISSING。"""

    def invalidate(self, node_id: str = None, provider: str = None) -> None:
        """管理员保存新版本后调用，清相关缓存。"""
```

**services.py 改造**：

```python
def _build_prompt(self, node_id: str, provider: str, context: dict) -> str:
    template = self._prompt_registry.get(node_id, provider)
    return self._prompt_registry.render(template, context)
```

原 `_build_prompt` 中所有硬编码字符串全部废除。

### 2.4 文件 → DB 的 seeding 机制

- 应用启动时执行 `PromptStore.ensure_seeded()`：
  - 遍历 `workflow/prompts/{node_id}/{provider}.md`
  - 对每个文件，检查 DB 中是否已有对应 `(node_id, provider)` 的任何版本
  - 若**完全没有**：从文件读取内容，创建 template + version 1，status=active，source=file_seed
  - 若已有版本：**不覆盖**（管理员可能已经在后台改过了）
- 这保证了两件事：
  - 新部署的环境能直接跑起来（无需先手工创建 prompt）
  - 不会用 Git 里的旧文件覆盖后台已编辑的最新版

**额外提供管理员命令**：
- `python -m apps.api.tools.prompt_sync --from-file --node lesson_plan --provider deepseek`：强制把文件 reseed 为新版本（管理员决策，留痕）
- `python -m apps.api.tools.prompt_sync --to-file --node lesson_plan --provider deepseek`：把 DB active 版本导出回文件（用于 Git 提交基线）

### 2.5 管理员后台 UI

**路由**：`apps/web/src/app/admin/prompts/`，与用户态 `apps/web/src/app/(app)/` 完全隔离。

**权限门禁**：
- 后端中间件：`/admin/*` 路径必须携带管理员 JWT；非管理员返回 403
- 前端：路由级守卫；非管理员访问跳转 404，不显示"无权限"提示（避免暴露后台存在）
- v1 阶段管理员账号由环境变量配置（`ADMIN_USERNAMES=archi,teaching_lead`），v1.x 接入正式账号系统

**主页面（4 个）**：

| 页面 | 路由 | 功能 |
|---|---|---|
| 模板列表 | `/admin/prompts` | 表格：node × provider × active version × 最后修改人 / 时间；筛选、搜索 |
| 模板编辑器 | `/admin/prompts/{node_id}/{provider}` | 左：Markdown 编辑器（CodeMirror）；右：变量声明 + 预览渲染（用 fixture context）；底部"保存为草稿" / "发布为 active" / "灰度发布" |
| 版本历史 | `/admin/prompts/{node_id}/{provider}/history` | 时间线 + 任意两版本 diff；一键回滚 |
| 操作日志 | `/admin/prompts/audit` | 谁在什么时间改了什么 prompt（不显示 prompt 内容，只显示元数据） |

**编辑器关键能力**：
- 变量占位符语法 `{{project_meta}}` / `{{selected_knowledge_point_markdown}}` 等
- `{{include shared/system_role.md}}` 共享片段引用（保持与 Git 文件相同语义）
- 保存时自动 lint：必填变量是否声明、include 路径是否存在
- 旁挂"试运行"按钮：用一组 fixture 数据真实调用 LLM 生成一次，让管理员对比效果（**只用 fake provider 或 DeepSeek 测试模型，不消耗真实生产配额**）

### 2.6 灰度发布机制

`prompt_versions.status` 取值与路由逻辑：

| status | 行为 |
|---|---|
| `draft` | 管理员草稿，不影响生产 |
| `canary` | 按 `canary_percent` 抽样，例如 10% 流量走新版本 |
| `active` | 当前生产默认版本 |
| `archived` | 历史版本，可回滚到此版本 |

canary 抽样依据：`hash(project_id + node_id) % 100 < canary_percent`，保证同一项目多次生成走同一版本（避免同项目内 prompt 抖动）。

灰度期间 `prompt_usage_log` 记录每次调用用了哪个版本，便于管理员对比生成质量后决定是否转正。

### 2.7 安全与合规

| 项 | 措施 |
|---|---|
| 普通用户接触面 | 前端 admin 路由文件不打包进用户态 bundle（Next.js 分组路由 + 构建排除） |
| 管理员鉴权 | JWT + 服务端中间件 + 前端路由守卫双重校验 |
| Prompt 内容审计 | 所有 prompt_versions 写入留痕，不删除（archived 而非 delete） |
| 敏感变量 | prompt 里禁止出现真实密钥、token；服务端注入 context 时只允许白名单字段 |
| 试运行成本控制 | 仅用 fake provider 或专用测试模型；单次试运行成本不超过 ¥1 |
| 跨租户隔离 | v1 内部单租户，prompt 全局生效；v1.x 外销时增加 `tenant_id` 字段 |

---

## 三、实施计划（5 阶段，预计 8 个工作日）

### 阶段 1：止血（D1，半天）

**目标**：让 `services._build_prompt` 改读 `workflow/prompts/` 文件，硬编码作为 fallback。先解决 prompt 漂移，不引入数据库。

**任务**：T058（后端工程师）

**交付**：
- 新增 `apps/api/app/prompt_loader.py`：从文件读取 + 占位符渲染
- 改造 `services.py._build_prompt`：调用 prompt_loader
- 保留硬编码作为兜底（文件读不到时使用，但记 warning 日志）
- 单元测试覆盖文件读取、变量替换、include 展开

**验收**：
- `python -m pytest apps/api/tests/test_prompt_loader.py -q` 通过
- 真实 smoke：调一次 lesson_plan/generate，确认返回内容反映 `node_01_lesson_plan/deepseek.md` v1.1 两层结构（即"修复了刚才那次工作没生效"的问题）

### 阶段 2：数据库 + Registry（D2-D3）

**目标**：建表、写 PromptRegistry、文件 seed 进 DB。

**任务**：T059（后端工程师）

**交付**：
- 新增 SQLite 表：`prompt_templates` / `prompt_versions` / `prompt_usage_log`
- 新增 `apps/api/app/prompt_registry.py`：DB 优先 + 文件 fallback + TTL 缓存
- 新增 `prompt_sync` 命令工具：`--from-file` / `--to-file`
- 启动时 `ensure_seeded()`：把 `workflow/prompts/` 现有文件灌入 DB（首次）

**验收**：
- 后端启动后查询 DB：所有现有节点 prompt 都有 active 版本
- 单元测试覆盖 seed 幂等性、active 唯一性、缓存失效

### 阶段 3：管理员 API（D4）

**目标**：提供 CRUD + 版本切换 API，前端管理后台调用。

**任务**：T060（后端工程师）

**交付**：
- 新增 `apps/api/app/routes/admin_prompts.py`：
  - `GET /admin/prompts/templates` 列表
  - `GET /admin/prompts/templates/{template_id}` 详情含全部版本
  - `POST /admin/prompts/templates/{template_id}/versions` 新建版本（draft / active / canary）
  - `POST /admin/prompts/templates/{template_id}/activate` 切换 active
  - `POST /admin/prompts/templates/{template_id}/rollback` 回滚到指定历史版本
  - `POST /admin/prompts/templates/{template_id}/test-run` 试运行（用 fake provider）
- 新增 `admin_auth` 中间件：校验 JWT 中 `role=admin`
- 所有写操作记入 `prompt_usage_log` / audit log

**验收**：
- pytest 覆盖：管理员能 CRUD，普通用户 403，非法 JWT 401
- contract 测试：active 切换原子性、回滚不破坏历史

### 阶段 4：管理员后台 UI（D5-D7）

**目标**：4 个页面 + 编辑器 + 灰度控件。

**任务**：T061（前端工程师）

**交付**：
- `apps/web/src/app/admin/prompts/page.tsx`：模板列表
- `apps/web/src/app/admin/prompts/[node]/[provider]/page.tsx`：编辑器（CodeMirror + Markdown 预览）
- `apps/web/src/app/admin/prompts/[node]/[provider]/history/page.tsx`：版本时间线 + diff
- `apps/web/src/app/admin/prompts/audit/page.tsx`：操作日志
- 用户态构建产物不包含 admin 代码（Next config 排除）
- 管理员登录入口（v1 简单的 username + token 校验，v1.x 接正式账号）

**验收**：
- 浏览器实测：管理员可登录、可编辑 `lesson_plan@deepseek`、可保存新版本、可看历史、可回滚、可灰度 10%
- 用户态访问 `/admin/prompts` → 404（不暴露后台存在）
- typecheck / lint / build 全通过

### 阶段 5：联调验收 + 文档（D8）

**任务**：T062（测试工程师）+ T063（架构师复核）

**交付**：
- 端到端测试：管理员改 prompt → 切 active → 用户态生成节点 → 确认新 prompt 已生效
- 灰度测试：50% 流量走新版本，统计两边生成结果差异
- 回滚演练：故意发布"坏 prompt" → 一键回滚 → 验证立刻恢复
- 文档：
  - `docs/prompt-platform-admin-guide.md`：管理员操作手册
  - `docs/prompt-platform-architecture.md`：架构说明（含数据流、缓存策略、灰度算法）
- 更新 `workflow/prompts/README.md`：说明文件现在是"Git 基线 / 默认值"，DB 才是运行时真源

---

## 四、不做什么（明确推迟）

| 推迟项 | 推到 |
|---|---|
| 多租户 prompt 隔离 | v1.x 外销时 |
| Prompt 性能效果指标（生成质量自动评分） | 飞轮数据攒够后 |
| Prompt 变量类型校验（schema 化） | v1.1 |
| 多语言 prompt | 不在 v1 范围 |
| Prompt marketplace（社区共享） | v3+ |
| Prompt 实验平台（多臂赌博机） | v2+ |
| 复杂权限分级（review / approve 角色） | v1.x |

---

## 五、对其他模块的影响

### 5.1 工作流文档定位变化

`workflow/prompts/*.md` 的角色从"装饰文档"变成"Git 默认基线 + 灾难恢复源"：
- 新部署环境靠这些文件 seed
- DB 损坏时可从这些文件重建
- 管理员可用 `prompt_sync --to-file` 把 DB 当前 active 导出回 Git，作为版本基线

需要在 `workflow/prompts/README.md` 写清楚这套规则，避免后续团队成员误以为改文件能改线上行为。

### 5.2 与 rules.md 的协同

rules.md 仍是规则真源，prompt 平台不替代它。两者协同：
- rules.md：定义"什么不能违反"（机器可验，硬阻断或 warning）
- prompt：定义"如何指导 AI 生成"（软约束 + 引导）

未来 v1.x 可以考虑也把 rules.md 做成"规则管理后台"，但本期不做。

### 5.3 dispatch.md 更新

新增 T058-T063（本方案任务）+ T064-T068（审计 P0 修复中其他项）。

### 5.4 架构师 T057 收口

T057 锚点全码排查已通过本次三路审计完成，结论已写入 `docs/qa-audits/2026-06-21-workflow-compliance-audit.md`，本方案是 T057 的延续修复方案。

---

## 六、关键风险与缓解

| 风险 | 缓解 |
|---|---|
| 管理员误改 prompt 导致生产异常 | 灰度发布 + 一键回滚 + 操作日志 |
| Prompt 平台本身故障 | 文件 fallback；Registry 启动时如果 DB 不可用，降级为只读文件模式 |
| 不同 provider 切换时 prompt 没适配 | 每个 (node, provider) 独立 prompt，文件目录天然支持 |
| 管理员后台权限被绕过 | 前端不暴露 + 后端中间件双重校验 + 用户态 bundle 不含 admin 代码 |
| 试运行成本失控 | 仅用 fake provider 或专用测试 endpoint；单次预算上限 |
| 文件 / DB 漂移失控 | `prompt_sync` 工具 + CI 提示（DB 有变更未导出回文件时警告） |

---

## 七、验收标准

整个 prompt 平台 GA 当且仅当：

1. ✅ `services.py` 中无任何硬编码 prompt 字符串
2. ✅ 管理员能通过后台 UI 编辑 `lesson_plan@deepseek` 并发布，生效在 30 秒内
3. ✅ 修改 prompt 后无需重启后端
4. ✅ 普通用户访问 `/admin/*` 返回 404
5. ✅ Prompt 改坏后能在 1 分钟内回滚到上一版本
6. ✅ 所有现有节点 prompt（≥7 个）都已从 `workflow/prompts/` seed 进 DB
7. ✅ 灰度发布按 canary_percent 正确路由
8. ✅ 单元 + 契约 + E2E 测试通过
9. ✅ 管理员操作手册 + 架构文档已写入 `docs/`
10. ✅ 用户态 build 产物经过 grep 不含"admin"路径相关代码

---

## 八、本方案的副产品

落地后，下列长期问题自动解决或获得抓手：

- ✅ 我之前对 `node_01_lesson_plan/deepseek.md` v1.1 的修改自动生效
- ✅ T070（跨 provider prompt 矩阵）有了承载平台，只需补 `claude.md` / `gpt.md` 文件
- ✅ T065（R046 黑名单扩展）等"在 prompt 里多写几条约束"的任务变成在管理后台改字，不再需要发版
- ✅ 飞轮信号"用户高频 override 哪条规则"可以反向指导管理员调 prompt
- ✅ 教学法负责人独立维护 prompt 的能力（PRD 8.3 路径打通）
