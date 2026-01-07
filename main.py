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

    prompt = f"""
You are a STRICT ATS resume parser.

Your task is to extract structured data ONLY from the provided resume text.

IMPORTANT RULES (must follow):
1. Extract ONLY information that is explicitly present in the resume text.
2. DO NOT guess, infer, assume, normalize, or fabricate any data.
3. If a field is not present, return an empty string ("") or empty list ([]).
4. Do NOT repeat entries.
5. Do NOT duplicate sections.
6. Return VALID JSON ONLY that strictly matches the schema.
7. Do NOT add explanations, comments, or extra text.

SECTION HANDLING RULES:
- Treat sections such as "SKILLS", "KEY COMPETENCIES", "CORE SKILLS", or similar as SKILLS.
- Treat sections such as "EXPERIENCE", "WORK EXPERIENCE", or "PROFESSIONAL EXPERIENCE" as EXPERIENCE.
- Treat addresses only if explicitly written as a location or address.

EDUCATION RULES:
- Extract multiple education entries if present.
- Identify the highest degree ONLY by comparing degrees explicitly mentioned.
- Do NOT assume dates, results, or percentages.
- Extract education dates EXACTLY as written in the resume.
- If a single year is mentioned (e.g., "2021"), return that year.
- If a range is mentioned (e.g., "2025 - 2029" or "2029–2030"), return the FULL RANGE STRING exactly as written.
- Do NOT convert ranges into a single year.
- Do NOT infer missing start or end years.
- Do NOT normalize or reformat date ranges.
- If no date is mentioned, return an empty string.

EXPERIENCE RULES:
- Extract multiple experience entries in chronological order.
- Use "Present" only if explicitly written.
- Projects must belong ONLY to their respective experience.
- If salary, hike, or pay unit is not present, leave it empty.

SKILLS RULES:
- Extract skills as individual entries.
- Use skillset_type ONLY if explicitly mentioned (e.g., Technical, Soft Skills).
- Do NOT infer years of experience or last used dates.

ADDRESS RULES:
- Extract only addresses explicitly present.
- Do NOT infer address start or end dates.

OUTPUT FORMAT:
Return a SINGLE JSON object using EXACTLY this schema:

{{
  "education": [
    {{
      "degree": "",
      "subject": "",
      "year_passed": "",
      "result": "",
      "college_university": "",
      "percentage": "",
      "is_highest": false
    }}
  ],
  "experience": [
    {{
      "organization": "",
      "job_title": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "last_pay_rate": "",
      "pay_uom": "",
      "last_hike_date": "",
      "projects": [
        {{
          "project_name": "",
          "project_details": ""
        }}
      ]
    }}
  ],
  "skills": [
    {{
      "skillset_type": "",
      "skill_name": "",
      "years": "",
      "last_used": ""
    }}
  ],
  "addresses": [
    {{
      "address": "",
      "start_date_active": "",
      "end_date_active": ""
    }}
  ]
}}

Resume Text:
{text}
"""


    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "You are a strict ATS resume parser."},
            {"role": "user", "content": prompt}
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
    pdf_path = "Resume/resume4.pdf"  # <-- put your resume path here

    if not os.path.exists(pdf_path):
        raise FileNotFoundError("Resume PDF not found")

    parsed_data = parse_resume(pdf_path)

    print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
