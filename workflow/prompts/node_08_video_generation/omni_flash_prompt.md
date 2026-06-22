# Node 08 视频生成 — omni_flash-10s prompt 模板
version: 1.0
provider: omni_flash_10s
node_id: final_video

---

## 用途

把 storyboard 的每个 shot 转换为 omni_flash-10s API 的真实调用 payload。

**这不是 LLM 调用的 prompt**，是给视频生成 API 的提示词模板。
本文件是 storyboard.shots[*].model_prompt 字段的样板，调度器按此拼装。

## 字段映射

```python
omni_flash_payload = {
    "model": "omni_flash_10s",
    "prompt": shot.model_prompt,
    "reference_images": [
        asset.storage_path
        for asset in intro_video_assets
        if asset.asset_id in shot.reference_image_ids
    ],
    "duration": shot.duration_sec,
    "aspect_ratio": "16:9",
    "audio": {
        "enabled": False,    # 我们不用模型生成的音频
        "policy": "discarded_or_muted"  # 落到 final_video.model_audio_policy
    }
}
```

## prompt 模板（中文旁白 + 禁英文配音硬约束句）

每条 model_prompt 必须包含以下固定结尾：

```
中文旁白：{{narration_slice}}
画面：{{visual_description}}
风格：{{style_keywords}}
角色：{{character_multi_view_desc}}
禁止英文配音；如平台自动生成英文音频，则该片段判为不合格，需要静音或重合成中文配音。
```

R043 会按这个固定句校验每条 prompt。

## 模型音轨处理策略

omni_flash-10s 可能会输出英文音频或不符合旁白配置的音轨，**默认丢弃**：

1. 视频生成后，提取纯视频流（无音频）
2. 用中文 TTS（待选型）按 narration_slice 重新合成旁白音频
3. ffmpeg 拼接视频 + 新音频
4. 写入 final_video.model_audio_policy = "discarded_or_muted"

## 失败重试策略

| 失败原因 | 策略 |
|---|---|
| API 超时 | 自动重试 2 次（指数退避） |
| 内容审核驳回 | 不重试，提示用户改 prompt（可能触发 banned_elements） |
| 生成质量崩 | 用户手动重试 |
| 配额不足 | 立即提示，不消耗额度 |

## 提交前必跑（R015 + R042）

```bash
python scripts/workflow_contract_gate.py {project_path} --mode submit
python scripts/videogen_batch_jobs.py validate
python scripts/workflow_enforcement_gate.py --stage submit
```

并且所有 shot 的 first_frame_test_status 必须 == "passed"。

## 拼接前必查（R044）

所有 clips 的 status 必须 == "approved" 才能进入 ffmpeg 拼接流程。
