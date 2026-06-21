# rules.md — 规则登记表

版本：v1
角色：所有机器可验规则的统一登记。审查智能体和门禁脚本按此清单执行。

## 规则结构

每条规则用统一字段记录：

| 字段 | 说明 |
|---|---|
| `rule_id` | 唯一 ID，例 `R001` |
| `trigger_node` | 触发节点（节点 ID） |
| `trigger_event` | 触发时机：`on_generate` / `on_save` / `on_approve_attempt` |
| `check` | 检查内容（机器可执行的描述） |
| `severity` | `hard_block` / `warning` / `info` |
| `action` | 命中后的处置 |
| `executor` | 执行器：`builtin` / `script:xxx.py` / `agent:claude` |
| `legacy_source` | 来自原规范的哪一处（追溯用，可空） |

`severity` 含义见 `state_machine.md`：
- `hard_block` 命中 → 节点 `blocked`，禁止 approve，无 override
- `warning` 命中 → UI 提示，允许 override，override 记入飞轮
- `info` 命中 → 仅提示，不阻拦

---

## 红线规则（hard_block，6 条，对应产品红线）

### R001 中文男声硬约束

| 字段 | 值 |
|---|---|
| rule_id | R001 |
| trigger_node | final_video |
| trigger_event | on_approve_attempt |
| check | `final_video.voice_gender == "male" AND final_video.voice_language == "zh-CN"`，除非 `voice_exemption.approved == true` |
| severity | hard_block |
| action | 阻断 approve，提示"必须中文男声或结构化人工豁免" |
| executor | builtin |
| legacy_source | 01_执行入口.md「事故防复发规则」 |

### R002 禁英文配音

| 字段 | 值 |
|---|---|
| rule_id | R002 |
| trigger_node | final_video |
| trigger_event | on_approve_attempt |
| check | `final_video.english_audio_detected == false` 且 `final_video.model_audio_policy` ∈ {discarded_or_muted, verified_chinese, no_model_audio} |
| severity | hard_block |
| action | 阻断 approve，提示"检测到英文音频或未记录模型音轨处理策略" |
| executor | builtin |
| legacy_source | 04_审查规则/README.md「阶段8」 |

### R003 单段不得冒充完整视频

| 字段 | 值 |
|---|---|
| rule_id | R003 |
| trigger_node | final_video |
| trigger_event | on_approve_attempt |
| check | 若 `intro_video_type == "full_60_120s"`：要求 `clip_count >= 6 AND total_duration_sec ∈ [60, 120]`；若 `short_10_15s`：允许单段但 `total_duration_sec ∈ [10, 15]` |
| severity | hard_block |
| action | 阻断 approve，提示"单段 omni_flash-10s 只能作为短导入片或素材，不能作为完整教学视频" |
| executor | script:final_delivery_gate.py |
| legacy_source | 01_执行入口.md「事故防复发规则」 |

### R004 角色字典禁真人

| 字段 | 值 |
|---|---|
| rule_id | R004 |
| trigger_node | character_dict |
| trigger_event | on_save |
| check | `character.style_constraint ∈ {cartoon, silhouette, 3d_non_realistic}` 且 `banned_keywords` 包含 ["真人", "photorealistic", "real child"] 三项 |
| severity | hard_block |
| action | 阻断保存，强制补全 banned_keywords 默认项 |
| executor | builtin |
| legacy_source | 第九步分镜小云雀提示词、合规要求 |

### R005 候选不得伪装终版

| 字段 | 值 |
|---|---|
| rule_id | R005 |
| trigger_node | final_delivery |
| trigger_event | on_approve_attempt |
| check | `final_delivery.gate_result_json_path` 中 `mode == "final"` 且 `gate_passed == true` |
| severity | hard_block |
| action | 阻断 approve，提示"必须 final_delivery_gate.py --mode final 通过" |
| executor | script:final_delivery_gate.py |
| legacy_source | 01_执行入口.md「正式交付硬边界」 |

### R006 数学事实必须可编辑

| 字段 | 值 |
|---|---|
| rule_id | R006 |
| trigger_node | ppt_page_script |
| trigger_event | on_approve_attempt |
| check | 每页所有 `math_assertions[].editable_layer` ∈ {ppt_text, ppt_shape, ppt_chart}，禁止 ppt_image / video |
| severity | hard_block |
| action | 阻断 approve，提示"数学公式/数字/单位/答案不得交给图片/视频模型生成" |
| executor | builtin |
| legacy_source | PPT探究型页面约束_工作流节点.md「准确性门禁」 |

