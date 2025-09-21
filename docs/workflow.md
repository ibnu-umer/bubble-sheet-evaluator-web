# OMR Evaluation System – Workflow

1. **Upload OMR Sheets / Answer Key**
   - PDF or ZIP files

2. **PDF → Image Conversion**
   - Use `pdf2image` at 300 dpi
   - Each page becomes a separate image

3. **Preprocess Sheets**
   - Grayscale conversion
   - Gaussian blur to reduce noise
   - Thresholding to create binary images
   - Perspective/skew correction

4. **Bubble Detection**
   - Find contours using OpenCV
   - Filter by size and shape
   - Calculate fill ratio to classify as marked/unmarked

5. **OCR Extraction (Student Info)**
   - Crop header region
   - Use `pytesseract` to extract name and roll number
   - Clean text with regex

6. **Answer Evaluation**
   - Compare detected answers with answer key
   - Calculate score
   - Flag ambiguous or invalid sheets

7. **Store Results in Database**
   - Save student info, answers, and scores

8. **Export Results**
   - Generate Excel or CSV reports
   - Allow download for teachers/admins
