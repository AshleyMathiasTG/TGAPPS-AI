# TGAPP-AI - AI-Powered Resume Parser

An intelligent ATS (Applicant Tracking System) resume parser that extracts structured information from PDF resumes using OpenAI's GPT-4.1-mini. The system supports JD-based skill filtering to match candidate skills against job requirements.

## Features

- **Document Text Extraction**: Extracts text from PDF, DOCX, and DOC resume files using `pdfplumber` and `python-docx`
- **Regex-based Extraction**: Extracts emails, phone numbers, LinkedIn URLs, and dates of birth
- **AI-Powered Structured Parsing**: Uses OpenAI GPT-4.1-mini to extract:
  - Education history with highest degree identification
  - Work experience with projects and compensation details
  - Skills and competencies with years of experience
  - Addresses and locations
- **JD-Based Skill Filtering**: Two-step process to match resume skills against Job Description requirements
- **Robust Error Handling**: Comprehensive exception handling for all operations
- **Singleton API Client**: Optimized OpenAI client management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AshleyMathiasTG/TGAPP-AI.git
cd TGAPP-AI
```

2. Create a virtual environment:
```bash
python -m venv venv
# On Windows (PowerShell)
.\venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
```bash
# On Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# On Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage (Without JD Filtering)

```python
from main import parse_resume

result = parse_resume("Resume/resume9.pdf")  # PDF
# or
result = parse_resume("Resume/resume.docx")  # DOCX
# or
result = parse_resume("Resume/resume.doc")    # DOC
print(result)
```

### Usage with JD-Based Skill Filtering

```python
from main import parse_resume

result = parse_resume(
    doc_path="Resume/resume9.pdf",  # Supports PDF, DOCX, or DOC
    jd_path="jds/EUC_Delivery_lead.txt"
)
print(result)
```

### Command Line Usage

1. Place your resume document (PDF, DOCX, or DOC) in the `Resume/` directory
2. Place your Job Description in the `jds/` directory (optional)
3. Update the `doc_path` and `jd_path` variables in `main.py` (lines 584-585)
4. Run the parser:
```bash
python main.py
```

The script outputs structured JSON data to stdout and logs progress/errors to stderr.

**Supported Document Formats:**
- PDF (`.pdf`) - Using `pdfplumber`
- DOCX (`.docx`) - Using `python-docx`
- DOC (`.doc`) - Using `python-docx` (Note: Limited support for older .doc format)

## Function Documentation

### Core Functions

#### `get_openai_client()`
**Purpose**: Singleton pattern to manage OpenAI client instance  
**Returns**: `OpenAI` client instance  
**Error Handling**: Raises `ValueError` if `OPENAI_API_KEY` environment variable is not set  
**Location**: Lines 14-22

Creates a single OpenAI client instance that is reused across all API calls, optimizing resource usage and connection management.

---

#### `extract_emails(text: str) -> list`
**Purpose**: Extract email addresses from text using regex  
**Parameters**: 
- `text`: Input text to search
**Returns**: List of unique email addresses  
**Location**: Lines 28-29

Uses regex pattern `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+` to find all email addresses.

---

#### `extract_phone_numbers(text: str) -> list`
**Purpose**: Extract phone numbers from text using regex  
**Parameters**: 
- `text`: Input text to search
**Returns**: List of unique phone numbers (normalized)  
**Location**: Lines 31-34

Uses regex pattern to match various phone number formats including international formats with country codes.

---

#### `extract_linkedin(text: str) -> str | None`
**Purpose**: Extract LinkedIn profile URL from text  
**Parameters**: 
- `text`: Input text to search
**Returns**: First LinkedIn URL found, or `None`  
**Location**: Lines 36-38

Matches LinkedIn URLs in formats: `https://linkedin.com/...`, `https://www.linkedin.com/...`, `http://linkedin.com/...`

---

#### `extract_dob(text: str) -> str | None`
**Purpose**: Extract date of birth from text  
**Parameters**: 
- `text`: Input text to search
**Returns**: Date string in format found, or `None`  
**Location**: Lines 40-42

Matches patterns like "DOB: 01/01/1990" or "Date of Birth: 01-01-1990"

---

#### `extract_text_from_document(doc_path: str) -> str`
**Purpose**: Extract text from document files (PDF, DOCX, or DOC) with automatic file type detection  
**Parameters**: 
- `doc_path`: Path to document file (PDF, DOCX, or DOC)
**Returns**: Extracted text content  
**Error Handling**: 
- Raises `FileNotFoundError` if file doesn't exist
- Raises `ValueError` if file type not supported or file is empty
- Raises `RuntimeError` for other extraction failures
**Location**: Lines 81-117