---

## 状态/契约规则（hard_block，6 条）

### R010 上游必须 approved 才能进入下游

| 字段 | 值 |
|---|---|
| rule_id | R010 |
| trigger_node | 所有 |
| trigger_event | on_generate |
| check | 上游依赖节点状态必须是 approved 或 skipped |
| severity | hard_block |
| action | 阻断生成 |
| executor | builtin |
| legacy_source | 01_执行入口.md「关键停顿点」 |

### R011 PPT 分支资产只能进 08A

| 字段 | 值 |
|---|---|
| rule_id | R011 |
| trigger_node | ppt_visual_asset |
| trigger_event | on_save |
| check | `storage_path` 必须落在 `08A_PPT视觉资产/` 下 |
| severity | hard_block |
| action | 阻断保存 |
| executor | builtin |
| legacy_source | 公开课自动化9步完整流程-Promax版.md「资产目录必须分支隔离」 |

### R012 视频分支资产只能进 08B 且禁用 PPT 资产作参考

| 字段 | 值 |
|---|---|
| rule_id | R012 |
| trigger_node | intro_video_asset / storyboard |
| trigger_event | on_save |
| check | 视频资产 `storage_path` 必须落在 `08B_导入视频资产/` 下；`reference_image_ids` 不得引用 ppt_visual_asset / PPT contact sheet / 本地候选视频抽帧 |
| severity | hard_block |
| action | 阻断保存 |
| executor | builtin |
| legacy_source | 公开课自动化9步完整流程-Promax版.md「资产目录必须分支隔离」 |

### R013 真实视频片段必须带参考图

| 字段 | 值 |
|---|---|
| rule_id | R013 |
| trigger_node | final_video |
| trigger_event | on_approve_attempt |
| check | `clips[].reference_image_ids` 非空 |
| severity | hard_block |
| action | 阻断 approve |
| executor | builtin |
| legacy_source | 01_执行入口.md「阶段8真实提交前」 |

### R014 视频拼接清单字段完整性

| 字段 | 值 |
|---|---|
| rule_id | R014 |
| trigger_node | final_video |
| trigger_event | on_approve_attempt |
| check | concat_manifest.json 必须包含：`status=final`、`clips`、`task_id`、`download_path`、`reference_images`、`final_video_seconds`/`total_duration_seconds`、`audio_streams>=1`、`audio_verified=true`、`voice_gender=male`、`voice_language=zh-CN` |
| severity | hard_block |
| action | 阻断 approve |
| executor | script:audit_delivery_contracts.py |
| legacy_source | 01_执行入口.md「事故防复发规则」 |

### R015 真实提交前合同门禁

| 字段 | 值 |
|---|---|
| rule_id | R015 |
| trigger_node | storyboard |
| trigger_event | on_submit_to_api |
| check | 必须先通过 `workflow_contract_gate.py --mode submit`、`videogen_batch_jobs.py validate`、`workflow_enforcement_gate.py --stage submit` |
| severity | hard_block |
| action | 阻断 API 提交 |
| executor | script:workflow_enforcement_gate.py |
| legacy_source | 02_规范索引/00_原始规范索引.md |

---

## PPT 探究型规则（warning，13 条覆盖逐页字段）

### R020 每页必须有学生课堂动作

| 字段 | 值 |
|---|---|
| rule_id | R020 |
| trigger_node | ppt_page_script |
| trigger_event | on_generate |
| check | 每页 `student_action` 字段非空（封面/目录/纯视频页可例外但需写明） |
| severity | warning |
| action | UI 红字提示 |
| executor | agent:claude |
| legacy_source | PPT探究型页面约束_工作流节点.md |

### R021 主视觉必须服务教学动作

| 字段 | 值 |
|---|---|
| rule_id | R021 |
| trigger_node | ppt_page_script |
| trigger_event | on_generate |
| check | `main_visual.serves_purpose` 不得为空或"装饰" |
| severity | warning |
| action | UI 红字 |
| executor | agent:claude |
| legacy_source | 同上 |

### R022 判断/练习页需有证据表达

