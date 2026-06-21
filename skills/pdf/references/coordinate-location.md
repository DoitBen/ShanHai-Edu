# Coordinate-Level PDF Location

Use this workflow when the user asks to find, locate, highlight, cite, or prove where something appears in the original PDF.

## Goal

Return source-grounded hits with page number, section path when available, bounding box, original excerpt, match type, and confidence.

## Workflow

1. Classify the PDF.
   - Text PDF: extract spans directly with PyMuPDF or pdfplumber.
   - Scanned PDF: route through OCR, usually MinerU OCR on this machine.
   - Mixed or complex paper: use MinerU for structure and PyMuPDF/pdfplumber for coordinates.

2. Build a coordinate span index.
   - Extract per-page text blocks, lines, spans, and bounding boxes.
   - Preserve page numbers as 1-based values in user-facing output.
   - Keep original text snippets for evidence.

3. Build or import structure.
   - Use MinerU for sections, headings, captions, formulas, tables, and references when the document is complex.
   - For simple PDFs, coordinate spans may be enough.

4. Align chunks to spans.
   - Match normalized text from structural chunks to nearby PDF spans.
   - Store page range and bbox list per chunk.
   - If exact alignment fails, report the page-level anchor and lower confidence.

5. Search.
   - Exact phrase or regex for quoted text, terms, formula labels, citation keys, and table numbers.
   - BM25 or keyword scoring for short queries.
   - Embeddings for natural-language questions.
   - Structure filters for Abstract, Methods, Results, References, Table, Figure, or a named section.

6. Verify.
   - Re-open the original span text around each hit.
   - Prefer answers whose excerpt exactly supports the claim.
   - Render a highlighted page image when visual confirmation is requested.

## Result Format

Use this shape for location answers:

```text
Hit 1
Location: page 7, Section 3.2
Type: body paragraph
BBox: (72, 214, 512, 286)
Match: exact phrase + semantic rerank
Confidence: high
Excerpt: ...
Next action: can render a highlighted page image
```

If returning JSON, use:

```json
{
  "hits": [
    {
      "page": 7,
      "section_path": ["3", "3.2"],
      "kind": "body_paragraph",
      "bbox": [72, 214, 512, 286],
      "match": ["exact_phrase", "semantic"],
      "confidence": "high",
      "excerpt": "..."
    }
  ]
}
```

## Tool Notes

- PyMuPDF is good for page text dictionaries, spans, blocks, bboxes, and rendering.
- pdfplumber is good for text/table extraction and page-coordinate inspection.
- pypdfium2 is good for fast rendering and visual QA.
- MinerU is good for structure; do not rely on it alone for final highlight coordinates unless its output includes suitable anchors for the current file.

## Common Mistakes

- Returning a Markdown chunk without page or bbox for a location request.
- Treating semantic similarity as proof without checking the original PDF text.
- Mixing 0-based internal page indexes with 1-based user-facing page numbers.
- Overclaiming coordinates when OCR text and visual layout are not aligned.

