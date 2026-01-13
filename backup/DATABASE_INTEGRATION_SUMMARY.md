# Database Integration Summary

## ✅ What Has Been Implemented

### 1. **DOC/DOCX Parser Support** (`main.py`)
   - Added support for parsing DOCX and DOC files alongside PDF
   - New functions:
     - `extract_text_from_docx()` - Extracts text from Word documents (paragraphs + tables)
     - `extract_text_from_document()` - Auto-detects file type (PDF/DOCX/DOC) and extracts text
   - Updated `parse_resume()` to accept any document format
   - Dependencies: `python-docx==1.1.0`

### 2. **Database Integration Module** (`db_integration.py`)
   A complete module that connects to your TGApps MySQL database and integrates with the AI parser.

   **Key Features:**
   - ✅ Database connection management
   - ✅ Retrieves candidate data by `candidate_id`
   - ✅ Downloads resume files from TGApps file server
   - ✅ Retrieves Job Descriptions for candidates
   - ✅ Parses resumes using AI (existing `main.py` logic)
   - ✅ Maps parsed data to database schema
   - ✅ **READ-ONLY** - No database updates
   - ✅ Comprehensive error handling
   - ✅ Automatic cleanup of temporary files

   **Database Tables Accessed:**
   - `mst_candidates` - Basic candidate information
   - `adm_attachments` - Resume file details
   - `mst_emails` - Email addresses
   - `mst_contact_numbers` - Contact numbers
   - `adm_skillsets` - Skills (for reference)
   - `adm_education` - Education details (for reference)
   - `mst_candidate_work_details` - Work experience (for reference)
   - `mst_requirements` + `adm_can_submissions` - Job descriptions

### 3. **Database Schema Mapping**
   The parsed resume data is mapped to your database schema:
   
   ```
   Parsed Data          →  Database Tables
   ─────────────────────────────────────────
   name                 →  mst_candidates.full_name
   linkedin_url         →  mst_candidates.linkedin_profile
   date_of_birth        →  mst_candidates.date_of_birth
   emails               →  mst_emails.email_address
   contact_numbers      →  mst_contact_numbers.contact_number
   skills               →  adm_skillsets.*
   education            →  adm_education.*
   experience           →  mst_candidate_work_details.*
   ```

### 4. **New Dependencies Installed**
   - `mysql-connector-python==9.5.0` - MySQL database connector
   - `requests==2.32.5` - HTTP library for file downloads
   - `urllib3==2.6.3` - HTTP client
   - `python-docx==1.1.0` - DOCX/DOC parsing

### 5. **Documentation**
   - `DB_INTEGRATION_README.md` - Comprehensive guide for database integration
   - `DATABASE_INTEGRATION_SUMMARY.md` - This file

## 📋 How It Works

### Process Flow:

```
1. User provides candidate_id
   ↓
2. Retrieve candidate info from mst_candidates
   ↓
3. Get resume file details from adm_attachments
   ↓
4. Download resume from TGApps file server
   (Fallback: use resume_content from mst_candidates)
   ↓
5. Retrieve Job Description from mst_requirements
   ↓
6. Parse resume using AI (existing logic from main.py)
   ↓
7. Retrieve additional data (emails, contacts from DB)
   ↓
8. Map parsed data to database schema
   ↓
9. Return structured JSON output
   ↓
10. Cleanup temporary files
```

### Example Usage:

```bash
python db_integration.py
```

**Input:**
```
Enter Candidate ID: 221522
```

**Output:**
```json
{
  "candidate_id": 221522,
  "company_id": 1,
  "full_name": "John Doe",
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  "date_of_birth": "1990-01-15",
  "emails": ["john.doe@example.com"],
  "contact_numbers": ["+1-555-1234"],
  "skills": [
    {
      "skill_name": "Python",
      "years_of_experience": "5"
    }
  ],
  "education": [...],
  "work_experience": [...],
  "resume_file": {...},
  "job_description": "...",
  "parsed_data": {...}
}
```

## 🔒 Database Credentials

**Current Configuration:**
```python
DB_CONFIG = {
    'host': '10.60.20.8',
    'user': 'root',
    'password': 'devdb@r00t',
    'database': 'tgapdb',
    'port': 3306
}
```

**File Server:**
```
Base URL: https://10.60.20.226/tgaprdv9/_lib/file/
Format: {base_url}{file_sub_directory}{file_name}
```

## ⚠️ Important Notes

1. **Read-Only Operations**
   - The module ONLY reads from the database
   - No INSERT, UPDATE, or DELETE operations are performed
   - Safe to test without affecting database integrity

2. **SSL Certificate**
   - SSL verification is disabled for the internal file server
   - This is necessary for self-signed certificates
   - Secure within your internal network

3. **Temporary Files**
   - Downloaded resumes are saved to temporary files
   - Automatically cleaned up after processing
   - No permanent files created on disk

