import os
import re
import json
import sys
import pdfplumber
from openai import OpenAI, OpenAIError, APIError, RateLimitError, APIConnectionError

# -------------------------
# OPENAI CLIENT (SINGLETON)
# -------------------------

_openai_client = None

def get_openai_client():
    """Get or create a singleton OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

# -------------------------
# REGEX EXTRACTORS
# -------------------------

def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def extract_phone_numbers(text):
    pattern = r"(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){8,9}\d"
    matches = re.findall(pattern, text)
    return list(set(m.strip() for m in matches))

def extract_linkedin(text):
    matches = re.findall(r"(https?://(?:www\.)?linkedin\.com/[^\s]+)", text)
    return matches[0] if matches else None

def extract_dob(text):
    match = re.search(r"(DOB|Date of Birth)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.IGNORECASE)
    return match.group(2) if match else None

# -------------------------
# PDF TEXT EXTRACTION
# -------------------------

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with error handling."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                raise ValueError(f"PDF file '{pdf_path}' has no pages")
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF '{pdf_path}': {str(e)}")

# -------------------------
# LLM STRUCTURED EXTRACTION
# -------------------------

def extract_structured_fields(text):
    """Extract structured fields from resume text using LLM with error handling."""
    if not text or not text.strip():
        raise ValueError("Resume text is empty")
    
    try:
        client = get_openai_client()
    except ValueError as e:
        raise ValueError(f"OpenAI client initialization failed: {str(e)}")

    system_prompt = """
You are a STRICT ATS resume parser.

Your task is to extract structured data ONLY from the provided resume text.

STRICT RULES (Must Follow):
1. Extract ONLY information that is explicitly and clearly present in the resume.
2. DO NOT guess, infer, assume, normalize, or fabricate any values under any circumstances.
3. Return only fields and structure matching the defined schema exactly.
4. If a value is not available, return an empty string ("") or empty list ([]) as appropriate.
5. NEVER include duplicated entries or repeated sections.
6. DO NOT include any additional text, explanations, formatting, or comments—ONLY return valid JSON.

SECTION RULES:

EDUCATION:
- Extract all education entries explicitly stated.
- Fields include: degree, subject, year_passed (as written), result, college_university, percentage.
- Identify the highest degree based on title only and set `is_highest` to true for that one.
- Use date formats exactly as written—if a single year, return that; if a range (e.g., "2020–2022"), return the full range string.
- Do NOT split or infer missing start/end years.
- Do NOT reformat dates or ranges.
- Leave year_passed empty if no date is mentioned.

EXPERIENCE:
- Parse all clearly written job entries in reverse chronological order (most recent first).
- Fields include: organization, job_title, location, start_date, end_date.
- Use "Present" only if explicitly written.
- Each experience must contain a list of projects, if project descriptions are present in that job entry.
- If multiple roles at the same company exist, treat them as separate entries.
- DO NOT guess project names—use only if named. Project details must be tied directly to the job.
- Leave `last_pay_rate`, `pay_uom`, `last_hike_date` empty if not clearly mentioned.

SKILLS:
- Extract every clearly mentioned skill or tool as a distinct entry.
- DO NOT group unrelated tools or platforms under a single skill name.
- Use `skillset_type` only if explicitly given (e.g., "Technical", "Soft Skills").
- Leave `years` and `last_used` blank unless those values are directly mentioned with the skill.

ADDRESSES:
- Extract any explicit addresses, locations, or place names mentioned as standalone or within education/experience.
- Each address must be treated as an independent entry under `"addresses"`.
- DO NOT infer timelines—set `start_date_active` and `end_date_active` as empty.
- Example: If "Mumbai, India" or "Bangalore, Karnataka 560001" is mentioned, treat it as an address.

CONTACT DETAILS:
- Extract `emails`, `contact_numbers`, `linkedin_url`, and `date_of_birth` ONLY if they are clearly visible.
- For phone numbers, avoid extracting date ranges that resemble numbers (e.g., "2020–2022").
- For LinkedIn, match only correct LinkedIn URLs.