| 字段 | 值 |
|---|---|
| rule_id | R022 |
| trigger_node | ppt_page_script |
| trigger_event | on_generate |
| check | 若 `page_type ∈ {error_judge, practice_challenge, evidence_reasoning}`，要求 `evidence_requirement` 非空 |
| severity | warning |
| action | UI 红字 |
| executor | builtin |
| legacy_source | 同上 |

### R023 必须包含板书小结页

| 字段 | 值 |
|---|---|
| rule_id | R023 |
| trigger_node | ppt_assembly_plan |
| trigger_event | on_approve_attempt |
| check | `page_type_quota.blackboard_summary >= 1` |
| severity | warning |
| action | UI 红字 |
| executor | builtin |
| legacy_source | 同上 |

### R024 页面类型多样性

| 字段 | 值 |
|---|---|
| rule_id | R024 |
| trigger_node | ppt_assembly_plan |
| trigger_event | on_approve_attempt |
| check | `page_type_quota` 至少覆盖 5 类页面类型 |
| severity | warning |
| action | UI 红字 |
| executor | builtin |
| legacy_source | 同上 |

### R025 信息密度限制

| 字段 | 值 |
|---|---|
| rule_id | R025 |
| trigger_node | ppt_page_script |
| trigger_event | on_generate |
| check | 每页正文字数 ≤25 字 / 信息块 ≤5（基于认知负荷理论） |
| severity | warning |
| action | UI 红字 |
| executor | builtin |

### R026 学生可见层不得暴露内部信息

| 字段 | 值 |
|---|---|
| rule_id | R026 |
| trigger_node | pptx_artifact |
| trigger_event | on_approve_attempt |
| check | 最终 PPTX 学生层不得出现：准确性提醒、QA 检查点、工作流阶段名、工具名、脚本名、API 字段、jobs/task_id/file_id |
| severity | hard_block |
| action | 阻断 approve |
| executor | script:audit_student_visible_text.py |
| legacy_source | PPT探究型页面约束_工作流节点.md「学生可见层检查」 |

### R027 ppt-master Eight Confirmations

| 字段 | 值 |
|---|---|
| rule_id | R027 |
| trigger_node | pptx_artifact |
| trigger_event | on_generate |
| check | `eight_confirmations_status` ∈ {confirmed, fast_mode_authorized} |
| severity | hard_block |
| action | 阻断进入 SVG 生成 |
| executor | builtin |
| legacy_source | 第十步：ppt-master公开课PPT生成_自动化执行规则.md |

### R028 SVG 质检通过

| 字段 | 值 |
|---|---|
| rule_id | R028 |
| trigger_node | pptx_artifact |
| trigger_event | on_approve_attempt |
| check | `svg_quality_passed == true` |
| severity | hard_block |
| action | 阻断 approve |
| executor | script:svg_quality_checker.py |
| legacy_source | 同上 |

### R029 PPTX 幻灯片数与备注数一致

| 字段 | 值 |
|---|---|
| rule_id | R029 |
| trigger_node | pptx_artifact |
| trigger_event | on_approve_attempt |
| check | `slide_count == notes_count` |
| severity | warning |
| action | UI 红字 |
| executor | builtin |

### R030 PPT 必须有课程视觉资产

| 字段 | 值 |
|---|---|
| rule_id | R030 |
| trigger_node | pptx_artifact |
| trigger_event | on_approve_attempt |
| check | `media_count > 0`（不接受只有文本框、色块、装饰形状的 PPT） |
| severity | hard_block |
| action | 阻断 approve |
| executor | builtin |
| legacy_source | 01_执行入口.md「事故防复发规则」 |

### R031 配色 / 字体一致性

| 字段 | 值 |
|---|---|
| rule_id | R031 |
| trigger_node | pptx_artifact |
| trigger_event | on_approve_attempt |
| check | PPT 使用的配色集合 ⊆ `visual_contract.palette`；字体 ⊆ `visual_contract.font_preference`（若指定） |
| severity | warning |
| action | UI 红字 |
| executor | builtin |

### R032 角色一致性

| 字段 | 值 |
|---|---|
| rule_id | R032 |
| trigger_node | ppt_page_script / storyboard |
| trigger_event | on_generate |
| check | `character_refs` 中的所有 ID 必须存在于 `character_dict` |
| severity | hard_block |
| action | 阻断生成 |
| executor | builtin |

---

## 视频规则（warning/hard_block，6 条）

### R040 旁白时长一致性

