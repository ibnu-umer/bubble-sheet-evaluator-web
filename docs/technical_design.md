# Technical Design Document – OMR Evaluation System

**Author:** Muhammad Riyas
**Date:** 20/09/2025


## 1. Purpose
Describes the technical architecture, design decisions, and implementation plan for the OMR Evaluation System.


## 2. Architecture Overview

### 2.1 System Components
1. **Frontend (Web Interface)**
   - Django Templates + Bootstrap/Tailwind
   - Upload sheets/keys, display progress, show results

2. **Backend (Django)**
   - File uploads, DB interactions, trigger processing pipeline

3. **Processing Engine (Python/OpenCV)**
   - PDF → Image (`pdf2image`)
   - Preprocessing (grayscale, threshold, skew correction)
   - Bubble detection (`OpenCV`)
   - OCR for student info (`pytesseract`)
   - Scoring

4. **Database**
   - PostgreSQL or SQLite (MVP)
   - Stores students, exams, results

5. **Export Module**
   - Excel/CSV export (`pandas` / `openpyxl`)


### 2.2 Data Flow
[Upload PDF/ZIP] → [PDF → Images] → [Preprocess Sheets] → [Bubble Detection] → [Answer Comparison] → [Store in DB] → [Export Results: Excel/CSV]


## 3. Data Model

### Student
- `roll_no` (PK)
- `name`
- `email` (optional)

### Exam
- `id` (PK)
- `name`
- `answer_key` (JSON/CSV)
- `template_type`
- `date`

### OMRResult
- `student_id` (FK)
- `exam_id` (FK)
- `answers` (JSON)
- `score`
- `flagged` (bool)


## 4. Processing Engine Design
- **PDF Conversion:** `pdf2image`, 300 dpi
- **Preprocessing:** Grayscale, blur, threshold, skew correction
- **Bubble Detection:** Contours → size/shape filtering → fill ratio
- **OCR:** Crop header, `pytesseract`, regex cleanup
- **Scoring:** Compare with answer key, flag invalid/ambiguous


## 5. API / View Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Upload PDF/ZIP + answer key |
| `/process` | POST | Start sheet evaluation |
| `/results/{exam_id}` | GET | Retrieve/export results |


## 6. Non-Functional Requirements
- Process 100 sheets in <5 minutes
- Bubble detection accuracy >95%
- Consistent results
- Local file storage by default
- Scalable for future templates and SaaS


## 7. Deployment
- Local Django dev server
- Production: Docker or cloud VM
- Optional async processing: Celery + Redis


## 8. Testing Strategy
- **Unit Tests:** Bubble detection, OCR, scoring
- **Integration Tests:** Upload → Process → Export
- **Edge Cases:** Multiple bubbles, half-filled, rotated sheets


## 9. Future Enhancements
- Student login portal
- Multiple templates per institute
- Cloud SaaS deployment
- Analytics dashboards