DUPLICATE HANDLING:
- Avoid repeating any skill, project, experience, or education entry more than once.
- Skills with minor case or punctuation variations must be considered the same.

JSON OUTPUT FORMAT:
Return a single valid JSON object matching EXACTLY this schema:

{
  "emails": [],
  "contact_numbers": [],
  "linkedin_url": null,
  "date_of_birth": null,
  "education": [
    {
      "degree": "",
      "subject": "",
      "year_passed": "",
      "result": "",
      "college_university": "",
      "percentage": "",
      "is_highest": false
    }
  ],
  "experience": [
    {
      "organization": "",
      "job_title": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "last_pay_rate": "",
      "pay_uom": "",
      "last_hike_date": "",
      "projects": [
        {
          "project_name": "",
          "project_details": ""
        }
      ]
    }
  ],
  "skills": [
    {
      "skillset_type": "",
      "skill_name": "",
      "years": "",
      "last_used": ""
    }
  ],
  "addresses": [
    {
      "address": "",
      "start_date_active": "",
      "end_date_active": ""
    }
  ]
}

ONLY return this JSON structure and nothing else.

"""

    user_prompt = f"Resume Text:\n{text}"

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI API")
        
        return json.loads(content)
        
    except RateLimitError:
        raise RuntimeError("OpenAI API rate limit exceeded. Please try again later.")
    except APIConnectionError as e:
        raise RuntimeError(f"Failed to connect to OpenAI API: {str(e)}")
    except APIError as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse LLM response as JSON: {str(e)}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response structure from OpenAI: {str(e)}")
    except OpenAIError as e:
        raise RuntimeError(f"OpenAI error: {str(e)}")

# -------------------------
# JD-BASED SKILL FILTERING
# -------------------------

def read_jd_file(jd_path):
    """Read Job Description from a text file with error handling."""
    if not jd_path:
        return ""
    
    if not os.path.exists(jd_path):
        print(f"Warning: JD file not found: {jd_path}. Skipping skill filtering.", file=sys.stderr)
        return ""
    
    try:
        with open(jd_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"Warning: JD file is empty: {jd_path}. Skipping skill filtering.", file=sys.stderr)
            return content
    except UnicodeDecodeError as e:
        print(f"Warning: Failed to read JD file (encoding issue): {jd_path}. {str(e)}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Warning: Failed to read JD file: {jd_path}. {str(e)}", file=sys.stderr)
        return ""

def extract_jd_skills(jd_text):
    """
    Extract skills explicitly mentioned in the Job Description.
    Returns a list of skill names that are explicitly written in the JD.
    """
    if not jd_text:
        return []
    
    try:
        client = get_openai_client()
    except ValueError as e:
        print(f"Warning: JD skill extraction skipped - {str(e)}", file=sys.stderr)
        return []
    
    extract_prompt = """
You are an intelligent skill extraction system for Job Descriptions that handles multiple JD formats.

TASK: Extract ALL skills that are EXPLICITLY mentioned in the Job Description, regardless of format.

JD FORMATS TO HANDLE:
1. STRUCTURED SECTIONS: Look for sections like:
   - "Technology Scope", "Required Skills", "Technical Skills", "Qualifications & Skills"
   - "Key Responsibilities" (may contain embedded skills)
   - "Requirements", "Preferred Qualifications", "Experience"
   - Any section header that suggests skills/technologies

2. EXPLICIT LISTS: Extract from bullet points, numbered lists, or comma-separated lists
   Example: "VDI: VMware Horizon VDI, Azure Virtual Desktop (AVD)" → Extract both

3. NARRATIVE TEXT: Extract skills embedded in sentences
   Example: "Strong expertise in VDI, Endpoint Management, and Endpoint Security" → Extract all three

4. TABLE FORMATS: Extract from structured tables with skill columns