Automatically detects file type based on extension and uses appropriate parser:
- **PDF**: Uses `pdfplumber` to extract text from all pages
- **DOCX/DOC**: Uses `python-docx` to extract text from paragraphs and tables

#### `extract_text_from_docx(docx_path: str) -> str`
**Purpose**: Extract text from DOCX/DOC files  
**Parameters**: 
- `docx_path`: Path to DOCX or DOC file
**Returns**: Extracted text from paragraphs and tables  
**Error Handling**: 
- Raises `FileNotFoundError` if file doesn't exist
- Raises `ValueError` if file has no content
- Raises `RuntimeError` for other extraction failures
**Location**: Lines 49-79

Extracts text from both paragraphs and tables in Word documents.

#### `extract_text_from_pdf(pdf_path: str) -> str`
**Purpose**: Extract all text content from a PDF file (legacy function for backward compatibility)  
**Parameters**: 
- `pdf_path`: Path to PDF file
**Returns**: Concatenated text from all pages  
**Note**: This function now calls `extract_text_from_document()` internally. Use `extract_text_from_document()` for automatic file type detection.
**Location**: Lines 119-123

---

#### `extract_structured_fields(text: str) -> dict`
**Purpose**: Extract structured resume data using LLM  
**Parameters**: 
- `text`: Resume text content
**Returns**: Dictionary with structured resume data  
**Error Handling**: 
- Raises `ValueError` for empty text or API key issues
- Raises `RuntimeError` for API errors, rate limits, connection issues, or JSON parsing failures
**Location**: Lines 64-215

**Extracted Fields**:
- `emails`: List of email addresses
- `contact_numbers`: List of phone numbers
- `linkedin_url`: LinkedIn profile URL
- `date_of_birth`: Date of birth string
- `education`: Array of education entries with:
  - `degree`: Degree name (e.g., "Bachelor of Science")
  - `subject`: Subject/major
  - `year_passed`: Year or date range as written
  - `result`: Grade/GPA
  - `college_university`: Institution name
  - `percentage`: Percentage score
  - `is_highest`: Boolean indicating highest degree
- `experience`: Array of work experience entries with:
  - `organization`: Company name
  - `job_title`: Job title
  - `location`: Work location
  - `start_date`: Start date
  - `end_date`: End date ("Present" if current)
  - `last_pay_rate`: Last salary
  - `pay_uom`: Pay unit of measure (e.g., "USD/year")
  - `last_hike_date`: Last salary hike date
  - `projects`: Array of project entries with:
    - `project_name`: Project name
    - `project_details`: Project description
- `skills`: Array of skill entries with:
  - `skillset_type`: Type of skill (e.g., "Technical", "Soft Skills")
  - `skill_name`: Name of the skill
  - `years`: Years of experience
  - `last_used`: Last used date
- `addresses`: Array of address entries with:
  - `address`: Address string
  - `start_date_active`: Start date (usually empty)
  - `end_date_active`: End date (usually empty)

**LLM Configuration**:
- Model: `gpt-4.1-mini`
- Temperature: `0` (deterministic output)
- Uses strict system prompt to prevent inference or fabrication

---

### JD-Based Skill Filtering Functions

#### `read_jd_file(jd_path: str) -> str`
**Purpose**: Read Job Description text from a file  
**Parameters**: 
- `jd_path`: Path to JD text file
**Returns**: JD text content, or empty string if file not found/invalid  
**Error Handling**: Prints warnings to stderr for file errors, returns empty string  
**Location**: Lines 221-241

Reads JD file with UTF-8 encoding, handles encoding errors gracefully, and returns empty string for missing or empty files.

---

#### `extract_jd_skills(jd_text: str) -> list`
**Purpose**: Extract skills explicitly mentioned in Job Description using LLM  
**Parameters**: 
- `jd_text`: Job Description text content
**Returns**: List of skill names (normalized to lowercase)  
**Error Handling**: Prints warnings to stderr, returns empty list on errors  
**Location**: Lines 243-403

