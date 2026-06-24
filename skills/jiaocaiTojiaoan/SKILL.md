---
name: jiaocaiTojiaoan
description: Use when converting a PDF textbook or scanned/PDF教材 page range into a structured Chinese lesson-plan draft for AI-youjiao, especially when the task needs MinerU, page定位, PDF裁剪, 图文核验, 教材物体清单, or 教材到教案整理.
---

# jiaocaiTojiaoan

## Overview

Use this project-local skill to turn a **PDF 教材** page range into a structured lesson-plan draft. The core pattern is:

1. Locate the target textbook pages inside the PDF.
2. Crop only the relevant PDF page range.
3. Run MinerU on the cropped PDF.
4. Visually verify page images.
5. Combine extracted text with image semantics into a reusable教案 draft.

This skill is for PDF-based textbook analysis. If the input is already a clean lesson-plan text document, use the downstream lesson/video skills instead.

## Inputs

Collect or infer:

- Original PDF path.
- Target topic, unit, or keywords.
- Textbook name, grade, edition, and page range if known.
- Desired output directory.
- Whether the result is for lesson planning, video planning, or both.

If no output directory is given, use the user's Codex workspace convention and create a task folder with `work\` and `outputs\`.

## Local MinerU Environment

Known local MinerU path from the validated workflow:

```powershell
$MinerURoot = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525"
$MinerUExe = "$MinerURoot\.venv-mineru\Scripts\mineru.exe"
```

Known working command pattern:

```powershell
& $MinerUExe -p $pdf -o $out -b pipeline -m txt -l ch -f true -t true
```

Use `pipeline` and `txt` first when the PDF has a text layer. Switch strategy only after diagnosing the actual failure.

## Workflow

### 1. Verify the PDF

Check that the PDF exists, record size, page count, and modification time.

```powershell
Get-Item -LiteralPath "原始PDF路径" | Format-List FullName,Length,LastWriteTime
```

Use a PDF library such as PyMuPDF or pypdf to count pages and inspect whether a text layer exists.

### 2. Locate the Target Pages

Do not run MinerU on the full textbook first. Search the PDF text layer with topic and exercise keywords.

For math textbooks, useful keywords include:

- 课题名 or unit name
- `做一做`
- `试一试`
- `练一练`
- `思考题`
- nearby knowledge points such as `比大小`、`第几`、`分与合`

Always record both:

- PDF page numbers
- textbook printed page numbers

These often differ.

### 3. Render Page Images

Render the target pages to images before writing the final教案. Use them to check objects, scenes, quantities, actions, and exercise layouts that OCR may not name.

Recommended outputs:

```text
work\<task_slug>\page_19.png
work\<task_slug>\page_20.png
work\<task_slug>_contact.jpg
```

Do not rely only on OCR text. In picture-rich教材, the teaching meaning often lives in images, object counts, gestures, and page layout.

### 4. Crop to a Small PDF

Crop only the relevant page range.

Recommended:

- Keep a descriptive Chinese filename for humans.
- Also create a short English filename for MinerU commands.

Example:

```text
work\lesson_5以内数_教材页14-23.pdf
work\lesson_5.pdf
```

Short English paths reduce command-line and model-service uncertainty.

### 5. Run MinerU

Run MinerU on the cropped PDF, not the full textbook.

```powershell
$MinerUExe = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525\.venv-mineru\Scripts\mineru.exe"
$pdf = "C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\lesson_5.pdf"
$out = "C:\Users\HB\Documents\Codex\2026-06-16\mine-u\work\mineru_lesson5"

& $MinerUExe -p $pdf -o $out -b pipeline -m txt -l ch -f true -t true
```

Expected useful outputs:

```text
lesson_x.md
lesson_x_content_list.json
lesson_x_content_list_v2.json
lesson_x_middle.json
lesson_x_model.json
lesson_x_layout.pdf
lesson_x_span.pdf
images\
```

### 6. Handle MinerU Hangs

If MinerU appears stuck or times out:

1. Check whether MinerU, FastAPI, or Python child processes are still running.
2. Run a minimal repro: English path + single-page PDF + `pipeline` + `txt`.
3. Watch for model download, Hugging Face SSL, or timeout retries.
4. After the model cache is ready, rerun the target page-range PDF.

Do not conclude that the PDF is broken just because the first run times out. In the validated case, the root cause was first-run model initialization and network/model-cache delay.

### 7. Build the Structured 教案

Use MinerU text and rendered page images together. The final Markdown should include:

```markdown
# 《课题名》图文教材结构化整理

来源：教材名称、单元、教材页码、PDF 页码。
处理方式：本地 MinerU 解析 + 页面渲染图人工核验。

## 一、课节范围判断

## 二、核心知识点

## 三、图片、物体、道具清单

## 四、逐页结构化内容

## 五、可转成教案的课堂流程

## 六、可直接形成的教学目标

## 七、建议板书

## 八、输出与核验说明
```

For each page, capture:

- page goal
- visible objects and quantities
- exercise structure
- teacher-facing classroom language
- uncertainty or teacher-confirmation points

## Output Rules

Write final deliverables under:

```text
outputs\
```

Recommended files:

```text
outputs\<课题名>_结构化文字教案.md
outputs\MinerU图文教材解析经验文档.md
```

For AI-youjiao long-term reuse, also write or update a project documentation copy under:

```text
docs\jiaocaiTojiaoan\
```

## Handoff

After this skill creates the structured lesson draft:

1. Use `lesson-video-director` if the user wants a video concept.
2. Use `storyboard-keyframe-planner` if a video theme needs timed shots and keyframes.
3. Use `keyframe-image-production` only after storyboard/keyframe assets are explicit.
4. Use `videogen` only after approved prompts/keyframes exist.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Running MinerU on the full textbook first | Locate and crop the target pages first |
| Treating PDF page numbers as textbook page numbers | Record both page systems |
| Trusting OCR for image meaning | Render pages and visually verify objects/actions |
| Using long Chinese paths for every command | Keep a short English PDF copy for MinerU |
| Calling first-run timeout a PDF failure | Test single-page English-path repro and allow model cache initialization |
| Letting video models generate exact text/math later | Mark exact board text, digits, formulas, and captions for deterministic overlay |

## Validated Case

The workflow was validated on a 人教版小学数学一年级上册 PDF, extracting教材页 14-23 / PDF页 19-28 for `5以内数的认识`. It produced:

- `5以内数的认识_结构化文字教案.md`
- `MinerU图文教材解析经验文档.md`

The result included page-range判断, 1-5认识、比大小、第几、分与合, 图片/物体/道具清单, 逐页结构化内容, 教学目标, and board-writing suggestions.
