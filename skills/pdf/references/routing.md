# PDF Task Routing

Route by the user's desired evidence, not by file extension alone.

## Decision Rules

Use the smallest route that preserves the output the user needs:

- If the user wants to change the PDF file itself, use PDF-native tools.
- If the user wants quick Markdown from mixed document formats, use markitdown.
- If the user wants faithful structure from a complex PDF, use MinerU.
- If the user wants to prove where something appears in the original PDF, use coordinate extraction even if Markdown is also produced.
- If the document is scanned or mixed, probe OCR support and prefer MinerU OCR when local Tesseract is unavailable.

## Task Matrix

| Signals in request | Route |
|---|---|
| "merge", "split", "rotate", "encrypt", "decrypt", "watermark", "create PDF" | Basic PDF operations |
| "fill this form", "fields", "fillable", "AcroForm" | Form scripts and `forms.md` |
| "render", "screenshot", "preview page", "visual check" | pypdfium2, PyMuPDF, or Poppler after probing |
| "extract text", "extract table" from a simple text PDF | pdfplumber or PyMuPDF |
| "convert to Markdown", "DOCX/PPTX/HTML/EPUB to Markdown", "LLM ingest" | markitdown unless the PDF is complex |
| "paper", "academic", "formula", "table", "figure", "caption", "reference", "layout", "textbook", "knowledge base" | MinerU pipeline |
| "where does it say", "locate", "page", "highlight", "bbox", "source evidence" | Coordinate location workflow |
| "scanned", "OCR", "image-only", "no selectable text" | OCR workflow |

## Combining Routes

Complex tasks often need two routes:

- Paper to searchable knowledge base: MinerU plus chunk/index generation.
- Precise paper search: MinerU structure plus PyMuPDF/pdfplumber coordinate spans.
- Highlight a search result: coordinate extraction plus page rendering.
- Convert Office to Markdown then index: markitdown plus downstream indexing.

## Avoid These Mistakes

- Do not use markitdown as the main parser for complex academic PDFs when formulas, tables, figures, or source-location fidelity matter.
- Do not use MinerU for simple merge/split/rotate tasks.
- Do not call OCR binaries without probing whether they exist.
- Do not answer precise location questions with only a Markdown chunk when a PDF coordinate anchor is available or can be built.

