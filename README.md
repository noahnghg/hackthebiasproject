# HackTheBias Project

A FastAPI-based application designed to reduce hiring bias by parsing, anonymizing, and semantically matching resumes and job descriptions.

## Features (Planned)

- **Resume Parsing**: Extract structured data from PDF resumes using `pdfplumber`.
- **Anonymization**: Remove personally identifiable information (PII) to ensure unbiased screening using `spacy` NER.
- **Semantic Matching**: Match candidates to jobs based on skills and context using `sentence-transformers`.
- **REST API**: Built with `FastAPI` for high performance and easy integration.

## Getting Started

### Prerequisites

- **Python 3.9+** (Python 3.14 is currently unsupported by some dependencies, so Python 3.9 is recommended).

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd hackthebiasproject
   ```

2. **Create a Virtual Environment**
   It is recommended to use `venv` to manage dependencies.
   ```bash
   # Using Python 3.9 (or your reliable python3 executable)
   python3 -m venv venv
   ```

3. **Activate the Virtual Environment**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download Language Models**
   This project uses `spacy` for natural language processing. You need to download the English core model.
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Usage

### Running the Application

Start the development server using `uvicorn`:

```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. 
Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Project Structure

```
hackthebiasproject/
├── app/
│   ├── jobs.py          # Job description management
│   └── resumes.py       # Resume upload and processing logic
├── utils/
│   ├── anonymizer.py    # PII removal logic
│   ├── parser.py        # PDF extraction helpers
│   └── semantics.py     # Embedding and similarity scoring
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```