**Extraction Strategy**:
- Handles multiple JD formats (structured sections, lists, narrative text, tables)
- Extracts from sections like "Technology Scope", "Required Skills", "Key Responsibilities"
- Extracts both full names and abbreviations (e.g., "Microsoft SCCM" and "SCCM")
- Does NOT infer skills (e.g., "daily stand-ups" does NOT mean "Agile")
- Normalizes all skills to lowercase for comparison

**LLM Configuration**:
- Model: `gpt-4.1-mini`
- Temperature: `0`
- Returns JSON array of skill names

**Example Output**:
```json
["vmware horizon vdi", "microsoft sccm", "jira", "sap ecc", "s/4hana"]
```

---

#### `match_resume_skills_with_jd(resume_skill_names: list, jd_skills: list) -> list`
**Purpose**: Match resume skills against extracted JD skills  
**Parameters**: 
- `resume_skill_names`: List of skill names from resume
- `jd_skills`: List of skill names extracted from JD (lowercase)
**Returns**: List of matching resume skill names  
**Error Handling**: Prints warnings to stderr, returns empty list on errors  
**Location**: Lines 406-487

**Matching Rules**:
1. Exact match (case-insensitive)
2. Version/variant matching:
   - JD: "Python" → Resume: "Python 3" ✓
   - JD: "SQL" → Resume: "MySQL", "PostgreSQL" ✓
   - JD: "VMware Horizon" → Resume: "VMware", "VMware VDI" ✓
3. Semantic similarity:
   - JD: "Project Management" → Resume: "Program Management" ✓
   - JD: "Process Improvements" → Resume: "Process Optimization" ✓
