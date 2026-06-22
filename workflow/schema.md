# schema.md — 字段定义

版本：v1
角色：所有节点产物的字段结构定义。后端建表、前端建表单、AI 生成时填字段，均以此为准。

## 通用约定

- 所有字段名用 snake_case
- 枚举值用小写英文（前端展示时映射为中文）
- 必填字段标 `required`，可选标 `optional`
- 字段长度上限不在此定义，进 `rules.md`

## 项目元数据（project_meta）

第 0 步表单填写，整个项目生命周期不变。

| 字段 | 类型 | 必填 | 取值 | 说明 |
|---|---|---|---|---|
| project_id | string | required | UUID | 系统生成 |
| project_name | string | required | 用户填课题 | 唯一标识，slug 化用于路径 |
| subject | enum | required | math | v1 仅数学 |
| grade | enum | required | 1 / 2 / 3 / 4 / 5 / 6 | 年级 |
| textbook_version | enum | required | renjiao / beishida / sujiao / xishida / other | 教材版本 |
| volume | enum | required | shang / xia | 上册 / 下册 |
| lesson_type | enum | required | public / regular / review / practice | 课型 |
| lesson_duration_min | int | required | 35 / 40 | 课时长度（分钟） |
| created_at | datetime | required | 系统填 | 创建时间 |
| deadline_at | datetime | optional | 用户填 | 预计上课时间（用于紧急模式） |

## 配置（project_config）

第 0 步表单可改、影响下游分支。

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| needs_intro_video | bool | true | false 时第 1.5/4B/4C/5B/6/8 步置 skipped |
| intro_video_type | enum | full_60_120s | full_60_120s / short_10_15s |
| ppt_page_range | tuple<int,int> | (12, 16) | PPT 目标页数范围 |
| visual_richness | enum | mid | low / mid / high |
| embed_video_in_ppt | bool | false | PPT 是否嵌入视频 |
| intro_design_types | set<enum> | {science, application, story} | 三类九套覆盖范围 |
| designs_per_type | int | 3 | 每类方案数 |

## 视觉契约（visual_contract）

第 0 步定义。PPT 和视频两条分支都引用同一份。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| palette | list<color> | required | 3-5 个主色（HEX） |
| style_keywords | list<string> | required | 例：flat / 3d / hand_drawn / gradient |
| font_preference | string | optional | 字体偏好 |
| template_pptx | file | optional | 学校模板上传（v1 起步层：提取色彩/字体/版式） |

## 角色字典（character_dict）

第 0 步定义。每个角色一条记录，跨节点引用。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| character_id | string | required | `char_xiaoming` 形式，唯一 |
| name | string | required | 中文名 |
| identity | string | required | 身份描述，例"二年级学生" |
| view_front | string | required | 正面外观描述 |
| view_side | string | required | 侧面外观描述 |
| view_back | string | required | 背面外观描述 |
| view_half | string | optional | 半身特写 |
| view_hand | string | optional | 手部特写 |
| outfit_lock | object | required | { color, style, accessories } |
| hair_lock | string | required | 发型锁定 |
| body_proportion | string | required | 体型 / 比例 |
| style_constraint | enum | required | cartoon / silhouette / 3d_non_realistic |
| banned_keywords | list<string> | required | 例：["真人", "photorealistic", "real child"]，**不可删除** |
| reference_image | file | optional | 参考图 |

合规底线：`style_constraint` 不能是 realistic / photorealistic；`banned_keywords` 至少包含三项默认硬约束。

## 节点 1：公开课教案（lesson_plan，粗粒度 6 字段）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| textbook_anchor | text | required | 教材依据（版本/册次/单元/页码） |
| teaching_objectives | text | required | 教学目标 |
| key_difficulty | text | required | 教学重难点 |
| teaching_flow | text | required | 教学流程 |
| blackboard_design | text | required | 板书设计 |
| intro_designs | list<intro_design> | required | 三类九套导入设计，结构化 |

### intro_design 子结构

每套策划卡必须有两层结构：层一独立创意（视频本身），层二课堂接入（锚点层）。

**层一：独立创意**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| design_id | string | required | `design_science_01` 形式 |
| type | enum | required | science / application / story |
| title | string | required | 方案名（10字内） |
| video_theme | text | required | 视频独立主题（视频讲什么，不必和课堂直接相关） |
| hook | text | required | 视频开场钩子（50字内，描述开场冲突/悬念/奇妙发现） |
| eye_catch_tag | string | required | 新奇特标签（3词内，体现差异化） |

