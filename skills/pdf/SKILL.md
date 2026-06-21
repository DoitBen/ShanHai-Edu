---
name: pdf
description: Use when working with PDFs or document parsing, including PDF search, page or bbox location, OCR, Markdown conversion, markitdown, MinerU, forms, rendering, merge, split, rotate, watermark, encryption, tables, formulas, academic papers, textbooks, or knowledge-base ingestion.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF Skill Router

## Core Rule

Use this skill as the entry point for PDF and document parsing tasks. First classify the user's goal, then route to the smallest tool chain that can preserve the evidence the user needs.

Do not treat Markdown conversion, document understanding, and PDF coordinate location as the same task:

- `markitdown` is for lightweight multi-format conversion to Markdown.
- MinerU is for high-fidelity document parsing, especially complex PDFs.
- PyMuPDF, pdfplumber, pypdfium2, Poppler, pypdf, ReportLab, and pdf-lib are for PDF-native operations, rendering, text spans, coordinates, forms, and file manipulation.

## Start Here

1. Identify the task type from the user's requested outcome.
2. Probe the current runtime before using external binaries or machine-specific environments.
3. Read only the relevant reference file below.
4. Return source evidence when the task involves extraction, search, or location.

## Routing Table

| User goal | Default route | Read |
|---|---|---|
| Merge, split, rotate, encrypt, watermark, create PDF | `pypdf`, `pdf-lib`, ReportLab, qpdf if available | `references/pdf-operations.md` |
| Fill or inspect PDF forms | Existing form scripts and `forms.md` | `forms.md` |
| Render pages, make screenshots, visual QA | `pypdfium2`, PyMuPDF, or Poppler after probing | `references/pdf-operations.md` |
| Extract plain text or simple tables from a text PDF | pdfplumber or PyMuPDF | `references/pdf-operations.md` |
| Convert DOCX, PPTX, XLSX, HTML, EPUB, images, or simple documents to Markdown | markitdown | `references/markitdown.md` |
| Parse papers, textbooks, scanned PDFs, formulas, complex tables, figures, references, or knowledge-base corpus PDFs | MinerU pipeline by default | `references/mineru.md` |
| Locate search hits in the original PDF with page, section, bbox, and excerpt | MinerU structure plus PyMuPDF/pdfplumber coordinate index | `references/coordinate-location.md` |
| OCR a scanned or mixed PDF | Probe OCR tools; prefer MinerU OCR when Tesseract is unavailable | `references/ocr.md` |

If a task spans multiple rows, combine routes. For example, precise paper search usually needs MinerU for structure and PyMuPDF/pdfplumber for coordinates.

For fuller task classification, read `references/routing.md`.

## HB Windows Runtime

Before rendering pages, OCRing scans, or calling external PDF tools on this machine, read `C:\Users\HB\.agents\skills\document-toolchain-hb.md` and probe the current shell.

Use this probe:

```powershell
$cmds = 'soffice','pandoc','pdftoppm','tesseract','magick','node','npm','uv'
foreach ($c in $cmds) {
  $x = Get-Command $c -ErrorAction SilentlyContinue
  if ($x) { "$c`t$($x.Source)" } else { "$c`tNOT_FOUND" }
}
```

Only use OCR workflows that call `pytesseract` after confirming the `tesseract` binary exists. If an external helper is missing, switch to an available Python library or MinerU route instead of treating the task as blocked.

## HB MinerU Runtime

For high-fidelity PDF structure extraction on this machine, prefer the verified MinerU environment before building a new parser from scratch:

```powershell
$MinerURoot = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525"
$MinerUPython = "$MinerURoot\.venv-mineru\Scripts\python.exe"
$MinerUExe = "$MinerURoot\.venv-mineru\Scripts\mineru.exe"
$env:MINERU_EXE = $MinerUExe
```

Known local state checked on 2026-06-02:

- MinerU package: `3.2.0`; PyPI latest observed then: `3.2.1`.
- Main pipeline model cache: `C:\Users\HB\.cache\huggingface\hub\models--opendatalab--PDF-Extract-Kit-1.0`.
- Pipeline model snapshot SHA: `d1336ee3c2975a8b26c4b09ff39dc6b593d34141`; it matched Hugging Face `opendatalab/PDF-Extract-Kit-1.0` at check time.
- Default VLM model in MinerU 3.2.0/3.2.1 code: `opendatalab/MinerU2.5-Pro-2605-1.2B`; not downloaded locally at check time.
- Shared manifest directory for this machine: `E:\desktop\AI\12_local-models\document-parsing\manifests`.

Use `pipeline`/`PDF-Extract-Kit-1.0` as the default for batch academic PDF corpus work because it is stable and hallucination-free. Treat VLM or hybrid backends as optional spot-check tools for complex pages; they are separate from the pipeline model and do not replace it. Before upgrading MinerU or moving model caches, run a small smoke test in a copied environment.

## Precise PDF Search and Location

When the user asks where a claim, term, table, formula, or idea appears in a paper, do not stop at a Markdown excerpt. Return a source-location answer whenever possible:

```text
Hit 1
Location: page 7, Section 3.2
Type: body paragraph
BBox: (72, 214, 512, 286)
Match: keyword + semantic
Excerpt: ...
Next action: can render a highlighted page image
```

Use `references/coordinate-location.md` for the workflow.

## Existing References

- Advanced PDF operations and library examples: `reference.md`.
- Fillable forms: `forms.md`.
- Existing deterministic scripts: `scripts/`.

