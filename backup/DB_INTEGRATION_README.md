# TGApps - AI Resume Parser (Database Integration)

## Overview

This module integrates the AI-powered resume parser with the TGApps MySQL database. It retrieves candidate resumes and job descriptions from the database, processes them using the AI parser, and maps the parsed data to the database schema.

## Features

- ✅ **Database Connection**: Connects to TGApps MySQL database securely
- ✅ **Candidate Retrieval**: Fetches candidate information by candidate_id
- ✅ **Resume Download**: Downloads resume files from TGApps file server
- ✅ **JD Retrieval**: Retrieves job descriptions for candidates
- ✅ **AI Parsing**: Processes resumes using OpenAI GPT-4.1-mini
- ✅ **Schema Mapping**: Maps parsed data to TGApps database schema
- ✅ **Read-Only**: No database updates, only reads data

## Database Configuration

```python
DB_CONFIG = {
    'host': '10.60.20.8',
    'user': 'root',
    'password': 'devdb@r00t',
    'database': 'tgapdb',
    'port': 3306
}
```

## Database Schema Reference

### Tables Used

#### 1. `mst_candidates`
Stores basic candidate information:
- `candidate_id` (Primary Key)
- `full_name` - Candidate name
- `linkedin_profile` - LinkedIn URL
- `resume_content` - Complete resume text
- `sex` - Gender
- `nationality` - Country
- `date_of_birth` - DOB
- `company_id` - Company reference

#### 2. `adm_attachments`
Stores all attachments (resumes, documents):
- `attachment_id` (Primary Key)
- `related_obj_pk` = `candidate_id`
- `related_obj_name` = `'Cnd'`
- `company_id` - Company reference
- `attachment_type` - Lookup type for 'Resume'
- `file_sub_directory` - Subdirectory path
- `file_name` - File name

**Resume URL Format:**
```
https://10.60.20.226/tgaprdv9/_lib/file/{file_sub_directory}{file_name}
```

#### 3. `mst_emails`
Stores email addresses:
- `email_address`
- `related_obj_pk` = `candidate_id`
- `related_obj_name` = `'Cnd'`
- `company_id` - Company reference

#### 4. `mst_contact_numbers`
Stores contact numbers:
- `contact_number`
- `related_obj_pk` = `candidate_id`
- `related_obj_name` = `'Cnd'`
- `company_id` - Company reference

#### 5. `adm_skillsets`
Stores candidate skills:
- `skill_name`, `years_of_experience`, etc.
- `related_obj_pk` = `candidate_id`
- `related_obj_name` = `'Cnd'`
- `company_id` - Company reference

#### 6. `adm_education`
Stores education details:
- `degree`, `institution`, `year`, etc.
- `related_obj_pk` = `candidate_id`
- `related_obj_name` = `'Cnd'`
- `company_id` - Company reference

#### 7. `mst_candidate_work_details`
Stores work experience:
- `candidate_id` - Reference to candidate
- `company_name`, `designation`, `from_date`, `to_date`, etc.

#### 8. `mst_requirements` and `adm_can_submissions`
Retrieve Job Description:
```sql
SELECT job_description FROM mst_requirements
WHERE req_id = (
    SELECT req_id FROM adm_can_submissions
    WHERE candidate_id = ?
)
```

## Installation

### Prerequisites
- Python 3.13+
- MySQL database access (TGApps)
- OpenAI API Key
- Network access to TGApps file server

### Dependencies
```bash
pip install -r requirements.txt
```

Key dependencies:
- `mysql-connector-python==9.5.0` - MySQL database connector
- `requests==2.32.5` - HTTP library for file downloads
- `urllib3==2.6.3` - HTTP client
- `openai==2.14.0` - OpenAI API
- `pdfplumber==0.11.9` - PDF parsing
- `python-docx==1.1.0` - DOCX parsing

### Environment Setup
```bash
# Set OpenAI API Key
export OPENAI_API_KEY="your-openai-api-key"

# Or on Windows
set OPENAI_API_KEY=your-openai-api-key
```

## Usage

### Command Line Interface

```bash
python db_integration.py
```

You will be prompted to enter a candidate ID:

```
============================================================
TGApps - AI Resume Parser (Database Integration)
============================================================

Enter Candidate ID: 221522
```

### Python Script

