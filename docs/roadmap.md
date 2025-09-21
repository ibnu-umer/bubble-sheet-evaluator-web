# OMR Evaluation System – MVP Roadmap (Day-by-Day)

| Day | Task | Deliverable / Notes |
|-----|------|-------------------|
| 0–1 | Environment Setup | Git repo, virtual environment, core packages installed, `.env`, `.gitignore` |
| 1–2 | Core App Structure | Django project/app created, folder structure in place, server runs |
| 2–3 | File Upload Module | OMR sheets (PDF/ZIP) & answer key (CSV) upload working, stored in `/media/uploads/` |
| 3–4 | PDF → Image Conversion | PDFs converted to images, multiple pages handled, stored in `/media/processed/` |
| 4–5 | Preprocessing Pipeline | Grayscale, blur, thresholding, skew correction; module in `/processing/sheet_parser.py` |
| 5–7 | Bubble Detection & Answer Evaluation | Detect bubbles, map to questions, compare with answer key, calculate scores, flag ambiguities |
| 6–7 | OCR Extraction | Crop header, extract student info (name/roll) with `pytesseract`, clean text with regex |
| 7–8 | Results Storage & Export | Django models (`Student`, `Exam`, `OMRResult`), save results, export to Excel/CSV |
| 8–9 | Web Interface | Minimal UI: upload pages, processing status, download results, optionally show table of processed sheets |
| 9–10 | Testing & Validation | Unit tests (modules), integration tests (full workflow), edge case handling (multiple/half-filled/rotated sheets) |
| Future | Optional Enhancements | Multi-template support, student portal, analytics dashboard, cloud/SaaS deployment |
