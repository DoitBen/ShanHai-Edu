# 2026-06-21 真实视频与图片生成 smoke

## 结论

- 视频生成链路：通过。
- 图片生成链路：通过。
- 本报告不包含任何真实密钥，运行日志中 key 仅显示为 `configured` 或 `<redacted>`。

## 视频 smoke

- API：`http://127.0.0.1:8000`
- 项目 ID：`proj_1338cff3c969`
- provider task id：`task_AiOfbv2BjggLRDc9dSxJzL8Dc57anDpw`
- 最终状态：`completed`
- 下载文件：`docs\qa-audits\octo-real-video-smoke\20260621-145411\shot_01.mp4`
- 文件大小：`2570764` bytes
- 结论：`omni_flash-10s` 已完成 `submit -> query -> completed -> download`。

## 图片 smoke

- Provider：`imagegen-myself` primary
- Base URL：`https://img.baofu.eu.cc/v1`
- 模型：`gpt-image-2`
- 下载文件：`docs\qa-audits\imagegen-real-smoke\20260621-145411\imagegen-smoke.png`
- 文件大小：`1283726` bytes
- 文件签名：PNG
- 结论：图片供应商真实生成成功；本轮补齐了供应商返回 URL 时的下载兼容。

## 本轮发现与修复

- `scripts\smoke-octo-real-video.ps1` 旧 fixture 缺 `selected_anchor`，已补齐后通过真实视频 smoke。
- `skills\imagegen-myself\scripts\aircode_image_gen.py` 原先只支持 `b64_json`，供应商返回 URL 时会失败；已补 URL 提取与下载，并新增单元测试。

## 验证命令

```powershell
python .\skills\imagegen-myself\scripts\test_aircode_image_gen_env.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke-octo-real-video.ps1 -ApiBaseUrl http://127.0.0.1:8000 -ProjectName "video-real-omni-20260621-145411" -PollSeconds 10 -MaxPolls 24
python .\skills\imagegen-myself\scripts\aircode_image_gen.py generate-stream --prompt "A clean non-realistic classroom desk with one red apple and number card 1, educational illustration, no text, no real children" --size 1024x1024 --quality high --out .\docs\qa-audits\imagegen-real-smoke\20260621-145411\imagegen-smoke.png --force
```