```python
from db_integration import process_candidate_resume
import json

# Process candidate by ID
candidate_id = 221522
result = process_candidate_resume(candidate_id)

if result:
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

## Output Format

The parsed data is returned in the following format:

```json
{
  "candidate_id": 221522,
  "company_id": 1,
  
  "full_name": "John Doe",
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  "sex": "Male",
  "nationality": "USA",
  "date_of_birth": "1990-01-15",
  
  "emails": [
    "john.doe@example.com",
    "johndoe@gmail.com"
  ],
  
  "contact_numbers": [
    "+1-555-1234",
    "+1-555-5678"
  ],
  
  "skills": [
    {
      "skill_name": "Python",
      "years_of_experience": "5"
    },
    {
      "skill_name": "AWS",
      "years_of_experience": "3"
    }
  ],
  
  "education": [
    {
      "degree": "Master's in Computer Science",
      "institution": "MIT",
      "year": "2015",
      "is_highest_degree": true
    }
  ],
  
  "work_experience": [
    {
      "company_name": "Tech Corp",
      "designation": "Senior Software Engineer",
      "from_date": "2018-01",
      "to_date": "Present",
      "projects": ["Project A", "Project B"],
      "total_compensation": "$150,000"
    }
  ],
  
  "resume_file": {
    "attachment_id": 12345,
    "file_name": "johndoe_resume.pdf",
    "file_sub_directory": "candidates/2024/01/"
  },
  
  "job_description": "Full text of job description...",
  
  "parsed_data": {
    // Full parsed data from AI
  }
}
```

## Functions Reference

### Database Connection

#### `create_db_connection() -> connection | None`
Creates a connection to the MySQL database.

**Returns:** MySQL connection object or None if failed

#### `close_db_connection(connection)`
Closes the database connection.

### Data Retrieval

#### `get_candidate_basic_info(candidate_id) -> dict | None`
Retrieves basic candidate information from `mst_candidates` table.

**Parameters:**
- `candidate_id` (int): Candidate ID

**Returns:** Dictionary with candidate basic info or None

#### `get_resume_file_details(candidate_id, company_id) -> dict | None`
Retrieves resume file details from `adm_attachments` table.

**Parameters:**
- `candidate_id` (int): Candidate ID
- `company_id` (int): Company ID

**Returns:** Dictionary with file details (file_sub_directory, file_name, attachment_id) or None

#### `download_resume_from_url(file_sub_directory, file_name) -> str | None`
Downloads resume file from TGApps file server.

**Parameters:**
- `file_sub_directory` (str): Subdirectory path
- `file_name` (str): File name

**Returns:** Path to downloaded temp file or None

#### `get_candidate_emails(candidate_id, company_id) -> list`
Retrieves candidate email addresses from `mst_emails` table.

**Parameters:**
- `candidate_id` (int): Candidate ID
- `company_id` (int): Company ID

**Returns:** List of email addresses

#### `get_candidate_contact_numbers(candidate_id, company_id) -> list`
Retrieves candidate contact numbers from `mst_contact_numbers` table.

**Parameters:**
- `candidate_id` (int): Candidate ID
- `company_id` (int): Company ID

**Returns:** List of contact numbers

#### `get_job_description(candidate_id) -> str | None`
Retrieves Job Description from `mst_requirements` table.

**Parameters:**
- `candidate_id` (int): Candidate ID

**Returns:** Job description text or None

### Main Processing

#### `process_candidate_resume(candidate_id) -> dict | None`
Main function to retrieve, parse, and map candidate data.

**Parameters:**
- `candidate_id` (int): Candidate ID

**Returns:** Dictionary with parsed data mapped to database schema

**Process Flow:**
1. Retrieve candidate basic information
2. Retrieve resume file details
3. Download resume file (or use resume_content from DB)
4. Retrieve Job Description
5. Parse resume using AI
6. Retrieve additional data (emails, contacts)
7. Map parsed data to database schema
8. Cleanup temporary files

## Error Handling

The module includes comprehensive error handling:

- **Database Errors**: Connection failures, query errors
- **File Download Errors**: Network issues, file not found
- **Parsing Errors**: Invalid file formats, API errors
- **Data Validation**: Missing required fields

All errors are logged to stderr with descriptive messages.

## Logging

The module logs all operations to stderr:

- ✅ Success messages (green)
- ⚠️ Warning messages (yellow)
- ❌ Error messages (red)
- 📋 📄 📥 📝 🤖 📊 🗺️ 🗑️ Progress indicators

Example:
```
============================================================
Processing Candidate ID: 221522
============================================================

📋 Step 1: Retrieving candidate basic information...
✅ Successfully connected to MySQL Server version 8.0.x
✅ Retrieved candidate: John Doe

📄 Step 2: Retrieving resume file details...
✅ Resume file found: johndoe_resume.pdf

📥 Step 3: Downloading resume file...
📥 Downloading resume from: https://10.60.20.226/tgaprdv9/_lib/file/...
✅ Resume downloaded to: /tmp/tmpxyz123.pdf

📝 Step 4: Retrieving Job Description...
✅ Retrieved Job Description (2500 characters)

🤖 Step 5: Parsing resume with AI...
...

✅ Processing Complete!
```

## Security Considerations

- **SSL Verification**: Disabled for internal TGApps server (self-signed certificates)
- **Database Credentials**: Hard-coded in module (update in production)
- **Read-Only**: No database updates to prevent accidental data modification
- **Temporary Files**: Automatically cleaned up after processing

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to database
```
❌ Error connecting to MySQL: Access denied
```

**Solution:** Verify database credentials and network access

### Resume Download Fails

**Problem:** Cannot download resume file
```
❌ Error downloading resume: Connection timeout
```

**Solution:** 
1. Check network connectivity to file server
2. Verify file_sub_directory and file_name are correct
3. Fallback to `resume_content` from database

### No Job Description Found

**Problem:** JD not found for candidate
```
⚠️ No Job Description found for candidate_id: 221522
```

**Solution:** This is a warning, not an error. The parser will proceed without JD filtering.

### OpenAI API Errors

**Problem:** API rate limit or authentication issues
```
❌ OpenAI API error: Rate limit exceeded
```

**Solution:**
1. Check OPENAI_API_KEY environment variable
2. Wait and retry if rate limited
3. Verify API quota

## Future Enhancements

- [ ] Support for bulk processing (multiple candidate IDs)
- [ ] Write parsed data back to database (INSERT/UPDATE)
- [ ] Support for different attachment types
- [ ] Caching mechanism for frequently accessed data
- [ ] Async processing for better performance
- [ ] Web API endpoint for integration

## Testing

To test the integration:

1. Use a known candidate ID from the database
2. Verify all data retrieval steps complete successfully
3. Check parsed output matches expected format
4. Validate data mapping to database schema

```bash
# Test with a sample candidate
python db_integration.py
# Enter candidate ID: 221522
```

## License

This module is part of the TGAPPS-AI project.

## Support

For issues or questions:
1. Check error logs in stderr
2. Verify database connectivity
3. Test with a simple candidate ID first
4. Review the database schema documentation
