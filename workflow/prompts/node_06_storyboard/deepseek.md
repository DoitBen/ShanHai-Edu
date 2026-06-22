# Node 06 分镜脚本 — DeepSeek prompt
version: 1.0
provider: deepseek
node_id: storyboard

---

{{include shared/system_role.md}}

## 你的任务

把已 approved 的导入视频剧本（按场分段）进一步切分为 ≥6 个分镜，每个分镜对应一个独立视频片段。
输出符合 schemas/storyboard.schema.json 的 JSON。

## 输入

```json
{
  "intro_video_script": {{intro_video_script}},
  "intro_video_screenplay": {{intro_video_screenplay}},
  "intro_video_asset": {{intro_video_asset}},
  "character_dict": {{character_dict}},
  "visual_contract": {{visual_contract}}
}
```

## 分镜数量约束

- 完整短片（60-120s）：默认 ≥ 6 个分镜，每个 10s 对齐 omni_flash-10s
- 短导入片（10-15s）：可 1-2 个分镜

## 每个 shot 字段说明

| 字段 | 注意 |
|---|---|
| `shot_id` | 格式 `shot_01`、`shot_02` |
| `duration_sec` | 默认 10（对齐 omni_flash）；备选 12（sora-2）、15（旧版兼容） |
| `main_subject` | 画面主体一句话描述 |
| `character_refs` | 引用 character_dict 中存在的角色 ID（R032） |
| `reference_image_ids` | **必须非空**（R013），引用 intro_video_asset 中已 approved 的资产 ID |
| `narration_slice` | 这一段的旁白文本。**所有 shot 的 narration_slice 拼接后必须等于 intro_video_script.narration_full_text**（R041） |
| `subtitle` | 字幕文本，可空 |
| `model_prompt` | **喂给 omni_flash 的最终 prompt**（见下） |
| `first_frame_test_status` | 初始为 "not_tested" |

## model_prompt 必须的结构

**R043 强约束**：每条 model_prompt 必须包含：

```
中文旁白：[narration_slice 内容]
画面：[镜头主体描述]
风格：[visual_contract.style_keywords]
角色：[引用 character_dict 中的多视角描述]
禁止英文配音；如平台自动生成英文音频，则该片段判为不合格，需要静音或重合成中文配音。
```

模板示例：

```
中文旁白：小明站在操场上，看着同学们绕着操场跑步。
画面：俯视视角，卡通扁平风格，操场是绿色椭圆形跑道，小明在中心位置仰头观察。
风格：扁平、明亮、低饱和度。
角色：小明 - 二年级男生，正面：圆脸短发，蓝色T恤白短裤，运动鞋。
禁止英文配音；如平台自动生成英文音频，则该片段判为不合格，需要静音或重合成中文配音。
```

## 红线

- 引用的 reference_image_ids 必须落在 `08B_导入视频资产/` 目录（R012）
- 不得引用 PPT 资产 / contact sheet / 候选视频抽帧
- model_prompt 不含中文旁白和禁英文配音句即被 R043 拒
- narration_slice 拼接缺漏会被 R041 拒

{{include shared/output_format_json.md}}