4. **Error Handling**
   - Comprehensive error handling at every step
   - Fallback mechanisms (e.g., use resume_content if file download fails)
   - Detailed error messages logged to stderr

5. **Data Merging**
   - Parsed data is merged with existing database data
   - Example: Emails from both resume and database are combined
   - Duplicates are removed automatically

## 🎯 What You Can Do Now

### 1. Test the Database Integration

```bash
# Activate virtual environment
cd C:\Users\AshleyMathias\Documents\TGAPPS
.\venv\Scripts\activate

# Set OpenAI API Key (if not already set)
$env:OPENAI_API_KEY="your-openai-api-key"

# Run the database integration
python db_integration.py
```

### 2. Verify Database Connection

```python
from db_integration import create_db_connection, close_db_connection

conn = create_db_connection()
if conn:
    print("✅ Database connection successful!")
    close_db_connection(conn)
else:
    print("❌ Database connection failed!")
```

### 3. Process a Specific Candidate

```python
from db_integration import process_candidate_resume
import json

# Replace with actual candidate_id from your database
candidate_id = 221522

result = process_candidate_resume(candidate_id)

if result:
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 4. Batch Processing (Custom Script)

```python
from db_integration import process_candidate_resume
import json

# List of candidate IDs to process
candidate_ids = [221522, 221523, 221524]

results = []
for cid in candidate_ids:
    print(f"\nProcessing candidate: {cid}")
    result = process_candidate_resume(cid)
    if result:
        results.append(result)

# Save all results to file
with open('parsed_candidates.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Processed {len(results)} candidates")
```

## 📁 Project Structure

```
TGAPPS/
├── main.py                          # Core AI resume parser
├── db_integration.py                # Database integration module (NEW)
├── requirements.txt                 # Updated with DB dependencies
├── DB_INTEGRATION_README.md         # Database integration guide (NEW)
├── DATABASE_INTEGRATION_SUMMARY.md  # This file (NEW)
├── README.md                        # Main project documentation
├── document/
│   └── Candidate Tables Details (1).pdf  # Database schema reference
├── jds/                             # Job descriptions
│   ├── EUC_Delivery_lead.txt
│   ├── program_manager.txt
│   ├── sap_basis_lead.txt
│   └── ...
└── Resume/                          # Sample resumes
    ├── Resume5.pdf
    ├── resume9.pdf
    └── ...
```

## 🚀 Next Steps

You can now:

1. **Test with a real candidate_id** from your database
2. **Verify data retrieval** from all tables
3. **Check resume parsing** accuracy
4. **Review mapped data** structure
5. **Integrate with your application** workflow

### Testing Checklist:

- [ ] Database connection successful
- [ ] Candidate basic info retrieved
- [ ] Resume file downloaded (or resume_content used)
- [ ] Job description retrieved
- [ ] Resume parsed successfully
- [ ] Skills matched against JD
- [ ] Data mapped to schema correctly
- [ ] Output JSON format correct
- [ ] Temporary files cleaned up

## 🔧 Customization

### Change Database Credentials

Edit `db_integration.py`:
```python
DB_CONFIG = {
    'host': 'your-host',
    'user': 'your-user',
    'password': 'your-password',
    'database': 'your-database',
    'port': 3306
}
```

### Add Custom Fields

Modify the `mapped_data` dictionary in `process_candidate_resume()`:
```python
mapped_data = {
    # ... existing fields ...
    'custom_field': your_custom_value,
}
```

### Change File Server URL

Edit `download_resume_from_url()`:
```python
base_url = "https://your-server/path/"
```

## 📞 Support

If you encounter any issues:

1. **Check Database Connectivity**
   ```bash
   mysql -h 10.60.20.8 -u root -p tgapdb
   ```

2. **Verify OpenAI API Key**
   ```bash
   echo $OPENAI_API_KEY  # Linux/Mac
   echo %OPENAI_API_KEY%  # Windows CMD
   $env:OPENAI_API_KEY   # Windows PowerShell
   ```

3. **Check Error Logs**
   - All errors are logged to stderr
   - Look for ❌ symbols in output

4. **Test Individual Functions**
   ```python
   from db_integration import get_candidate_basic_info
   
   result = get_candidate_basic_info(221522)
   print(result)
   ```

## ✨ Summary

**What we've built:**
- Complete database integration for TGApps resume parser
- Support for DOC/DOCX files in addition to PDF
- Automated workflow: Database → AI Parser → Structured Output
- Read-only operations (safe for testing)
- Comprehensive error handling and logging
- Schema-mapped output ready for database insertion

**You're ready to:**
1. Process candidate resumes directly from your database
2. Parse PDF, DOCX, and DOC resume files
3. Match skills against job descriptions
4. Get structured, database-ready output

All without manually handling files or database queries! 🎉
