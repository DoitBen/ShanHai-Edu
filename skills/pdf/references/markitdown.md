# markitdown Route

Use markitdown for lightweight conversion of mixed document formats to Markdown, especially for LLM ingestion when high-fidelity PDF layout is not required.

## Local State

The default Python installation had markitdown `0.1.5` installed on 2026-06-02. PyPI latest observed then was `0.1.6`.

Probe before use:

```powershell
python -m pip show markitdown
```

## When to Use

- DOCX, PPTX, XLSX, HTML, EPUB, images, or simple documents to Markdown.
- Quick extraction for summarization or LLM context.
- Batch conversion where rough structure is acceptable.
- Simple PDFs where page coordinates, formulas, tables, and layout fidelity do not matter.

## When Not to Use

- Complex academic PDFs with formulas, tables, figures, citations, or multi-column layout.
- Scanned PDFs where OCR quality matters.
- Tasks requiring page number, bounding box, source highlight, or exact provenance.
- Production-grade paper corpus parsing unless benchmarked against MinerU.

## Suggested Flow

1. Probe markitdown installation.
2. Convert the source file to Markdown.
3. Inspect a sample of the output when fidelity matters.
4. If the output loses important layout or structure, switch to MinerU or PDF-native extraction.

## Provenance Warning

Markdown output alone is not enough for precise PDF search. If the user asks "where" something appears, pair the conversion with PDF coordinate extraction or switch to the coordinate-location workflow.