SKILL CATEGORIES TO EXTRACT:
- Technologies, tools, platforms (e.g., VMware, SAP, Python, AWS, Oracle, JIRA, Confluence)
- Software and systems (e.g., SAP ECC, S/4HANA, Salesforce, MES)
- Methodologies and frameworks (e.g., Agile, Scrum, DevOps, ITIL)
- Governance and compliance (e.g., SOX Compliance, ITGC, Risk Management)
- Infrastructure and security (e.g., Active Directory, SCCM, Intune, VDI, HANA)
- Process and management skills (e.g., Project Management, Vendor Management, Process Improvements)
- Certifications (e.g., SAP Certified, ITIL certification, Atlassian certifications)
- Cloud platforms (e.g., Azure, AWS, GCP, SAP BTP)
- Integration technologies (e.g., SAP PO/PI, Solution Manager, GRC)

EXTRACTION RULES:
1. Extract skills from ALL relevant sections:
   - Technology/Technical sections (explicit lists)
   - Required Skills/Qualifications sections
   - Key Responsibilities (if skills are mentioned)
   - Preferred Qualifications
   - Experience requirements (if specific technologies mentioned)

2. Handle different presentation styles:
   - "VDI: VMware Horizon VDI, Azure Virtual Desktop" → Extract: ["VMware Horizon VDI", "Azure Virtual Desktop", "AVD", "VDI"]
   - "SAP ECC, S/4HANA, BW, PO/PI" → Extract: ["SAP ECC", "S/4HANA", "BW", "PO/PI", "SAP"]
   - "Jira and Confluence" → Extract: ["Jira", "Confluence"]
   - "Strong experience with SAP HANA" → Extract: ["SAP HANA", "HANA"]

3. Extract both full names and common abbreviations:
   - "Microsoft SCCM" → Extract: ["Microsoft SCCM", "SCCM"]
   - "SAP S/4HANA" → Extract: ["SAP S/4HANA", "S/4HANA"]
   - "Azure Virtual Desktop (AVD)" → Extract: ["Azure Virtual Desktop", "AVD"]

4. Extract from narrative descriptions:
   - "Experience in SAP integrations and BTP set up" → Extract: ["SAP", "SAP BTP", "BTP"]
   - "Configure SAP FI (GL, AP, AR, AA, Bank Accounting)" → Extract: ["SAP FI", "SAP GL", "SAP AP", "SAP AR", "SAP AA", "Bank Accounting"]

5. DO NOT infer or assume:
   - "daily stand-ups" → Do NOT extract "Agile" or "Scrum" (not explicitly mentioned)
   - "customer-facing" → Do NOT extract "Communication" (too generic, not a skill)
   - Only extract if the skill name is clearly stated

6. Handle certifications:
   - "SAP Certified Technology Associate" → Extract: ["SAP Certified", "SAP Certification"]
   - "ITIL certification preferred" → Extract: ["ITIL"]
   - "Atlassian certifications (Jira/Confluence Administrator)" → Extract: ["Jira", "Confluence", "Atlassian"]

EXAMPLES FROM DIFFERENT FORMATS:

Example 1 - Structured Section:
JD: "Technology Scope (Must Have)
VDI: VMware Horizon VDI, Azure Virtual Desktop (AVD)
Endpoint Management: Microsoft SCCM, Microsoft Intune"
Extract: ["VMware Horizon VDI", "Azure Virtual Desktop", "AVD", "VDI", "Microsoft SCCM", "SCCM", "Microsoft Intune", "Intune", "Endpoint Management"]

Example 2 - Narrative Text:
JD: "Strong expertise in VDI, Endpoint Management, and Endpoint Security"
Extract: ["VDI", "Endpoint Management", "Endpoint Security"]

Example 3 - Requirements Section:
JD: "Technical Skills:
• Proficiency in Jira and Confluence administration
• Experience with ITSM tools"
Extract: ["Jira", "Confluence", "ITSM"]

Example 4 - Embedded in Responsibilities:
JD: "Manage end-to-end SAP BASIS operations across SAP ECC, S/4HANA, BW, PO/PI"
Extract: ["SAP BASIS", "SAP ECC", "S/4HANA", "BW", "PO/PI", "SAP"]