**层二：课堂接入（锚点层）**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| anchor_to_lesson | text | required | **课程锚点**：视频最后通过[具体现象/物品/冲突/疑问]，引出本课核心学习任务（15-40字，必须具体，不得是教学目标描述） |
| classroom_entry_question | text | required | 课堂落点问题：视频播完后老师第一句话（一个具体问题） |
| no_pre_teach | text | required | 不提前讲解的内容（列出视频不能碰的知识点） |
| entry_position | text | required | 接入教案的位置（在哪个教学环节之前播放） |
| recommend_score | int | required | 推荐分 1-100 |
| recommend_reason | text | required | 推荐理由（适配度/吸引力/可制作性/接入自然度） |
| risk_note | text | optional | 适配风险 |

## 节点 1.5：导入设计选择集（intro_selection）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| selection_mode | enum | required | single_best / same_type_multi / one_each_type / all_types_custom / all_nine |
| selected_design_ids | list<string> | required | 引用 intro_design.design_id |
| primary_design_id | string | required | 选择集主方案 |
| selected_anchor | text | required | 用户确认（可编辑）的最终课程锚点；下游 intro_video_script / storyboard / final_video 必须使用此字段，不得自行改写 |
| downstream_generation_mode | enum | required | one_script_per_design / three_variants_for_primary / compare_selected_designs |
| selection_reason | text | required | 选择理由 |

## 节点 2：PPT 总装方案（ppt_assembly_plan）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| persistent_context | text | required | 持续情境（例"操场跑步"） |
| page_count_target | int | required | 计划页数（在 ppt_page_range 内） |
| page_type_quota | map<page_type, int> | required | 11 类页面类型的配比约束 |
| action_chain | list<string> | required | 课堂动作链（从 14 动作词表中选） |
| inquiry_path | text | required | 探究链路 |
| ppt_video_division | text | required | PPT 与视频的分工 |
| material_requirements | list<text> | required | 素材需求清单 |
| editable_text_rules | text | required | 精确文本层规则（公式/数字/单位/答案必须可编辑） |
| accuracy_warnings | list<text> | required | 本课最易被 AI 误写的内容清单 |

### page_type 枚举（11 类）

`life_observation` / `role_task` / `inquiry_operation` / `step_reveal` / `dual_image_compare` / `error_judge` / `practice_challenge` / `evidence_reasoning` / `math_id_card` / `blackboard_summary` / `homework_practice`

### action 枚举（14 类动作词表）

`look` / `touch` / `arrange` / `count` / `divide` / `compare` / `circle` / `link` / `draw` / `speak` / `judge` / `fill` / `correct` / `find`

## 节点 3：PPT 页面脚本（ppt_page_script，细粒度 13 字段，逐页）

每页一条记录。

| # | 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 1 | core_competency | enum | required | 新课标核心素养锚点，11 选 1-2 |
| 2 | page_objective | string | required | 本页教学目标（≤30 字） |
| 3 | student_action | enum | required | 14 动作词表选 1 |
| 4 | page_type | enum | required | 11 类页面类型选 1 |
| 5 | main_visual | object | required | { description, serves_purpose } 主视觉对象 + 服务目的 |
| 6 | character_refs | list<string> | optional | 引用 character_dict.character_id |
| 7 | image_prompts | list<image_prompt> | optional | 待生图清单 |
| 8 | math_assertions | list<math_assertion> | optional | 精确数学内容 |
| 9 | zone_layout | object | required | { task_zone, math_zone, conclusion_zone } 三区描述 |
| 10 | evidence_requirement | text | optional | 证据表达要求 |
| 11 | accuracy_notes | text | optional | 准确性提醒（教师备注层，不给学生看） |
| 12 | link_to_prev_page | text | optional | 与上一页的衔接 |
| 13 | density_limits | object | required | { body_text_max: 25, info_chunks_max: 5 } |

### core_competency 枚举（11 类）

`number_sense` / `quantity_sense` / `symbol_awareness` / `operation_ability` / `geometric_intuition` / `spatial_concept` / `reasoning_awareness` / `data_awareness` / `model_awareness` / `application_awareness` / `innovation_awareness`

### image_prompt 子结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| prompt_id | string | required | 唯一 ID |
| description | text | required | 生图描述 |
| knowledge_link | text | required | 与本页知识点的关联 |
| real_life_scene | bool | required | 是否真实生活场景 |
| character_refs | list<string> | optional | 用到的角色字典 ID |
| aspect_ratio | enum | required | 16:9 / 1:1 / 9:16 |

