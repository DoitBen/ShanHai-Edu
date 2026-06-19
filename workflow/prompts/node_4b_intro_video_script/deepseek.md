# Node 4B 导入视频文稿 — DeepSeek prompt
version: 1.0
provider: deepseek
node_id: intro_video_script

---

{{include shared/system_role.md}}

## 你的任务

为已 approved 的导入设计选择集，生成符合 schemas/intro_video_script.schema.json 的视频文稿 JSON。

**导入视频的核心目的不是讲数学，是给课堂开场一个抓人的钩子**。
学生看完视频会带着"这是什么？""为什么会这样？"的好奇进入正课。

## 输入

### 项目元数据
```json
{{project_meta}}
```

### 公开课教案（上游 approved）
```json
{{lesson_plan}}
```

### 导入设计选择集（上游 approved）
```json
{{intro_selection}}
```

{{include shared/seed_params_block.md}}
{{include shared/flywheel_samples_block.md}}

## 字段说明

| 字段 | 注意 |
|---|---|
| `total_duration_sec` | 完整短片选 60-120，短导入片选 10-15 |
| `video_type` | science / application / story，必须与选择集的 primary_design_id 一致 |
| `anchor_to_lesson` | 视频结尾如何自然引出本课题（10-20 字一句话） |
| `narration_full_text` | **完整中文旁白**。这段文字会被切片到分镜、做中文男声 TTS，所以**字数必须精确**：按 280 字/分钟换算（R040） |
| `narration_word_count` | 旁白字数（用于校验时长一致性） |
| `banned_elements` | **必须包含 ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"]**（R045） |

## 旁白风格要求

1. **第一句必须是钩子**——情境冲突、奇妙发现、谜题——直接抓住注意力
2. **中段保持悬念或冲突推进**，不要急着讲知识点
3. **结尾自然引到课题**，但不要让结尾"剧透"完整答案
4. **全程中文**，不得夹英文（R002 会查最终视频，但文稿就要起好头）
5. **不写教师话术 / 不写学生回答 / 不写课堂活动**——这些是 PPT 该承担的

## 时长 vs 字数对照参考

| 时长 | 旁白字数 |
|---|---|
| 60 秒 | 约 280 字 |
| 90 秒 | 约 420 字 |
| 120 秒 | 约 560 字 |
| 10 秒（短导入） | 约 45 字 |
| 15 秒（短导入） | 约 70 字 |

字数偏差超过 ±10% 会被 R040 警告。

## 红线

- banned_elements 不得遗漏任何一项强制项
- 旁白中不得出现"小朋友们好""同学们看一下"这类教师腔
- 不得在旁白里塞数学公式或精确数字（这些放进 PPT）

{{include shared/output_format_json.md}}
