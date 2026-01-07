# TGAPP-AI

An AI-powered ATS (Applicant Tracking System) resume parser that extracts structured information from PDF resumes using OpenAI's GPT-4.

## Features

- **PDF Text Extraction**: Extracts text from PDF resumes using pdfplumber
- **Regex-based Extraction**: Extracts emails, phone numbers, LinkedIn URLs, and dates of birth
- **AI-Powered Parsing**: Uses OpenAI GPT-4 to extract structured data including:
  - Education history
  - Work experience with projects
  - Skills and competencies
  - Addresses

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AshleyMathiasTG/TGAPP-AI.git
cd TGAPP-AI
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

1. Place your resume PDF in the `Resume/` directory
2. Update the `pdf_path` variable in `main.py` to point to your resume
3. Run the parser:
```bash
python main.py
```

The script will output structured JSON data extracted from the resume.

## Output Format

The parser returns a JSON object with the following structure:
- `emails`: List of email addresses
- `contact_numbers`: List of phone numbers
- `linkedin_url`: LinkedIn profile URL
- `date_of_birth`: Date of birth
- `education`: Array of education entries
- `experience`: Array of work experience entries with projects
- `skills`: Array of skills with details
- `addresses`: Array of address entries

## Project Structure

```
TGAPP-AI/
├── main.py              # Main resume parser script
├── backup_main.py       # Backup of main script
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
├── Resume/             # Directory for resume PDFs (gitignored)
└── venv/              # Virtual environment (gitignored)
```

## Technologies Used

- Python 3.13
- OpenAI GPT-4 API
- pdfplumber for PDF processing
- Regular expressions for pattern matching

## License

MIT License

## Author

Ashley Mathias - TruGlobal AI Team