4. Prioritizes precision over recall (when in doubt, don't match)

**LLM Configuration**:
- Model: `gpt-4.1-mini`
- Temperature: `0`
- Returns JSON array of matching resume skill names

---

#### `filter_skills_by_jd(extracted_skills: list, jd_text: str) -> list`
**Purpose**: Main orchestrator for JD-based skill filtering (two-step process)  
**Parameters**: 
- `extracted_skills`: List of skill objects from resume extraction
- `jd_text`: Job Description text content
**Returns**: Filtered list of skill objects that match JD requirements  
**Error Handling**: Returns empty list if JD text is empty or no skills extracted  
**Location**: Lines 490-525

**Process Flow**:
1. Extract skills from JD using `extract_jd_skills()`
2. Get skill names from resume skill objects
3. Match resume skills with JD skills using `match_resume_skills_with_jd()`
4. Filter original skill objects to keep only matched ones
5. Return filtered skill objects with all original metadata

**Logging**: Prints progress messages to stderr (number of JD skills extracted, number of resume skills, number of matches)

---

### Main Pipeline Function

#### `parse_resume(doc_path: str, jd_path: str | None = None) -> dict`
**Purpose**: Main entry point for resume parsing with optional JD filtering  
**Parameters**: 
- `doc_path`: Path to resume document file (PDF, DOCX, or DOC)
- `jd_path`: Optional path to Job Description text file
**Returns**: Complete parsed resume data dictionary  
**Error Handling**: 
- Raises `FileNotFoundError` if PDF not found
- Raises `ValueError` for invalid input or API configuration
- Raises `RuntimeError` for processing failures
**Location**: Lines 531-577

**Process Flow**:
1. Extract text from document (PDF, DOCX, or DOC) using `extract_text_from_document()`
2. Extract regex-based fields (emails, phone, LinkedIn, DOB)
3. Extract structured fields using `extract_structured_fields()`
4. If `jd_path` provided:
   - Read JD file using `read_jd_file()`
   - Filter skills using `filter_skills_by_jd()`
5. Return complete parsed data

**Output Format**: See `extract_structured_fields()` documentation for output structure.

---

## Architecture & Flow

```
┌─────────────────┐
│  Resume PDF     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ extract_text_   │
│ from_pdf()      │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│ Regex Extractors│  │ extract_        │
│ (emails, phone, │  │ structured_     │
│  LinkedIn, DOB) │  │ fields()        │
└─────────────────┘  └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Structured Data │
                    │ (education,     │
                    │  experience,    │
                    │  skills, etc.) │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
         ┌──────────────────┐  ┌──────────────────┐
         │ No JD Provided   │  │ JD Provided      │
         │ Return all       │  │ filter_skills_   │
         │ skills           │  │ by_jd()          │
         └──────────────────┘  └────────┬─────────┘
                                        │
                           ┌────────────┴────────────┐
                           │                         │
                           ▼                         ▼
                  ┌─────────────────┐      ┌─────────────────┐
                  │ extract_jd_     │      │ match_resume_    │
                  │ skills()        │      │ skills_with_jd() │
                  └────────┬────────┘      └────────┬────────┘
                           │                         │
                           └────────────┬────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │ Filtered Skills │
                              │ (JD-matched)    │
                              └─────────────────┘
```

## Error Handling

The system implements comprehensive error handling:

- **File Operations**: `FileNotFoundError` for missing files, `UnicodeDecodeError` for encoding issues
- **API Operations**: `RateLimitError`, `APIConnectionError`, `APIError` for OpenAI API issues
- **Data Validation**: `ValueError` for invalid inputs, empty responses
- **JSON Parsing**: `JSONDecodeError` with descriptive error messages
- **Graceful Degradation**: Warnings printed to stderr, operations continue where possible

All errors are logged to stderr, and the main script exits with appropriate exit codes:
- `1`: General errors
- `130`: Keyboard interrupt (Ctrl+C)

## Output Format

The parser returns a JSON object with the following structure:

```json
{
  "emails": ["email@example.com"],
  "contact_numbers": ["+1-234-567-8900"],
  "linkedin_url": "https://linkedin.com/in/profile",
  "date_of_birth": "01/01/1990",
  "education": [
    {
      "degree": "Bachelor of Science",
      "subject": "Computer Science",
      "year_passed": "2020",
      "result": "First Class",
      "college_university": "University Name",
      "percentage": "85%",
      "is_highest": false
    }
  ],
  "experience": [
    {
      "organization": "Company Name",
      "job_title": "Software Engineer",
      "location": "City, Country",
      "start_date": "2020-01",
      "end_date": "Present",
      "last_pay_rate": "",
      "pay_uom": "",
      "last_hike_date": "",
      "projects": [
        {
          "project_name": "Project Name",
          "project_details": "Project description"
        }
      ]
    }
  ],
  "skills": [
    {
      "skillset_type": "Technical",
      "skill_name": "Python",
      "years": "5",
      "last_used": "2024"
    }
  ],
  "addresses": [
    {
      "address": "City, State, Country",
      "start_date_active": "",
      "end_date_active": ""
    }
  ]
}
```

## Project Structure

```
TGAPP-AI/
├── main.py                    # Main resume parser script
├── backup_main.py            # Backup of main script
├── backup_main2.py           # Additional backup
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── LICENSE                   # MIT License
├── Resume/                   # Directory for resume PDFs
│   ├── resume7.pdf
│   ├── resume9.pdf
│   └── ...
├── jds/                      # Directory for Job Descriptions
│   ├── EUC_Delivery_lead.txt
│   ├── program_manager.txt
│   ├── data_analyst.txt
│   └── ...
└── venv/                     # Virtual environment (gitignored)
```

## Technologies Used

- **Python 3.13**: Programming language
- **OpenAI GPT-4.1-mini**: LLM for structured extraction and skill matching
- **pdfplumber**: PDF text extraction library
- **python-docx**: DOCX/DOC text extraction library
- **Regular Expressions**: Pattern matching for contact details
- **JSON**: Data serialization format

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required. Your OpenAI API key for accessing GPT-4.1-mini

### Model Configuration

- **Model**: `gpt-4.1-mini`
- **Temperature**: `0` (deterministic, reproducible outputs)
- **Max Tokens**: Default (model-dependent)

## Limitations

1. **PDF Quality**: Text extraction quality depends on PDF structure. Scanned images require OCR preprocessing.
2. **LLM Accuracy**: Extraction accuracy depends on resume format and clarity. Complex layouts may require prompt tuning.
3. **Skill Matching**: Semantic matching may occasionally produce false positives or miss valid matches.
4. **API Rate Limits**: OpenAI API rate limits apply. The system handles rate limit errors gracefully.

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable is not set"**
   - Solution: Set the environment variable as shown in Installation section

2. **"PDF file not found"**
   - Solution: Verify the PDF path is correct and file exists

3. **"Empty response from OpenAI API"**
   - Solution: Check API key validity and account status

4. **"Rate limit exceeded"**
   - Solution: Wait and retry, or upgrade OpenAI plan

5. **Unicode encoding errors**
   - Solution: Ensure JD files are UTF-8 encoded

## License

MIT License

## Author

Ashley Mathias - TruGlobal AI Team

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style and patterns
- Error handling is comprehensive
- Functions are well-documented
- Tests are added for new features