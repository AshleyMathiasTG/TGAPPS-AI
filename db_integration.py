import mysql.connector
from mysql.connector import Error
import os
import sys
import tempfile
import requests
from urllib.parse import quote
from dotenv import load_dotenv
from main import parse_resume

# Load environment variables from .env file
load_dotenv()

# -------------------------
# DATABASE CONFIGURATION
# -------------------------

def get_db_config():
    """
    Get database configuration from environment variables.
    
    Returns:
        dict: Database configuration dictionary
    
    Raises:
        ValueError: If required environment variables are missing
    """
    config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT', 3306))
    }
    
    # Validate required fields
    required_fields = ['host', 'user', 'password', 'database']
    missing_fields = [field for field in required_fields if not config[field]]
    
    if missing_fields:
        raise ValueError(
            f"Missing required database environment variables: {', '.join(missing_fields)}. "
            f"Please set DB_HOST, DB_USER, DB_PASSWORD, and DB_NAME in your .env file."
        )
    
    return config

# -------------------------
# DATABASE CONNECTION
# -------------------------

def create_db_connection():
    """
    Create a connection to the MySQL database.
    
    Returns:
        connection: MySQL connection object or None if failed
    """
    try:
        db_config = get_db_config()
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"[SUCCESS] Successfully connected to MySQL Server version {db_info}", file=sys.stderr)
            return connection
    except Error as e:
        print(f"[ERROR] Error connecting to MySQL: {e}", file=sys.stderr)
        return None

def close_db_connection(connection):
    """Close the database connection."""
    if connection and connection.is_connected():
        connection.close()
        print("[SUCCESS] Database connection closed", file=sys.stderr)

# -------------------------
# RETRIEVE CANDIDATE DATA
# -------------------------