Return ONLY a JSON array of skill names (normalized to lowercase), nothing else.
Example: ["vmware horizon vdi", "microsoft sccm", "jira", "sap ecc", "s/4hana"]
"""
    
    user_prompt = f"""Job Description:
{jd_text}

INSTRUCTIONS:
1. Read through the ENTIRE Job Description carefully
2. Identify ALL sections that mention skills, technologies, tools, or competencies:
   - Look for section headers like "Technology Scope", "Required Skills", "Technical Skills", "Qualifications", "Requirements"
   - Check "Key Responsibilities" for embedded skill mentions
   - Review "Preferred Qualifications" and "Experience" sections
3. Extract skills from:
   - Explicit lists (bullet points, comma-separated, colon-separated)
   - Narrative text (e.g., "Strong experience with X, Y, and Z")
   - Table formats if present
4. Extract both full names and abbreviations when both are mentioned
5. Return all extracted skills as a JSON array (lowercase)

Extract all explicitly mentioned skills as a JSON array."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": extract_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        if not content:
            print("Warning: Empty response from JD skill extraction API.", file=sys.stderr)
            return []
        
        jd_skills = json.loads(content)
        
        if not isinstance(jd_skills, list):
            print("Warning: Invalid JD skill extraction response format.", file=sys.stderr)
            return []
        
        # Normalize to lowercase for comparison
        jd_skills_normalized = [skill.lower().strip() for skill in jd_skills if skill]
        print(f"Extracted {len(jd_skills_normalized)} skills from JD", file=sys.stderr)
        
        return jd_skills_normalized
        
    except RateLimitError:
        print("Warning: OpenAI API rate limit exceeded during JD skill extraction.", file=sys.stderr)
        return []
    except (APIConnectionError, APIError, OpenAIError) as e:
        print(f"Warning: OpenAI API error during JD skill extraction: {str(e)}.", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JD skill extraction response: {str(e)}.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Unexpected error during JD skill extraction: {str(e)}.", file=sys.stderr)
        return []


def match_resume_skills_with_jd(resume_skill_names, jd_skills):
    """
    Match resume skills against extracted JD skills.
    Returns a list of resume skill names that match JD skills.
    """
    if not resume_skill_names or not jd_skills:
        return []
    
    try:
        client = get_openai_client()
    except ValueError as e:
        print(f"Warning: Skill matching skipped - {str(e)}", file=sys.stderr)
        return []
    
    match_prompt = """
You are a skill matching system for ATS (Applicant Tracking System).

TASK: Match resume skills against JD skills and return only the matching ones.

MATCHING RULES:
1. Match if the resume skill is the same as a JD skill (case-insensitive)
2. Match if the resume skill is a variant/version of a JD skill:
   - JD: "Python" → Resume: "Python 3", "Python 3.9" ✓
   - JD: "SQL" → Resume: "MySQL", "PostgreSQL", "MS SQL" ✓
   - JD: "VMware Horizon" → Resume: "VMware", "VMware VDI" ✓
   - JD: "Oracle EBS" → Resume: "Oracle R12", "Oracle E-Business Suite" ✓
3. Match semantically similar skills:
   - JD: "Project Management" → Resume: "Program Management", "PMO" ✓
   - JD: "Process Improvements" → Resume: "Process Improvements", "Process Optimization" ✓
4. DO NOT match if the skill is NOT in the JD skills list (even if related)
5. DO NOT add skills that are not in the resume skills list
6. Return complete skill names from the resume (not partial names)
7. When in doubt, DO NOT match (prioritize precision)

Return ONLY a JSON array of matching resume skill names, nothing else.
Example: ["Python 3", "MySQL", "Project Management"]
"""
    
    user_prompt = f"""JD Skills (extracted from Job Description):
{json.dumps(jd_skills)}

Resume Skills:
{json.dumps(resume_skill_names)}

Return only the matching resume skills as a JSON array."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": match_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.choices[0].message.content
        if not content:
            print("Warning: Empty response from skill matching API.", file=sys.stderr)
            return []
        
        matched_skill_names = json.loads(content)
        
        if not isinstance(matched_skill_names, list):
            print("Warning: Invalid skill matching response format.", file=sys.stderr)
            return []
        
        print(f"Matched {len(matched_skill_names)} resume skills with JD skills", file=sys.stderr)
        return matched_skill_names
        
    except RateLimitError:
        print("Warning: OpenAI API rate limit exceeded during skill matching.", file=sys.stderr)
        return []
    except (APIConnectionError, APIError, OpenAIError) as e:
        print(f"Warning: OpenAI API error during skill matching: {str(e)}.", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse skill matching response: {str(e)}.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Unexpected error during skill matching: {str(e)}.", file=sys.stderr)
        return []


def filter_skills_by_jd(extracted_skills, jd_text):
    """
    Filter extracted skills to only include those explicitly present in the JD.
    Uses a two-step process: first extract JD skills, then match resume skills.
    """
    if not jd_text or not extracted_skills:
        return []
    
    # Step 1: Extract skills explicitly mentioned in the JD
    jd_skills = extract_jd_skills(jd_text)
    
    if not jd_skills:
        print("Warning: No skills extracted from JD. Returning empty skills list.", file=sys.stderr)
        return []
    
    # Step 2: Get resume skill names
    skill_names = [skill.get("skill_name", "") for skill in extracted_skills if skill.get("skill_name")]
    
    if not skill_names:
        return []
    
    print(f"Resume has {len(skill_names)} skills to match against {len(jd_skills)} JD skills", file=sys.stderr)
    
    # Step 3: Match resume skills with JD skills
    matched_skill_names = match_resume_skills_with_jd(skill_names, jd_skills)
    
    if not matched_skill_names:
        return []
    
    # Step 4: Filter original skill objects to keep only matched ones
    filtered_skills = [
        skill for skill in extracted_skills 
        if skill.get("skill_name", "") in matched_skill_names
    ]
    
    return filtered_skills

# -------------------------
# MAIN PIPELINE
# -------------------------

def parse_resume(pdf_path, jd_path=None):
    """
    Parse resume from PDF with optional JD-based skill filtering.
    
    Args:
        pdf_path: Path to the resume PDF file
        jd_path: Optional path to Job Description text file
    
    Returns:
        dict: Parsed resume data
    
    Raises:
        FileNotFoundError: If PDF file not found
        ValueError: If invalid input or API configuration
        RuntimeError: If processing fails
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Extract regex-based fields (safe operations)
    try:
        result = {
            "emails": extract_emails(text),
            "contact_numbers": extract_phone_numbers(text),
            "linkedin_url": extract_linkedin(text),
            "date_of_birth": extract_dob(text)
        }
    except Exception as e:
        print(f"Warning: Error during regex extraction: {str(e)}. Using empty values.", file=sys.stderr)
        result = {
            "emails": [],
            "contact_numbers": [],
            "linkedin_url": None,
            "date_of_birth": None
        }
    
    # Extract structured fields using LLM
    structured = extract_structured_fields(text)
    result.update(structured)
    
    # Apply JD-based skill filtering if JD is provided
    if jd_path:
        jd_text = read_jd_file(jd_path)
        if jd_text:
            result["skills"] = filter_skills_by_jd(result.get("skills", []), jd_text)

    return result

# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":
    pdf_path = "Resume/resume9.pdf"  
    jd_path = "jds/EUC_Delivery_lead.txt" 

    try:
        # Validate input
        if not pdf_path:
            print("Error: PDF path is required", file=sys.stderr)
            sys.exit(1)
        
        if not os.path.exists(pdf_path):
            print(f"Error: Resume PDF not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        
        # Parse resume
        print(f"Processing resume: {pdf_path}", file=sys.stderr)
        if jd_path:
            print(f"Applying JD filtering from: {jd_path}", file=sys.stderr)
        
        parsed_data = parse_resume(pdf_path, jd_path)
        
        # Output results
        print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
        print("\n✓ Resume parsing completed successfully", file=sys.stderr)
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
