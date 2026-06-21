# Basic PDF Operations

Use this route for PDF-native manipulation, rendering, form work, and simple extraction.

## Existing Detailed References

- `../reference.md` contains advanced pypdfium2, pdf-lib, PDF.js, and other examples.
- `../forms.md` contains fillable form instructions.
- `../scripts/` contains deterministic form and rendering helpers.

## Default Tools

| Task | Tool |
|---|---|
| Merge, split, rotate, decrypt, encrypt | `pypdf` or qpdf when available |
| Fill forms | Existing scripts, `pypdf`, or pdf-lib |
| Create simple PDFs | ReportLab |
| Render pages | pypdfium2, PyMuPDF, or Poppler `pdftoppm` after probing |
| Extract simple text | pdfplumber or PyMuPDF |
| Extract simple tables | pdfplumber |
| Extract images | Poppler `pdfimages` if available, otherwise PyMuPDF |

## Runtime Probe

Before depending on external commands:

```powershell
$cmds = 'pdftoppm','qpdf','tesseract','magick'
foreach ($c in $cmds) {
  $x = Get-Command $c -ErrorAction SilentlyContinue
  if ($x) { "$c`t$($x.Source)" } else { "$c`tNOT_FOUND" }
}
```

## Routing Reminder

Do not use MinerU for simple file operations. Do not use markitdown for PDF modifications. Use coordinate-location when the user asks for page-level or bbox-level source evidence.

