# HackTheBias 2026 Project

A FastAPI-based application designed to reduce hiring bias by parsing, anonymizing, and semantically matching resumes and job descriptions.

## Features

- **Resume Parsing**: Extract structured data from PDF resumes using `pdfplumber`.
- **Anonymization**: Remove personally identifiable information (PII) to ensure unbiased screening using `spacy` NER.
- **Semantic Matching**: Match candidates to jobs based on skills and context using `sentence-transformers`.
- **REST API**: Built with `FastAPI` for high performance and easy integration.
- **React Frontend**: Modern UI built with React and Vite.

## Getting Started

### Prerequisites

- **Python 3.9+** (Python 3.14 is currently unsupported by some dependencies)
- **Node.js 18+** (for frontend)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd hackthebiasproject
   ```

2. **Create a Virtual Environment**
   ```bash
   python3.11 -m venv venv
   ```

3. **Activate the Virtual Environment**
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download spaCy Model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

6. **Run the Backend Server**
   ```bash
   uvicorn main:app --reload
   ```
   - API: `http://127.0.0.1:8000`
   - Docs: `http://127.0.0.1:8000/docs`

### Frontend Setup

1. **Navigate to frontend folder**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```
   - Frontend: `http://localhost:3000`

## Project Structure

```
hackthebiasproject/
├── app/
│   ├── routes/          # API endpoints
│   └── services/        # Business logic
├── core/
│   └── database.py      # SQLite database with SQLModel
├── models/              # Pydantic models
├── utils/
│   ├── anonymizer.py    # PII removal
│   ├── parser.py        # PDF extraction
│   └── semantics.py     # NLP matching
├── frontend/            # React + Vite frontend
├── main.py              # FastAPI entry point
└── requirements.txt     # Python dependencies
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jobs/` | GET | List all jobs |
| `/jobs/` | POST | Create a job |
| `/users/upload-resume` | POST | Upload resume & create/update user |
| `/applications/` | POST | Create application |
