# ShanHaiEdu 全链路打通冲刺文档

**版本**：v1.1 | **日期**：2026-06-21 | **面向**：后端架构师团队（4人）
**状态**：🔴 当前开发唯一重点，其他任务暂停

---

## 目标（唯一）

> 用户上传一份小学数学教材 PDF，填写课题和学情，点击各步骤"生成"，全程人工只做审核和确认，最终能下载一个 `.pptx` 文件，第 2 页是 AI 生成的导入视频。

链路通了就算完成。内容质量、UI 美观、性能优化本轮不考核。

---

## 已完成，不用再做

> 以下内容已在 T038-T041 中完成，本轮工程师不要重复实现。

- ✅ MinerU 3.2.0 已接入，PDF 上传后可触发解析，知识点列表已抽取并落盘
- ✅ 前端教材上传/解析 UI 已完成（上传、解析中状态、字段回填、知识点下拉、Markdown 预览）
- ✅ `lesson_plan/generate` 已读取知识点 Markdown 作为输入（输入管道通了，只差接真实 LLM）
- ✅ 视频脚本链 5 个节点（`intro_selection` / `intro_video_script` / `intro_video_screenplay` / `intro_video_asset` / `storyboard`）API 路由和前端 UI 全部存在，fake 数据可走通
- ✅ `final_video` 节点 fake task 创建和查询已通
- ✅ 端到端 fake 全链路回归已通过（T041）

---

## 不做什么（硬边界）

- 不做用户鉴权和多租户
- 不做内容质量审核和合规过滤
- 不做错误重试和断点续传
- 不做前端 UI 优化
- 不做性能优化
- 不做部署上线

---

## 三条并行轨道（4 人分配）

### 轨道 B｜工程师 1：LLM 基础设施 + 教案生成

**任务**：建 LLM 调用层，跑通第一个真实 AI 输出。

1. 封装 LLM 调用模块，通过环境变量切换 provider（`PROVIDER_MODE=real` 走真实 API，`fake` 走原有 mock，两种都要能用）
2. **使用 DeepSeek API**（`DEEPSEEK_API_KEY` 注入环境变量，不写入代码）
3. `lesson_plan/generate` 接真实 LLM，输入已有的知识点 Markdown，输出教案 Markdown，格式见【契约 2】
4. 顺带验证：上传非 fixture 的任意 PDF，知识点 Markdown 输出格式是否稳定符合契约 1（如有问题顺手修，不是主任务）

**可立即开始**：知识点 Markdown 输入管道已通（T040），直接对接 LLM 调用即可。

**LLM 模块要求**：轨道 C 直接复用，不要各自封装一套。

---

### 轨道 C｜工程师 2 + 3：视频脚本链（5 个节点接真实 LLM）

**任务**：教案进来，分镜 JSON 出去。复用轨道 B 的 LLM 模块，依次替换 fake 数据：

1. `intro_selection`：基于教案推荐 3 种视频导入方案，用户选一种
2. `intro_video_script`：生成视频总脚本
3. `intro_video_screenplay`：拆分为分场剧本
4. `intro_video_asset`：列出所需素材清单
5. `storyboard`：生成分镜 JSON，格式见【契约 3】

**可立即开始**：用契约 2 的 mock 教案 Markdown 先联调 LLM，B 完成后替换真实教案输入。

**注意**：LLM 模块由轨道 B 提供，不重复封装。

---

### 轨道 D｜工程师 4：视频生成 + PPT 导出

**任务**：分镜进来，PPT 出去。

1. `final_video/generate` 接真实视频生成 API（**provider 由项目负责人确认**，先用占位 MP4 打通后续流程）
2. 视频文件落盘到 `storage/projects/{project_id}/outputs/final_video.mp4`
3. **新增接口** `POST /projects/{id}/export/ppt`：
   - 用 `python-pptx` 生成 `.pptx`
   - 第 1 页：课题封面（项目标题 + 学科年级）
   - **第 2 页：嵌入 `final_video.mp4`**
   - 返回文件下载链接

**可立即开始**：用 5 秒占位 MP4 把 PPT 导出接口跑通，视频 provider 确认后替换真实视频文件。

---

## 三个接口契约（4 人对齐后不改）

### 契约 1：知识点 Markdown（已有，轨道 A 需验证格式稳定）

```markdown
# 教材：人教版小学数学一年级上册（2024）
## 单元：第一单元 准备课
### 知识点列表
- KP001 | 数数（1-10）| P.2-3
- KP002 | 比较多少 | P.4-5
- KP003 | 5以内数的认识 | P.6-8
## 选定知识点
KP003 | 5以内数的认识 | 适合2年级第一学期公开课
```

### 契约 2：教案 Markdown（B → C）

```markdown
# 教案：5以内数的认识
## 基本信息
- 年级：小学一年级 | 时长：40分钟 | 类型：新授课
## 教学目标
1. 认识1-5各数，会读写
2. 理解数的顺序和大小
## 教学环节
| 环节 | 内容 | 时长 |
|---|---|---|
| 导入 | 情境引入，引出"数一数" | 5分钟 |
| 新授 | 逐一认识1-5 | 15分钟 |
| 练习 | 数数游戏 | 10分钟 |
| 小结 | 梳理板书 | 5分钟 |
| 作业 | 数身边的物品 | 5分钟 |
```

### 契约 3：分镜 JSON（C → D）

```json
{
  "total_duration": 90,
  "shots": [
    {
      "id": "S001",
      "duration": 10,
      "scene": "教室情境",
      "subject": "5个苹果摆在桌上",
      "subtitle": "今天我们来认识5以内的数",
      "visual_type": "animation"
    }
  ]
}
```

---

## 环境变量（运维配置，工程师只读）

```bash
PROVIDER_MODE=real            # real | fake
DEEPSEEK_API_KEY=xxx          # 轨道 B / C 使用
VIDEO_API_KEY=xxx             # 轨道 D 使用（provider 确认后补充）
VIDEO_API_ENDPOINT=xxx        # 同上
```

---

## 联调顺序

```
Day 1：
  B：封装 LLM 模块，lesson_plan 接真实 DeepSeek，冒烟通过
  C：用 mock 教案跑通 intro_selection → storyboard LLM 调用
  D：用占位 MP4 跑通 POST /export/ppt，能下载 .pptx 且第 2 页有视频

Day 2：
  B → C 对接：B 输出真实教案 Markdown，C 替换 mock 输入
  D：等待视频 provider 确认，接入真实视频生成 API

Day 3：
  C → D 对接：C 输出真实分镜 JSON，D 用真实分镜触发视频生成
  全链路冒烟：PDF → 知识点 → 教案（真实）→ 脚本链（真实）→ 视频 → PPT 下载

Day 4：
  全链路联调修 bug，产品验收
```

---

## 遗留确认项（项目负责人今天回复）

- [ ] 视频生成 provider 用哪家？（可灵 / 即梦 / 其他）
- [ ] DeepSeek API Key 由谁分发？
