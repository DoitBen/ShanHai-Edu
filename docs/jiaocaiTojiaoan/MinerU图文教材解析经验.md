# MinerU 图文教材解析经验

记录时间：2026-06-16
来源文档：`C:\Users\HB\Documents\Codex\2026-06-16\mine-u\outputs\MinerU图文教材解析经验文档.md`
项目技能：`skills\jiaocaiTojiaoan\SKILL.md`

## 目标

把 **PDF 图文教材** 中的目标页段转换成可用于备课的结构化文字教案。整理时既保留教材原有结构，也补充图片、道具、物体数量、教学活动和可转教案语言。

本经验来自一次已验证案例：从人教版小学数学一年级上册 PDF 中抽取“5以内数的认识”相关内容，整理成结构化文字教案。

## 使用技能和工具

### 技能

- `pdf`：PDF 任务路由，决定复杂图文 PDF 使用 MinerU。
- `systematic-debugging`：MinerU 初次卡住后，用最小复现定位原因。
- `verification-before-completion`：交付前核验产物是否真实存在。

### 工具

- `shell_command`：运行 PowerShell、Python、MinerU、文件检查、进程检查。
- `view_image`：查看渲染后的页面图，人工确认图片内容。
- `apply_patch`：创建最终 Markdown 文档。
- `multi_tool_use.parallel`：并行执行多个只读检查和页面查看。

### 本地核心环境

MinerU 本地路径：

```powershell
$MinerURoot = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525"
$MinerUExe = "$MinerURoot\.venv-mineru\Scripts\mineru.exe"
```

本次核验到的版本：

```text
mineru, version 3.2.0
```

文档辅助 Python 环境：

```powershell
$DocsPy = "$env:USERPROFILE\.agents\envs\docs\Scripts\python.exe"
```

## 处理流程

### 1. 确认 PDF 文件

先检查用户给的 PDF 是否存在、大小和修改时间。

```powershell
Get-Item -LiteralPath "原始PDF路径" | Format-List FullName,Length,LastWriteTime
```

本次案例文件大小约 50 MB，共 118 页。

### 2. 定位目标页，不整本盲跑

用 PyMuPDF 读取文本层，搜索关键词：

- `5以内数的认识`
- `做一做`
- `试一试`
- `练一练`
- `思考题`
- `分与合`
- `第几`
- `比大小`

本次定位结果：

- PDF 页 19-28
- 教材页 14-23
- 内容包含：`1～5的认识`、`比大小`、`第几`、`分与合`、`做一做`、`练一练`、`思考题`

经验判断：

- 教材页码和 PDF 页码通常不一致，必须同时记录。
- 图文教材不要直接整本跑 MinerU，先定位页段更稳、更快。

### 3. 渲染目标页做视觉核验

用 PyMuPDF 把目标页渲染成图片，便于人工检查图片内容。

本次输出目录：

```text
C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\lesson_19_28
```

还生成了一张缩略图总览：

```text
C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\lesson_19_28_contact.jpg
```

经验判断：

- MinerU 能切图和 OCR，但“图片里是什么物体”仍需要人工或视觉模型核验。
- 对教材类任务，必须看页面图，否则会漏掉道具、动物、场景和教学意图。

### 4. 裁剪目标页成小 PDF

用 `pypdf` 裁剪出目标 10 页，避免整本处理。

本次中间文件：

```text
C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\lesson_5以内数_教材页14-23.pdf
C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\lesson_5.pdf
```

其中 `lesson_5.pdf` 是英文路径副本，用于降低命令行和模型服务处理中文路径的不确定性。

经验判断：

- 对 MinerU，建议正式解析文件使用短路径、英文名。
- 页段裁剪后再跑 MinerU，速度和稳定性明显更好。

### 5. 运行 MinerU

正式命令：

```powershell
$MinerUExe = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525\.venv-mineru\Scripts\mineru.exe"
$pdf = "C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\lesson_5.pdf"
$out = "C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\mineru_lesson5"

& $MinerUExe -p $pdf -o $out -b pipeline -m txt -l ch -f true -t true
```

参数说明：

