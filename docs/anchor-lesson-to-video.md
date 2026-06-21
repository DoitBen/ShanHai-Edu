# 课程锚点规范：教案 → 视频导入衔接点

**版本**：v1.0 | **日期**：2026-06-21  
**适用节点**：`lesson_plan` / `intro_selection` / `intro_video_script` / `storyboard` / `final_video`  
**地位**：教案与视频导入之间的唯一硬连接字段，所有角色必读。

---

## 一、什么是课程锚点

> 短视频和本课教案之间**唯一必须对齐的连接点**。  
> 它只负责把一个独立、有吸引力的视频主题，最后自然接回本课学习任务，**不负责提前讲解知识点**。

课程锚点回答一个问题：

> **这个视频最后，通过什么现象、问题、物品、冲突或任务，和本课课题发生关系？**

---

## 二、课程锚点是输出，也是约束

### 作为输出

`lesson_plan/generate` 必须为每套导入视频策划卡输出 `anchor_to_lesson` 字段（共 9 套）。

```json
{
  "intro_designs": [
    {
      "design_id": "design_story_01",
      "type": "story",
      "title": "小兔子搬萝卜",
      "hook": "小兔子面对一堆萝卜不知道要跑几趟",
      "anchor_to_lesson": "小兔子数不清萝卜，引出'数清楚了才知道要跑几趟'，自然进入5以内数的认识",
      "classroom_entry_question": "你们帮小兔子数一数，一共有几个萝卜？",
      "recommend_score": 88
    }
  ]
}
```

### 作为约束

用户在 `intro_selection` 确认（可修改）锚点后，该字段硬传入所有下游节点：

```
anchor_to_lesson（用户最终确认版）
  ↓
intro_video_script：旁白最后一句必须落在此
  ↓
storyboard：最后一个 shot 的 subtitle 必须体现此
  ↓
final_video：最后 10 秒画面和字幕
```

---

## 三、如何写课程锚点

### 格式

```
通过[具体现象 / 物品 / 冲突 / 问题 / 任务]，
自然引出[课题的核心学习任务或悬念]。
```

字数建议：**15-40 字**，一句话，不分行。

### 合格示例

| 课题 | 锚点写法 |
|---|---|
| 5以内数的认识 | 小兔子不知道5个萝卜要跑几趟才能搬完，引出"数清楚才能解决问题" |
| 认识三角形 | 桥梁、塔吊、屋顶反复出现三角形，引出"为什么它们都选三角形" |
| 平均分 | 两个小朋友分饼干分不公平吵起来了，引出"怎样分才算公平" |
| 20以内退位减法 | 小店老板找零找错了，引出"怎么快速算出要找多少钱" |

### 不合格示例

| 写法 | 问题 |
|---|---|
| "引出本课数学内容" | 太模糊，AI 无法依据此生成具体结尾画面 |
| "让学生理解5以内数的含义" | 这是教学目标，不是锚点 |
| "教学目标对应点：认识1-5" | 禁止用此说法替代课程锚点 |
| "视频讲完1-5怎么数，再进入课堂" | 提前讲解了知识点，违反边界 |
| "引出课堂探究活动" | 把课堂流程搬进视频，违反视频独立性原则 |

---

## 四、课程锚点的边界

视频可以做的：
- 故事任务、冲突悬念、奇妙发现、现实应用、历史由来、科学现象
- 视频主体与课堂流程无关也没关系
- 结尾用锚点自然过渡到课题

视频不能做的：
- 提前讲本课核心定义、方法、结论
- 模仿教师上课话术（"同学们，今天我们来学……"）
- 把课堂探究步骤提前演示一遍
- 出现真实未成年人（合规红线）

---

## 五、各节点对课程锚点的使用要求

### lesson_plan（输出方）

- 每套导入视频策划卡必须包含 `anchor_to_lesson` 字段
- 9 套锚点必须各不相同，不能只是换一种说法
- 锚点必须具体到"通过什么"，不能是抽象目标描述

### intro_selection（用户确认方）

- 向用户展示 9 套策划卡及其锚点
- 用户可修改选定套的锚点文本
- **用户点击确认前，视频生成链不得启动**（人工停顿强制门禁）
- 确认后的锚点为最终版，写入 `selected_anchor`

### intro_video_script（消费方）

- 接收 `selected_anchor` 作为硬输入
- `narration_full_text` 的最后一句必须体现锚点内容
- 不得修改或忽略锚点的核心指向

### storyboard（消费方）

- 最后一个 shot 的 `subtitle` 必须体现锚点关键词
- `model_prompt` 的画面描述必须与锚点一致
- approve 前系统检查：最后一个 shot subtitle 是否覆盖锚点关键词

### final_video（消费方）

- 最后 10 秒片段的字幕和旁白必须落在锚点上
- 锚点关键词列入视频 QA 审核清单

---

## 六、机器可验规则（待补入 rules.md）

| 规则 ID | 触发节点 | 触发时机 | 检查内容 | 级别 |
|---|---|---|---|---|
| R046 | lesson_plan | on_generate | 每套 intro_design 必须有非空 anchor_to_lesson | hard_block |
| R047 | intro_selection | on_approve_attempt | selected_anchor 非空且字数 ≥ 10 | hard_block |
| R048 | intro_video_script | on_generate | 接收到 selected_anchor 且非空 | hard_block |
| R049 | storyboard | on_approve_attempt | 最后一个 shot.subtitle 包含 selected_anchor 的核心关键词 | warning |

---

## 七、字段速查

| 字段名 | 所在节点 | 类型 | 说明 |
|---|---|---|---|
| `anchor_to_lesson` | lesson_plan.intro_designs[] | string | AI 生成的候选锚点，每套一个 |
| `selected_anchor` | intro_selection | string | 用户确认（可编辑）的最终锚点 |
| `narration_full_text` | intro_video_script | string | 旁白最后一句必须落在 selected_anchor |
| `shots[-1].subtitle` | storyboard | string | 最后一个镜头字幕必须体现 selected_anchor |
