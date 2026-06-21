# MinerU Route

Use MinerU for high-fidelity document parsing, especially complex PDFs, papers, textbooks, scanned documents, formulas, tables, figures, captions, references, and knowledge-base corpus ingestion.

## Local Runtime

Use the verified environment:

```powershell
$MinerURoot = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525"
$MinerUPython = "$MinerURoot\.venv-mineru\Scripts\python.exe"
$MinerUExe = "$MinerURoot\.venv-mineru\Scripts\mineru.exe"
$env:MINERU_EXE = $MinerUExe
```

Probe before use:

```powershell
if (Test-Path $MinerUExe) { & $MinerUExe --version } else { "MinerU exe not found: $MinerUExe" }
```

## Default Backend

Prefer `pipeline` for batch paper and corpus work:

```powershell
& $MinerUExe -p "input.pdf" -o "output-dir" -b pipeline -m auto -l en
```

Use `-m txt` for selectable text PDFs when OCR is unnecessary. Use `-m ocr` for image-based PDFs when OCR is needed. Keep `-f true` and `-t true` when formulas and tables matter.

## VLM and Hybrid Backends

Treat VLM or hybrid backends as optional spot-check or high-accuracy routes for difficult pages. They are not the default batch route on this machine because the default VLM model was not downloaded locally at the last check.

Use them only after confirming model availability or server URL:

```powershell
& $MinerUExe -p "input.pdf" -o "output-dir" -b hybrid-auto-engine -m auto -l en
```

## When MinerU Is the Right Choice

- The user asks about academic papers, formulas, references, tables, figures, or reading order.
- The PDF has multi-column layout or mixed text/images.
- The output should feed a knowledge base.
- The document is scanned or partly scanned.
- Markdown must preserve more structure than plain text extraction.

## When Not to Use MinerU

- Simple merge, split, rotate, watermark, encryption, or form filling.
- Quick conversion of Office/HTML/EPUB files where markitdown is enough.
- Precise PDF highlighting by itself; MinerU should be paired with coordinate extraction.

## Output Handling

Keep both structural and source artifacts:

- Markdown for readable chunks.
- JSON or intermediate parse output when available.
- Extracted page images and figure/table assets.
- Original PDF path for coordinate alignment.

For precise search, continue with `coordinate-location.md`.

