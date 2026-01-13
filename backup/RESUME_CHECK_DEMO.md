# Resume Availability Check - Enhanced Error Handling

## Overview

The database integration now includes **enhanced resume availability checking** with clear, actionable error messages when a resume is not found.

## How It Works

### Step-by-Step Process:

```
1. Retrieve candidate basic info
   ↓
2. Check resume availability
   ├─ Check: Resume file in file server (adm_attachments)
   └─ Check: Resume content in database (mst_candidates.resume_content)
   ↓
3. BOTH checks performed BEFORE attempting parsing
   ↓
4. If NEITHER exists → Show detailed error message and STOP
   ↓
5. If either exists → Continue with parsing
```

## Enhanced Error Message

When **NO resume is found** (neither file nor content), you'll see:

```
============================================================
❌ RESUME NOT FOUND
============================================================

Candidate ID: 12345
Candidate Name: John Doe

⚠️  No resume available for this candidate:
   • No resume file in file server (adm_attachments)
   • No resume_content in database (mst_candidates)

💡 Action Required:
   1. Upload resume file to TGApps file server, OR
   2. Add resume content to mst_candidates.resume_content

============================================================
```

## Resume Availability Scenarios

### ✅ Scenario 1: Resume File Available
```
📄 Step 2: Checking resume availability...
✅ Resume file found: candidate_resume.pdf
📥 Step 3: Downloading resume from file server...
✅ Resume file downloaded successfully
```

### ✅ Scenario 2: Resume Content Available (No File)
```
📄 Step 2: Checking resume availability...
❌ No resume file found for candidate_id: 221522
⚠️  Resume file not available. Using resume_content from database...
✅ Resume content loaded from database
```

### ❌ Scenario 3: NO Resume Available
```
📄 Step 2: Checking resume availability...
❌ No resume file found for candidate_id: 12345

============================================================
❌ RESUME NOT FOUND
============================================================

Candidate ID: 12345
Candidate Name: John Doe

⚠️  No resume available for this candidate:
   • No resume file in file server (adm_attachments)
   • No resume_content in database (mst_candidates)

💡 Action Required:
   1. Upload resume file to TGApps file server, OR
   2. Add resume content to mst_candidates.resume_content

============================================================
```

## Code Implementation

### Early Resume Check (Before Parsing)

```python
# Step 2: Check if resume is available
print("\n📄 Step 2: Checking resume availability...", file=sys.stderr)

# First check if resume_content exists in database
has_resume_content = bool(candidate_info.get('resume_content') and 
                         candidate_info.get('resume_content').strip())

# Then check if resume file exists
resume_file_info = get_resume_file_details(candidate_id, company_id)

# If NEITHER exists, stop early with clear message
if not resume_file_info and not has_resume_content:
    print("\n" + "="*60, file=sys.stderr)
    print("❌ RESUME NOT FOUND", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"\nCandidate ID: {candidate_id}", file=sys.stderr)
    print(f"Candidate Name: {candidate_info.get('full_name')}", file=sys.stderr)
    print("\n⚠️  No resume available for this candidate:", file=sys.stderr)
    print("   • No resume file in file server (adm_attachments)", file=sys.stderr)
    print("   • No resume_content in database (mst_candidates)", file=sys.stderr)
    print("\n💡 Action Required:", file=sys.stderr)
    print("   1. Upload resume file to TGApps file server, OR", file=sys.stderr)
    print("   2. Add resume content to mst_candidates.resume_content", file=sys.stderr)
    print("\n" + "="*60 + "\n", file=sys.stderr)
    return None  # ← STOPS HERE, doesn't proceed to parsing
```

### Fallback Logic (If File Fails)

```python
# Try to get resume file from file server
resume_path = None
if resume_file_info:
    print("\n📥 Step 3: Downloading resume from file server...", file=sys.stderr)
    resume_path = download_resume_from_url(
        resume_file_info['file_sub_directory'],
        resume_file_info['file_name']
    )
    if resume_path:
        print(f"✅ Resume file downloaded successfully", file=sys.stderr)

# Fallback to resume_content if file download failed
if not resume_path and has_resume_content:
    print("\n⚠️  Resume file not available. Using resume_content from database...", file=sys.stderr)
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(candidate_info['resume_content'])
            resume_path = temp_file.name
        print(f"✅ Resume content loaded from database", file=sys.stderr)
    except Exception as e:
        print(f"❌ Failed to save resume_content to temp file: {e}", file=sys.stderr)
        return None
```

## Benefits

### ✅ **Clear Communication**
- Users immediately know if resume is missing
- No confusing error messages
- Actionable instructions provided

### ✅ **Early Exit**
- System doesn't waste time attempting to parse
- No unnecessary API calls
- Faster feedback to user

### ✅ **Debugging Support**
- Shows exactly which checks failed
- Helps identify database issues
- Makes troubleshooting easier

### ✅ **Graceful Degradation**
- Tries file server first
- Falls back to database content
- Handles both scenarios seamlessly

## Usage Example

```bash
# Run the integration
python db_integration.py

# Enter a candidate ID
Enter Candidate ID: 12345

# If no resume exists, you'll see:
============================================================
❌ RESUME NOT FOUND
============================================================
...
```

## Testing

To test the error handling:

1. **Test with valid candidate** (has resume):
   ```bash
   python db_integration.py
   # Enter: 221522
   ```

2. **Test with candidate without resume**:
   ```bash
   python db_integration.py
   # Enter: [candidate_id without resume]
   ```

## Summary

✅ **Early validation** prevents wasted processing  
✅ **Clear error messages** guide user actions  
✅ **Fallback mechanism** tries multiple sources  
✅ **Graceful handling** of all scenarios  

The system now provides a professional, user-friendly experience when handling missing resumes!
