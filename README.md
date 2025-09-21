# OMR Evaluation System

**Author:** Muhammad Riyas
**Date:** 20/09/2025


## Overview

The **OMR Evaluation System** is a Django-based web application that automates the evaluation of OMR sheets. It is designed to save teachers and exam administrators time and reduce errors in scoring large batches of exam sheets.

Key features:
- Upload scanned OMR sheets (PDF/ZIP) in bulk
- Upload answer keys (CSV or form input)
- Detect filled bubbles using OpenCV
- Extract student information via OCR
- Score sheets automatically and flag ambiguities
- Export results to Excel or CSV
- Minimal, clean web interface
- Local storage by default (privacy-focused)


## Project Documentation

The `/docs` folder contains all key project documents:

| File | Purpose |
|------|---------|
| `vision.md` | Problem statement, target users, goals |
| `functional_spec.md` | Features, MVP, user stories, future roadmap |
| `technical_design.md` | Architecture, data model, processing engine, endpoints |
| `folder_structure.md` | Project folder hierarchy and structure |
| `workflow.md` | Step-by-step system workflow |
| `roadmap.md` | MVP development plan (day-by-day) |


## Folder Structure

The main project structure is available in [`docs/folder_structure.md`](docs/folder_structure.md).


## Getting Started

### Prerequisites
- Python 3.9+
- pip or poetry
- Virtual environment recommended

### Installation
```bash
# Clone the repository
git clone <repo_url>
cd omr_evaluator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the app
```bash
# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver
```

Access the app at http://127.0.0.1:8000/.


## Testing

- **Unit tests** for processing modules: `/processing/tests/`
- **Django app tests**: `/omr/tests/`
- **Integration tests** for end-to-end workflow

Run all tests with:

```bash
python manage.py test
```


## Future Enhancements

- Multi-template OMR support
- Student login portal
- Analytics dashboards
- Cloud/SaaS deployment


## License

This project is for **personal/educational use**. Commercial use requires explicit permission from the author.


## Contact

**Author:** Muhammad Riyas
**Email:** `muhammadriyask11@gmail.com`
