# OCR Route

Use this route for scanned PDFs, image-only pages, mixed PDFs, or requests that mention OCR.

## Probe First

On this machine, do not assume Tesseract exists. Probe before using pytesseract:

```powershell
$cmds = 'tesseract','pdftoppm','magick'
foreach ($c in $cmds) {
  $x = Get-Command $c -ErrorAction SilentlyContinue
  if ($x) { "$c`t$($x.Source)" } else { "$c`tNOT_FOUND" }
}
```

If `tesseract` is missing, avoid pytesseract workflows. Prefer MinerU OCR for document parsing, or use Python rendering libraries for non-OCR visual tasks.

## Route Selection

| Case | Route |
|---|---|
| Scanned paper or textbook | MinerU pipeline with `-m ocr` |
| Mixed text and image PDF | MinerU pipeline with `-m auto` |
| Simple image OCR and Tesseract exists | Render pages, then pytesseract |
| Need page highlight after OCR | OCR route plus coordinate-location workflow |

## MinerU OCR Example

```powershell
$MinerURoot = "E:\desktop\TAL_FULL_PDF_AND_CORPUS_20260525"
$MinerUExe = "$MinerURoot\.venv-mineru\Scripts\mineru.exe"
& $MinerUExe -p "input.pdf" -o "output-dir" -b pipeline -m ocr -l en
```

## Reporting Limits

OCR coordinates may be less reliable than selectable text spans. When returning locations from OCR results, state confidence and offer rendered visual confirmation if the user needs exact evidence.