| 字段 | 值 |
|---|---|
| rule_id | R040 |
| trigger_node | intro_video_script |
| trigger_event | on_generate |
| check | `narration_word_count / 280 * 60` 落在 `total_duration_sec ± 10%` 内 |
| severity | warning |
| action | UI 红字提示"旁白字数与视频时长不匹配" |
| executor | builtin |

### R041 分镜旁白切片完整性

| 字段 | 值 |
|---|---|
| rule_id | R041 |
| trigger_node | storyboard |
| trigger_event | on_approve_attempt |
| check | 所有 `storyboard[].narration_slice` 拼接后必须等于 `intro_video_script.narration_full_text` |
| severity | hard_block |
| action | 阻断 approve |
| executor | builtin |

### R042 首帧测试必须通过

| 字段 | 值 |
|---|---|
| rule_id | R042 |
| trigger_node | storyboard |
| trigger_event | on_submit_to_api |
| check | 所有 `storyboard[].first_frame_test_status == passed` |
| severity | hard_block |
| action | 阻断视频 API 提交 |
| executor | builtin |
| legacy_source | （v1 新增机制） |

### R043 视频 prompt 包含中文男声硬约束

| 字段 | 值 |
|---|---|
| rule_id | R043 |
| trigger_node | storyboard |
| trigger_event | on_save |
| check | `model_prompt` 必须包含"旁白（男声，中文）"和"禁止英文配音"字样 |
| severity | hard_block |
| action | 阻断保存 |
| executor | builtin |
| legacy_source | 第九步：修订版-分镜脚本生成提示词-小云雀生视频版.md |

### R044 视频片段必须人工验收

| 字段 | 值 |
|---|---|
| rule_id | R044 |
| trigger_node | final_video |
| trigger_event | on_approve_attempt |
| check | 所有 `clips[].status == approved` |
| severity | hard_block |
| action | 阻断进入拼接 |
| executor | builtin |

### R045 视频禁用元素清单非空

| 字段 | 值 |
|---|---|
| rule_id | R045 |
| trigger_node | intro_video_script |
| trigger_event | on_save |
| check | `banned_elements` 至少包含 ["real_minor", "real_classroom", "teacher_questioning", "student_group_activity"] |
| severity | hard_block |
| action | 阻断保存 |
| executor | builtin |

### R046 每套导入设计必须有具体课程锚点

| 字段 | 值 |
|---|---|
| rule_id | R046 |
| trigger_node | lesson_plan |
| trigger_event | on_generate |
| check | `intro_designs` 中每条记录的 `anchor_to_lesson` 非空且字数 ≥ 10；且不得包含"自然引出本课"、"教学目标对应点"、"教案关联点"等抽象套语 |
| severity | hard_block |
| action | 阻断生成，提示"每套导入设计必须包含具体课程锚点（15-40字，描述具体现象/物品/冲突/疑问）" |
| executor | builtin |
| legacy_source | docs/anchor-lesson-to-video.md R046 |

### R047 用户确认锚点非空

| 字段 | 值 |
|---|---|
| rule_id | R047 |
| trigger_node | intro_selection |
| trigger_event | on_approve_attempt |
| check | `selected_anchor` 非空且字数 ≥ 10 |
| severity | hard_block |
| action | 阻断确认，提示"课程锚点未填写或过短，请在选择页确认锚点后方可进入视频生成" |
| executor | builtin |
| legacy_source | docs/anchor-lesson-to-video.md R047 |

### R048 视频脚本必须接收到课程锚点

| 字段 | 值 |
|---|---|
| rule_id | R048 |
| trigger_node | intro_video_script |
| trigger_event | on_generate |
| check | 生成输入中必须包含来自 `intro_selection.selected_anchor` 的非空字段 |
| severity | hard_block |
| action | 阻断生成，提示"未传入课程锚点，请先在导入设计选择节点确认锚点" |
| executor | builtin |
| legacy_source | docs/anchor-lesson-to-video.md R048 |

### R049 分镜末帧字幕必须体现锚点关键词

| 字段 | 值 |
|---|---|
| rule_id | R049 |
| trigger_node | storyboard |
| trigger_event | on_approve_attempt |
| check | `shots[-1].subtitle` 包含 `selected_anchor` 的核心关键词（至少 1 个） |
| severity | warning |
| action | UI 红字提示"分镜末帧字幕未体现课程锚点关键词，建议检查是否自然衔接本课" |
| executor | agent:claude |
| legacy_source | docs/anchor-lesson-to-video.md R049 |

