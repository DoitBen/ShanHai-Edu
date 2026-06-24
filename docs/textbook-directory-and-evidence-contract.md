# 教材目录解析与教材证据包契约

## 1. 背景

当前教材库已具备 fixture 教材入库、知识点资产包、PDF/Markdown 预览和教案来源追溯能力，但仍存在三类缺口：

1. 人教版一年级上册知识点仍主要来自固定课时数组，不是目录页驱动。
2. PDF 页段裁剪失败时存在退回复制整册 PDF 的风险。
3. 非高质量 fixture 的 MinerU Markdown 仍偏占位说明，不能作为可信教材内容。

本契约定义下一轮 T127-T132 的共同数据和验收口径。

## 2. 教材结构分层

本轮固定支持：人教版小学数学一年级上册。

教材结构分两层：

### 2.1 目录章节

目录章节来自教材目录页，必须严格对照目录中的章节名称和起始页码。

至少包含：

| 目录项 | 起始教材页 |
|---|---:|
| 数学游戏 | 1 |
| 5以内数的认识和加、减法 | 12 |
| 6~10的认识和加、减法 | 34 |
| 认识立体图形 | 67 |
| 11~20的认识 | 73 |
| 20以内的进位加法 | 88 |
| 复习与关联 | 103 |

章节范围规则：

```text
当前章节起始教材页 <= 内容页 <= 下一章节起始教材页 - 1
```

最后一个章节的结束页可以由教材页码最大值或人工配置决定。

### 2.2 课时知识点

课时知识点挂在目录章节下。

课时知识点可以来自：

1. 已验证模板。
2. MinerU 解析结果。
3. 人工确认。

目录章节不是课时知识点的替代品。前端可展示目录项，也可展示目录项下的课时知识点，但必须保留二级关系。

## 3. 页码映射

必须同时记录两套页码：

- 教材页码：教材正文印刷页码。
- PDF 页码：PDF 文件实际页序号。

任何资产包都必须包含：

```json
{
  "textbook_pages": "14-23",
  "pdf_pages": "19-28"
}
```

禁止只记录 PDF 页码或只记录教材页码。

## 4. 教材库列表契约

教材库下拉框需要的数据形态：

```json
{
  "textbooks": [
    {
      "textbook_id": "renjiao-grade1-volume1-2024",
      "textbook_version_id": "renjiao-grade1-volume1-2024-v1",
      "publisher": "人教版",
      "subject_label": "小学数学",
      "grade_label": "一年级",
      "volume_label": "上册",
      "display_name": "人教版 / 小学数学 / 一年级 / 上册",
      "status": "indexed"
    }
  ]
}
```

内部字段可以继续保留 `subject=math`、`grade=1`、`textbook_version=renjiao`、`volume=shang`，但前端普通用户展示必须使用中文 label。

## 5. 目录与知识点契约

查询教材知识点时，必须返回目录章节和课时知识点：

```json
{
  "textbook_id": "renjiao-grade1-volume1-2024",
  "textbook_version_id": "renjiao-grade1-volume1-2024-v1",
  "chapters": [
    {
      "chapter_id": "ch_001",
      "title": "数学游戏",
      "page_start": 1,
      "page_end": 11,
      "pdf_page_start": 6,
      "pdf_page_end": 16,
      "source": "toc",
      "review_status": "needs_review"
    }
  ],
  "knowledge_points": [
    {
      "id": "kp_001",
      "chapter_id": "ch_002",
      "title": "5以内数的认识",
      "unit": "5以内数的认识和加、减法",
      "page_start": 14,
      "page_end": 23,
      "pdf_page_start": 19,
      "pdf_page_end": 28,
      "keywords": ["1-5", "比大小", "第几", "分与合"],
      "parse_status": "parsed",
      "review_status": "needs_review"
    }
  ]
}
```

如果目录识别失败：

```json
{
  "status": "needs_review",
  "message": "未能稳定识别教材目录，请人工确认目录页和页码映射。"
}
```

禁止静默套用错误目录。

## 6. 知识点资产包契约

每个知识点必须有资产包：

```json
{
  "asset_id": "asset_xxx",
  "textbook_id": "renjiao-grade1-volume1-2024",
  "textbook_version_id": "renjiao-grade1-volume1-2024-v1",
  "knowledge_point_id": "kp_001",
  "source_pdf_path": "textbook-library/uploads/source.pdf",
  "slice_pdf_path": "textbook-library/assets/.../source.pdf",
  "preview_images": [
    {
      "page": 19,
      "image_path": "textbook-library/assets/.../page_019.png"
    }
  ],
  "mineru_md_path": "textbook-library/assets/.../mineru.md",
  "textbook_pages": "14-23",
  "pdf_pages": "19-28",
  "parse_status": "parsed",
  "review_status": "needs_review",
  "checksum": "sha256:..."
}
```

### 6.1 裁剪失败规则

PDF 裁剪失败时：

- 不得复制整本 PDF 作为页段 PDF。
- `parse_status` 必须为 `failed` 或 `needs_review`。
- 必须返回可读失败原因。

### 6.2 预览规则

前端可以使用两类预览：

1. `slice_pdf_path` 内嵌 PDF 阅读器。
2. `preview_images` 按页图片预览。

至少一种必须可用。

## 7. MinerU Markdown 结构

MinerU Markdown 必须是教材内容，不是教案。

最低结构：

```markdown
# 《课题名》图文教材结构化整理

来源：教材名称、单元、教材页码、PDF 页码。
处理方式：页段 PDF 裁剪 + MinerU 解析 + 页面图核验。

## 一、课节范围判断

## 二、核心知识点

## 三、图片、物体、道具清单

## 四、逐页结构化内容

## 五、可转成教案的课堂流程

## 六、可直接形成的教学目标

## 七、建议板书

## 八、输出与核验说明
```

允许存在“待人工确认”的说明，但不能只有占位说明。

## 8. 重新解析规则

“重新解析”只针对当前选定知识点：

- 重跑当前知识点页段裁剪。
- 重跑当前知识点 MinerU 解析。
- 更新当前资产包状态。

不重新解析整册教材，除非用户明确选择“重新解析整本教材目录”。

## 9. 教案生成来源规则

教案生成主输入必须是当前知识点的 MinerU Markdown。

历史教案只能作为参考，不能替代当前教材内容。

生成结果必须记录：

- `source_textbook_id`
- `source_textbook_version_id`
- `source_knowledge_point_id`
- `source_slice_pdf_path`
- `source_mineru_md_path`
- `reference_lesson_plan_id`（如果有）

## 10. 验收红线

以下任一出现即不通过：

1. 知识点来自前端 mock。
2. 目录项与教材目录页不一致且无人工确认标识。
3. 页段 PDF 实际是整册 PDF。
4. Markdown 只有“待精抽”占位，没有教材结构化内容。
5. 教案生成没有追溯当前教材资产包。
6. 当前知识点未确认却标记为 approved。