### math_assertion 子结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| content | string | required | 题面 / 公式 / 数字 / 单位 |
| answer | string | optional | 答案 |
| editable_layer | enum | required | ppt_text / ppt_shape / ppt_chart（不得交给图片/视频） |

## 节点 4B：导入视频文稿（intro_video_script，L1 视频整体，v1 简版）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| total_duration_sec | int | required | 60-120 或 10-15 |
| video_type | enum | required | science / application / story |
| anchor_to_lesson | text | required | 课程锚点 |
| narration_full_text | text | required | 完整旁白文本（中文 TTS 输入） |
| narration_word_count | int | required | 按 280 字/分钟换算检查时长 |
| banned_elements | list<string> | required | 禁用清单：real_minor / real_classroom / teacher_questioning ... |

v1.x 补：节奏分配、核心冲突结构化。

## 节点 4C：导入视频剧本（intro_video_screenplay，L2 剧本分场，v1 简版）

每场一条记录。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| scene_id | string | required | scene_01 / scene_02 |
| duration_sec | int | required | 本场时长 |
| scene_description | text | required | 地点 / 时间 / 氛围 |
| character_refs | list<string> | optional | 引用角色字典 |
| narration_segment | text | required | 本场旁白（切自 narration_full_text） |

v1.x 补：情绪基调、数学元素显隐、上下场衔接。

## 节点 5A：PPT 视觉资产（ppt_visual_asset）

每张图一条记录。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| asset_id | string | required | 唯一 |
| source_prompt_id | string | required | 引用 ppt_page_script.image_prompts.prompt_id |
| storage_path | path | required | 文件路径 |
| status | enum | required | drafted / approved / failed |
| api_job_id | string | optional | 生图作业 ID |
| failed_reason | text | optional | 失败原因 |

## 节点 5B：导入视频资产（intro_video_asset）

结构同 5A，`source_prompt_id` 引用源不同（来自分镜脚本的参考图需求）。资产存储路径必须落在 `08B_导入视频资产/` 下，**禁用 PPT 视觉资产作参考图**（rules.md 强制）。

## 节点 6：分镜脚本（storyboard，L3 逐镜头，v1 中粒度）

每个镜头一条记录。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| shot_id | string | required | shot_01 ... shot_06 |
| duration_sec | int | required | 默认 10（对齐 omni_flash） |
| main_subject | text | required | 画面主体 |
| character_refs | list<string> | optional | 引用角色字典 |
| reference_image_ids | list<string> | required | 引用 intro_video_asset.asset_id |
| narration_slice | text | required | 这一段的旁白（切自 narration_full_text） |
| subtitle | text | optional | 字幕文本（默认空） |
| model_prompt | text | required | 喂给 omni_flash 的最终 prompt（v1 用模板拼接，v1.x 自动拼装器） |
| first_frame_test_status | enum | required | not_tested / passed / failed |
| first_frame_asset_id | string | optional | 首帧测试图 ID |

v1.x 补：景别、运动、多层元素清单、转场。

## 节点 7：PPT 装配（pptx_artifact）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pptx_path | path | required | 最终 PPTX 路径 |
| pdf_preview_path | path | required | PDF 预览路径 |
| contact_sheet_path | path | required | 全页联系表 |
| svg_quality_passed | bool | required | svg_quality_checker.py 结果 |
| eight_confirmations_status | enum | required | pending / confirmed / fast_mode_authorized |
| slide_count | int | required | 幻灯片数 |
| notes_count | int | required | 备注数（应等于 slide_count） |
| media_count | int | required | media 图片数 |

## 节点 8：视频生成 + 拼接（final_video）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| video_path | path | required | 最终视频路径 |
| total_duration_sec | int | required | 实际总时长（必须落在 60-120 或 10-15） |
| clip_count | int | required | 片段数（默认 ≥ 6） |
| clips | list<clip_record> | required | 每段独立记录 |
| audio_streams_count | int | required | 必须 ≥ 1 |
| audio_verified | bool | required | ffprobe 验证 |
| voice_gender | enum | optional | 配音配置，不作为硬阻断 |
| voice_language | enum | required | 建议 zh-CN；缺失或不明确触发 R001 warning |
| narration_audio_path | path | required | 中文 TTS 输出 |
| subtitle_srt_path | path | optional | 字幕 |
| model_audio_policy | enum | required | discarded_or_muted / verified_chinese / no_model_audio |
| english_audio_detected | bool | required | 必须 false |
| concat_manifest_path | path | required | concat_manifest.json 路径 |
| voice_exemption | object | optional | 历史兼容字段；新流程通过 warning override 记录原因 |