---

## 图片规则（warning，3 条）

### R050 已验证比例映射

| 字段 | 值 |
|---|---|
| rule_id | R050 |
| trigger_node | ppt_page_script / storyboard |
| trigger_event | on_save |
| check | `image_prompts[].aspect_ratio` 必须在已验证映射表中：16:9 → 1920x1080；1:1 → 1024x1024；9:16 → 1080x1920 |
| severity | hard_block |
| action | 阻断 |
| executor | builtin |
| legacy_source | 00-Promax修改清单.md |

### R051 出图前必须先测 1 张

| 字段 | 值 |
|---|---|
| rule_id | R051 |
| trigger_node | ppt_visual_asset / intro_video_asset |
| trigger_event | on_submit_to_api |
| check | 默认先测 1 张，除非用户明确授权快速模式 |
| severity | warning |
| action | UI 提示 |
| executor | builtin |
| legacy_source | 04_审查规则/README.md「阶段5」 |

### R052 生图 prompt 不得包含可读数学文字

| 字段 | 值 |
|---|---|
| rule_id | R052 |
| trigger_node | ppt_visual_asset / intro_video_asset |
| trigger_event | on_save |
| check | `image_prompts[].description` 不得包含数字、公式、单位、题面、答案（这些应在 `math_assertions` 走 PPT 可编辑层） |
| severity | warning |
| action | UI 红字 |
| executor | agent:claude |

---

## 收尾规则（hard_block，4 条）

### R060 六套一致性审计

| 字段 | 值 |
|---|---|
| rule_id | R060 |
| trigger_node | final_delivery |
| trigger_event | on_approve_attempt |
| check | 候选链路一致 |
| severity | hard_block |
| action | 阻断 approve |
| executor | script:audit_six_package_consistency.py |

### R061 学生可见文本审计

| 字段 | 值 |
|---|---|
| rule_id | R061 |
| trigger_node | final_delivery |
| trigger_event | on_approve_attempt |
| check | 通过 audit_student_visible_text.py |
| severity | hard_block |
| action | 阻断 approve |
| executor | script:audit_student_visible_text.py |

### R062 交付合同审计

| 字段 | 值 |
|---|---|
| rule_id | R062 |
| trigger_node | final_delivery |
| trigger_event | on_approve_attempt |
| check | 通过 audit_delivery_contracts.py（候选不冒充终版、完整教学视频命名不越界、本地预览有非终版标记） |
| severity | hard_block |
| action | 阻断 approve |
| executor | script:audit_delivery_contracts.py |

### R063 耗时统计必须产出

| 字段 | 值 |
|---|---|
| rule_id | R063 |
| trigger_node | final_delivery |
| trigger_event | on_approve_attempt |
| check | `time_stats_md_path` 必须存在，且包含每阶段耗时、返工耗时、主要瓶颈 |
| severity | warning |
| action | UI 红字 |
| executor | builtin |

---

## 规则执行顺序

每次 trigger_event 触发时：

1. 按 `trigger_node + trigger_event` 索引取出所有适用规则
2. 先跑 `hard_block` 规则（短路：任一命中即停）
3. 再跑 `warning` 规则（全跑，汇总展示）
4. 最后跑 `info` 规则

## 规则与状态机的契约

- 任何 `hard_block` 规则在 `on_approve_attempt` 时命中 → 状态不变（仍 needs_review），返回错误
- 任何 `hard_block` 规则在 `on_save` / `on_generate` 时命中 → 节点状态 → `blocked`
- `warning` 命中且用户 override → 记入 `user_preference_profile.overridden_rules`

## 规则编辑权限

- v1：rules.md 由开发 + 教学法负责人共同维护
- v1.x：考虑做后台界面让教学法负责人直接编辑规则文本（不改代码）

## 推迟到 v1.x / v2 的规则

| 推迟项 | 备注 |
|---|---|
| AI 味检测规则 | 飞轮数据够之后再上 |
| 跨项目一致性检查 | 跨项目复用功能上线后 |
| 紧急模式自动跳过非关键规则 | 紧急模式实现后 |
| 多人协作的锁/审批规则 | 外销时 |

## 规则编号预留

- R001-R009：产品红线
- R010-R019：状态/契约
- R020-R039：PPT 探究型
- R040-R059：视频
- R050-R059：图片
- R060-R079：收尾
- R080+：v1.x 扩展