def get_candidate_basic_info(candidate_id):
    """
    Retrieve basic candidate information from mst_candidates table.
    
    Args:
        candidate_id: Candidate ID
    
    Returns:
        dict: Candidate basic info or None if not found
    """
    connection = create_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT candidate_id, full_name, linkedin_profile, resume_content, 
                   sex, nationality, date_of_birth, company_id
            FROM mst_candidates
            WHERE candidate_id = %s
        """
        cursor.execute(query, (candidate_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print(f"[SUCCESS] Retrieved candidate: {result.get('full_name')}", file=sys.stderr)
        else:
            print(f"[ERROR] No candidate found with ID: {candidate_id}", file=sys.stderr)
        
        return result
    
    except Error as e:
        print(f"[ERROR] Error retrieving candidate info: {e}", file=sys.stderr)
        return None
    finally:
        close_db_connection(connection)

def get_resume_file_details(candidate_id, company_id):
    """
    Retrieve resume file details from adm_attachments table.
    
    Query structure:
    SELECT file_sub_directory, file_name FROM adm_attachments
    WHERE related_obj_pk = candidate_id
      AND related_obj_name = 'Cnd'
      AND attachment_type = (SELECT lookup_code_id FROM adm_lookup_codes 
                            WHERE lookup_code = 'Resume' AND company_id = company_id)
    
    Args:
        candidate_id: Candidate ID
        company_id: Company ID
    
    Returns:
        dict: Resume file details (file_sub_directory, file_name, attachment_id) or None
    """
    connection = create_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get resume file details using subquery for attachment_type
        # Query matches specification: SELECT file_sub_directory, file_name FROM adm_attachments
        # WHERE related_obj_pk = candidate_id AND related_obj_name = 'Cnd'
        # AND attachment_type = (SELECT lookup_code_id FROM adm_lookup_codes 
        #                        WHERE lookup_code = 'Resume' AND company_id = company_id)
        attachment_query = """
            SELECT attachment_id, file_sub_directory, file_name 
            FROM adm_attachments 
            WHERE related_obj_pk = %s 
              AND related_obj_name = 'Cnd' 
              AND attachment_type = (
                  SELECT lookup_code_id 
                  FROM adm_lookup_codes 
                  WHERE lookup_code = 'Resume' 
                    AND company_id = %s
              )
            LIMIT 1
        """
        cursor.execute(attachment_query, (candidate_id, company_id))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print(f"[SUCCESS] Resume file found: {result.get('file_name')}", file=sys.stderr)
        else:
            print(f"[ERROR] No resume file found for candidate_id: {candidate_id}", file=sys.stderr)
        
        return result
    
    except Error as e:
        print(f"[ERROR] Error retrieving resume file: {e}", file=sys.stderr)
        return None
    finally:
        close_db_connection(connection)

def download_resume_from_url(file_sub_directory, file_name):
    """
    Download resume file from the TGApps file server.
    
    URL Structure: {FILE_SERVER_BASE_URL}{file_sub_directory}/{url_encoded_file_name}
    Base URL: https://10.60.20.226/tgaprdv9/_lib/file/doc
    Example: https://10.60.20.226/tgaprdv9/_lib/file/doc_TGU_Resume/Mathew%20Shember_Automation%20Windows%20.pdf
    
    Args:
        file_sub_directory: Subdirectory path from database (e.g., "_TGU_Resume")
        file_name: File name from database (e.g., "Mathew Shember_Automation Windows .pdf")
    
    Returns:
        str: Path to downloaded file or None if failed
    
    Raises:
        ValueError: If FILE_SERVER_BASE_URL environment variable is not set
    """
    base_url = os.getenv('FILE_SERVER_BASE_URL')
    if not base_url:
        raise ValueError(
            "FILE_SERVER_BASE_URL environment variable is not set. "
            "Please set it in your .env file."
        )
    
    # URL encode the filename (spaces become %20, etc.)
    # Only encode the filename, not the subdirectory path
    encoded_file_name = quote(file_name, safe='')
    
    # Normalize file_sub_directory: remove "doc" prefix if present
    # (since base_url already ends with "doc")
    file_sub_directory = file_sub_directory.rstrip('/')
    if file_sub_directory.startswith('doc_'):
        # Remove "doc" but keep the underscore
        file_sub_directory = '_' + file_sub_directory[4:]
    elif file_sub_directory.startswith('doc'):
        # Handle case where it starts with "doc" but no underscore
        file_sub_directory = file_sub_directory[3:]
    
    # Construct the full URL: base_url + file_sub_directory + '/' + encoded_filename
    file_url = f"{base_url}{file_sub_directory}/{encoded_file_name}"
    
    try:
        print(f"[INFO] Downloading resume from: {file_url}", file=sys.stderr)
        
        # Download file (disable SSL verification for internal server)
        response = requests.get(file_url, verify=False, timeout=30)
        response.raise_for_status()
        
        # Save to temporary file
        file_extension = os.path.splitext(file_name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        print(f"[SUCCESS] Resume downloaded to: {temp_path}", file=sys.stderr)
        return temp_path
    
    except requests.RequestException as e:
        print(f"[ERROR] Error downloading resume: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERROR] Error saving resume: {e}", file=sys.stderr)
        return None

def get_candidate_emails(candidate_id, company_id):
    """
    Retrieve candidate email addresses from mst_emails table.
    
    Args:
        candidate_id: Candidate ID
        company_id: Company ID
    
    Returns:
        list: List of email addresses
    """
    connection = create_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT * 
            FROM mst_emails 
            WHERE related_obj_pk = %s 
              AND related_obj_name = 'Cnd' 
              AND company_id = %s
        """
        cursor.execute(query, (candidate_id, company_id))
        results = cursor.fetchall()
        cursor.close()
        
        # Try to extract email from different possible column names
        emails = []
        for row in results:
            email_value = row.get('email') or row.get('email_address') or row.get('email_id')
            if email_value:
                emails.append(email_value)
        
        print(f"[SUCCESS] Retrieved {len(emails)} email(s)", file=sys.stderr)
        return emails
    
    except Error as e:
        print(f"[WARNING] Could not retrieve emails: {e}", file=sys.stderr)
        return []
    finally:
        close_db_connection(connection)

