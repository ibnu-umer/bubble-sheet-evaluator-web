# Functional Specification – OMR Evaluation System

## 1. Core Features (MVP)
The minimum viable product will provide the following features:

1. Upload OMR sheets (PDF/ZIP).
2. Upload answer key (CSV or manual form input).
3. Process sheets:
   - Detect filled bubbles using OpenCV.
   - Compare with answer key to assign marks.
4. Export results in Excel/CSV format.
5. Flag ambiguous or invalid sheets for manual review.

### Non-Functional Expectations
- Process 100 sheets in under 5 minutes.
- Detection accuracy >95%.
- Consistent results on repeated runs.
- Local storage of all files and results by default.


## 2. Future Features
1. Student login portal to view individual results.
2. Multi-template support for different OMR layouts.
3. SaaS deployment to support multiple institutes.


## 3. User Stories
- **Teacher:** As a teacher, I can upload scanned OMR sheets so that I can avoid manual evaluation.
- **Teacher:** As a teacher, I can download an Excel file with marks so that I can share results easily.
- **Admin:** As an admin, I can review flagged sheets to resolve ambiguous answers.
- **Admin (Future):** As an admin, I can configure multiple templates for different exams.


## 4. Out of Scope (MVP)
- Mobile phone photo inputs (only scanned A4 PDFs supported).
- Support for multiple OMR sheet layouts (MVP supports single template).
- Cloud-based multi-tenant features.


## 5. Workflow Overview
1. Teacher/Admin uploads OMR sheets and answer key.
2. System converts PDFs to images and preprocesses them.
3. Bubbles are detected, matched with the answer key, and scores are calculated.
4. Results stored in DB and exported to Excel/CSV.
5. Ambiguous sheets are flagged for manual review.