### clip_record 子结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| shot_id | string | required | 引用 storyboard.shot_id |
| model | enum | required | omni_flash_10s / sora_2_12s |
| api_task_id | string | required | API 返回 task_id |
| download_path | path | required | 片段文件路径 |
| status | enum | required | pending / generated / approved / failed |
| reference_image_ids | list<string> | required | 必须非空（rules 强约束） |
| failed_reason | text | optional | 失败原因 |

## 节点 9：最终交付（final_delivery）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| lesson_plan_path | path | required | 交付教案 Markdown |
| pptx_final_path | path | required | 交付 PPTX |
| video_final_path | path/null | required | 交付视频；`needs_intro_video=false` 时允许为空 |
| delivery_manifest_path | path | required | 交付 manifest |
| qa_records | list<text> | required | QA / gate 记录摘要 |
| gate_result_json_path | path | required | final_delivery_gate.py 输出 |
| gate_passed | bool | required | 必须 true 才能进交付目录 |
| time_stats_md_path | path | required | 耗时统计 |
| feedback_trigger_at | datetime | required | 弹"课件到手反馈"的时间戳 |
| source_versions | object | required | lesson_plan / pptx_artifact / final_video 源版本 |
| generated_at | datetime | required | 交付包生成时间 |

## 反馈记录（feedback_record）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| feedback_id | string | required | UUID |
| project_id | string | required | 关联项目 |
| timing | enum | required | on_delivery / on_next_session_open |
| satisfaction_score | int | optional | 1-5 |
| class_effect_score | int | optional | 1-5（只在 on_next_session_open 时有效） |
| student_reaction | text | optional | 学生反应描述 |
| free_comment | text | optional | 自由文本 |
| submitted_at | datetime | required | 提交时间 |

## 用户偏好画像（user_preference_profile）

每个用户一条记录，飞轮自动更新。

| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | string | 关联用户 |
| style_preference | map<enum, float> | 风格分布（生活情境/数学情境/历史科普） |
| verbosity_preference | map<enum, float> | 详略分布 |
| inquiry_intensity_preference | map<enum, float> | 探究强度分布 |
| model_usage | map<provider, int> | 各 provider 使用次数 |
| topic_domain_preference | map<string, float> | 课题领域（几何/运算/应用题…） |
| approved_samples_top_n | list<sample_ref> | 最近 N 个 approved 节点产物片段（飞轮检索源） |
| post_approve_edits_top_n | list<diff> | approve 后又被改的 diff（精修信号） |
| overridden_rules | map<rule_id, int> | 被 override 的规则次数 |

## 种子参数（seed_params）

每次 AI 重做时附带。

| 字段 | 类型 | 取值 |
|---|---|---|
| language_style | enum | academic / research / classroom |
| verbosity | enum | concise / moderate / detailed |
| example_tendency | enum | life / math / history |
| inquiry_intensity | enum | conservative / balanced | aggressive |
| free_text_hint | string | 用户自由文本框 |

## 节点版本通用字段（node_version，所有节点共享）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| version_id | string | required | `v01` / `v02` ... |
| node_id | string | required | 节点 ID |
| project_id | string | required | 关联项目 |
| content | json | required | 节点字段化产物（按上面对应节点 schema） |
| status | enum | required | drafted / needs_review / approved / blocked / skipped（state_machine.md 定义） |
| generated_by | enum | required | ai / human_edit |
| provider | string | optional | LLM provider（ai 模式才有） |
| seed_params | object | optional | 重做用的种子参数 |
| created_at | datetime | required | 生成时间 |
| approved_at | datetime | optional | approve 时间 |
| is_current | bool | required | 是否当前 current 版本 |

## 不在 v1 schema 里的（明确推迟）

- 跨项目复用资产（v2+）
- 多人协作字段（owner / approver / lock）（外销时）
- 教程系统字段（v1.x）
- 紧急模式自动压缩规则（仅留 `deadline_at` 字段，规则 v1.x 补）
- 视频深度字段（景别 / 运动 / 多层元素 / 转场 / prompt 自动拼装器）（v1.x）
- AI 味检测分数字段（飞轮数据够之后）