def get_candidate_contact_numbers(candidate_id, company_id):
    """
    Retrieve candidate contact numbers from mst_contact_numbers table.
    
    Args:
        candidate_id: Candidate ID
        company_id: Company ID
    
    Returns:
        list: List of contact numbers
    """
    connection = create_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor()
        query = """
            SELECT contact_number 
            FROM mst_contact_numbers 
            WHERE related_obj_pk = %s 
              AND related_obj_name = 'Cnd' 
              AND company_id = %s
        """
        cursor.execute(query, (candidate_id, company_id))
        results = cursor.fetchall()
        cursor.close()
        
        contacts = [row[0] for row in results if row[0]]
        print(f"[SUCCESS] Retrieved {len(contacts)} contact number(s)", file=sys.stderr)
        return contacts
    
    except Error as e:
        print(f"[ERROR] Error retrieving contact numbers: {e}", file=sys.stderr)
        return []
    finally:
        close_db_connection(connection)

def get_job_description(candidate_id):
    """
    Retrieve Job Description for the candidate from mst_requirements table.
    
    Args:
        candidate_id: Candidate ID
    
    Returns:
        str: Job description text or None
    """
    connection = create_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        query = """
            SELECT job_description 
            FROM mst_requirements 
            WHERE req_id = (
                SELECT req_id 
                FROM adm_can_submissions 
                WHERE candidate_id = %s
                LIMIT 1
            )
        """
        cursor.execute(query, (candidate_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0]:
            jd_text = result[0]
            print(f"[SUCCESS] Retrieved Job Description ({len(jd_text)} characters)", file=sys.stderr)
            return jd_text
        else:
            print(f"[WARNING] No Job Description found for candidate_id: {candidate_id}", file=sys.stderr)
            return None
    
    except Error as e:
        print(f"[ERROR] Error retrieving Job Description: {e}", file=sys.stderr)
        return None
    finally:
        close_db_connection(connection)

# -------------------------
# MAIN PROCESSING FUNCTION
# -------------------------

def process_candidate_resume(candidate_id):
    """
    Main function to retrieve candidate data from database, parse resume, and map to schema.
    
    Args:
        candidate_id: Candidate ID
    
    Returns:
        dict: Parsed resume data mapped to database schema
    """
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Processing Candidate ID: {candidate_id}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # Step 1: Get basic candidate info
    print("Step 1: Retrieving candidate basic information...", file=sys.stderr)
    candidate_info = get_candidate_basic_info(candidate_id)
    if not candidate_info:
        print("[ERROR] Failed to retrieve candidate information. Exiting.", file=sys.stderr)
        return None
    
    company_id = candidate_info['company_id']
    
    # Step 2: Check if resume is available
    print("\nStep 2: Checking resume availability...", file=sys.stderr)
    
    # First check if resume_content exists in database
    has_resume_content = bool(candidate_info.get('resume_content') and candidate_info.get('resume_content').strip())
    
    # Then check if resume file exists
    resume_file_info = get_resume_file_details(candidate_id, company_id)
    
    # If NEITHER exists, stop early with clear message
    if not resume_file_info and not has_resume_content:
        print("\n" + "="*60, file=sys.stderr)
        print("[ERROR] RESUME NOT FOUND", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"\nCandidate ID: {candidate_id}", file=sys.stderr)
        print(f"Candidate Name: {candidate_info.get('full_name')}", file=sys.stderr)
        print("\n[WARNING] No resume available for this candidate:", file=sys.stderr)
        print("   • No resume file in file server (adm_attachments)", file=sys.stderr)
        print("   • No resume_content in database (mst_candidates)", file=sys.stderr)
        print("\n[INFO] Action Required:", file=sys.stderr)
        print("   1. Upload resume file to TGApps file server, OR", file=sys.stderr)
        print("   2. Add resume content to mst_candidates.resume_content", file=sys.stderr)
        print("\n" + "="*60 + "\n", file=sys.stderr)
        return None
    
    # Step 3: Try to get resume file from file server
    resume_path = None
    if resume_file_info:
        print("\nStep 3: Downloading resume from file server...", file=sys.stderr)
        resume_path = download_resume_from_url(
            resume_file_info['file_sub_directory'],
            resume_file_info['file_name']
        )
        if resume_path:
            print(f"[SUCCESS] Resume file downloaded successfully", file=sys.stderr)
    
    # Step 4: Fallback to resume_content if file download failed
    if not resume_path and has_resume_content:
        print("\n[WARNING] Resume file not available. Using resume_content from database...", file=sys.stderr)
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
                temp_file.write(candidate_info['resume_content'])
                resume_path = temp_file.name
            print(f"[SUCCESS] Resume content loaded from database", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to save resume_content to temp file: {e}", file=sys.stderr)
            return None
    
    # Step 5: Get Job Description
    print("\nStep 5: Retrieving Job Description...", file=sys.stderr)
    jd_text = get_job_description(candidate_id)
    
    # Save JD to temporary file if available
    jd_path = None
    if jd_text:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(jd_text)
            jd_path = temp_file.name
        print(f"[SUCCESS] JD saved to temporary file: {jd_path}", file=sys.stderr)
    
    # Step 6: Parse resume using existing parser
    print("\nStep 6: Parsing resume with AI...", file=sys.stderr)
    try:
        parsed_data = parse_resume(resume_path, jd_path)
    except Exception as e:
        print(f"[ERROR] Error parsing resume: {e}", file=sys.stderr)
        # Cleanup temp files
        if resume_path and os.path.exists(resume_path):
            os.unlink(resume_path)
        if jd_path and os.path.exists(jd_path):
            os.unlink(jd_path)
        return None
    
    # Step 7: Map parsed data to database schema
    print("\nStep 7: Mapping parsed data to database schema...", file=sys.stderr)
    mapped_data = {
        'candidate_id': candidate_id,
        'company_id': company_id,
        
        # From mst_candidates table
        'full_name': candidate_info.get('full_name') or parsed_data.get('name', ''),
        'linkedin_profile': parsed_data.get('linkedin_url') or candidate_info.get('linkedin_profile'),
        'sex': candidate_info.get('sex'),
        'nationality': candidate_info.get('nationality'),
        'date_of_birth': parsed_data.get('date_of_birth') or candidate_info.get('date_of_birth'),
        
        # From resume parsing only
        'emails': parsed_data.get('emails', []),
        'contact_numbers': parsed_data.get('contact_numbers', []),
        'addresses': parsed_data.get('addresses', []),
        
        # From adm_skillsets table
        'skills': parsed_data.get('skills', []),
        
        # From adm_education table
        'education': parsed_data.get('education', []),
        
        # From mst_candidate_work_details table
        'work_experience': parsed_data.get('experience', []),
        
        # From adm_attachments table
        'resume_file': {
            'attachment_id': resume_file_info.get('attachment_id') if resume_file_info else None,
            'file_name': resume_file_info.get('file_name') if resume_file_info else None,
            'file_sub_directory': resume_file_info.get('file_sub_directory') if resume_file_info else None
        } if resume_file_info else None,
        
        # Job Description
        'job_description': jd_text,
        
        # Full parsed data (for reference)
        'parsed_data': parsed_data
    }
    
    # Cleanup temporary files
    if resume_path and os.path.exists(resume_path):
        os.unlink(resume_path)
        print(f"[INFO] Cleaned up temporary resume file", file=sys.stderr)
    
    if jd_path and os.path.exists(jd_path):
        os.unlink(jd_path)
        print(f"[INFO] Cleaned up temporary JD file", file=sys.stderr)
    
    print("\n" + "="*60, file=sys.stderr)
    print("[SUCCESS] Processing Complete!", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)
    
    return mapped_data

# -------------------------
# CLI INTERFACE
# -------------------------

if __name__ == "__main__":
    import json
    
    # Suppress SSL warnings for internal server
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("\n" + "="*60)
    print("TGApps - AI Resume Parser (Database Integration)")
    print("="*60 + "\n")
    
    # Get candidate_id from user
    candidate_id_input = input("Enter Candidate ID: ").strip()
    
    if not candidate_id_input:
        print("[ERROR] Candidate ID is required. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    try:
        candidate_id = int(candidate_id_input)
    except ValueError:
        print("[ERROR] Invalid Candidate ID. Must be a number.", file=sys.stderr)
        sys.exit(1)
    
    # Process candidate resume
    result = process_candidate_resume(candidate_id)
    
    if result:
        # Output result as JSON
        print("\n" + "="*60)
        print("PARSED DATA (JSON)")
        print("="*60 + "\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n[ERROR] Failed to process candidate resume.", file=sys.stderr)
        sys.exit(1)
