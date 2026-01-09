import os
import re
import json
import pdfplumber
from openai import OpenAI

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
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

# -------------------------
# LLM STRUCTURED EXTRACTION
# -------------------------

def extract_structured_fields(text):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return json.loads(response.choices[0].message.content)

# -------------------------
# MAIN PIPELINE
# -------------------------

def parse_resume(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    result = {
        "emails": extract_emails(text),
        "contact_numbers": extract_phone_numbers(text),
        "linkedin_url": extract_linkedin(text),
        "date_of_birth": extract_dob(text)
    }

    structured = extract_structured_fields(text)
    result.update(structured)

    return result

# -------------------------
# RUN
# -------------------------

if __name__ == "__main__":
    pdf_path = "Resume/resume7.pdf"  # <-- put your resume path here

    if not os.path.exists(pdf_path):
        raise FileNotFoundError("Resume PDF not found")

    parsed_data = parse_resume(pdf_path)

    print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