- `-p`：输入 PDF。
- `-o`：输出目录。
- `-b pipeline`：使用稳定的 pipeline 后端。
- `-m txt`：该教材有文本层，优先文本抽取并结合版面分析。
- `-l ch`：中文。
- `-f true`：保留公式解析开关。
- `-t true`：保留表格解析开关。

本次成功输出目录：

```text
C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\mineru_lesson5\lesson_5\txt
```

关键产物：

```text
lesson_5.md
lesson_5_content_list.json
lesson_5_content_list_v2.json
lesson_5_middle.json
lesson_5_model.json
lesson_5_layout.pdf
lesson_5_span.pdf
images\
```

## 卡住根因和处理办法

### 现象

- 直接跑原始长路径 PDF 的页段，2 分钟超时，无输出。
- 裁剪成 10 页 PDF 后，5 分钟仍超时，无输出。

### 排查

1. 检查进程，发现 MinerU 临时 FastAPI 服务和 Python 子进程仍在运行。
2. 做最小复现：英文路径、单页 PDF、pipeline、txt 模式。
3. 最小复现成功，但日志显示它在下载或补齐模型文件。

### 根因判断

- 不是教材 PDF 无法解析。
- 不是 MinerU 完全损坏。
- 主要原因是首次运行时模型初始化和 Hugging Face 模型文件下载耗时，且网络出现 SSL/timeout 重试。

### 处理方法

1. 停止卡住的 MinerU 相关进程。
2. 先跑英文路径单页最小 PDF，让模型完成初始化和缓存。
3. 再跑 10 页目标 PDF，最终约 69.6 秒完成。

经验：

- MinerU 首次跑某些模型时可能需要联网补模型，不能把第一次超时直接判断为 PDF 错误。
- 遇到卡住时，先最小化：英文路径 + 单页 PDF + 明确后端。
- 模型缓存完成后，再跑目标页段会明显变快。

## 最终整理模板

后续同类教材可复用以下结构：

```markdown
# 《课题名》图文教材结构化整理

来源：教材名称、单元、教材页码、PDF 页码。
处理方式：本地 MinerU 解析 + 页面渲染图人工核验。

## 一、课节范围判断

- 本段教材实际包含哪些内容。
- 是否需要拆成多个教学环节。

## 二、核心知识点

### 1. 知识点一

- 学生要理解什么。
- 学生要会做什么。

## 三、图片、物体、道具清单

### 生活实物

- ...

### 练习中的物体

- ...

### 教学可准备道具

- ...

## 四、逐页结构化内容

### 教材页 X：标题

页面目标：

- ...

图文内容：

- ...

题目结构：

1. ...
2. ...

可转教案语言：

- ...

## 五、可转成教案的课堂流程

## 六、可直接形成的教学目标

## 七、建议板书

```text
板书内容
```

## 八、输出与核验说明

- MinerU 输出是否存在。
- 人工核验了哪些页面。
- 有哪些不确定或需要教师二次确认的地方。
```

## 本次案例成果

本次结构化结果包含：

- 课节范围判断：教材页 14-23，PDF 页 19-28。
- 核心知识点：1-5 的认识、数字书写、比大小、第几、分与合。
- 图片和物体：房子、狗、鹅、椅子、飞鸟、萝卜、向日葵、南瓜、小鸭、玉米、猴子、水果、松鼠、松果、火车站排队、小鸟、家庭成员、雪人、动物草原图、拔河、桃子等。
- 教学道具：数字卡、点子卡、算珠、小方块、小棒、花片、棋子、比较符号卡。
- 练习结构：做一做、试一试、练一练、思考题。
- 可直接改写为教案的课堂流程、教学目标和板书。

## 后续复用顺序

1. 先读 PDF 页数和文本层，定位目标页段。
2. 裁剪目标页为小 PDF。
3. 复制成短英文文件名。
4. 渲染目标页图片，人工确认图文结构。
5. 运行 MinerU pipeline。
6. 读取 `lesson_x.md` 和 `content_list.json`。
7. 用页面图补齐图片语义。
8. 按模板输出结构化文字教案。

不要只依赖 OCR 文本，因为教材中的核心信息经常藏在图片、人物动作、物体数量和版面关系里。
