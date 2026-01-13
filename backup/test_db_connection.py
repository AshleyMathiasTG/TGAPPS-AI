"""
Quick test script to verify database connectivity and basic operations.
"""

import sys
from db_integration import (
    create_db_connection,
    close_db_connection,
    get_candidate_basic_info,
    get_job_description
)

def test_connection():
    """Test basic database connection."""
    print("\n" + "="*60)
    print("Test 1: Database Connection")
    print("="*60)
    
    conn = create_db_connection()
    if conn:
        print("✅ SUCCESS: Database connection established")
        close_db_connection(conn)
        return True
    else:
        print("❌ FAILED: Could not connect to database")
        return False

def test_candidate_retrieval():
    """Test retrieving candidate information."""
    print("\n" + "="*60)
    print("Test 2: Candidate Information Retrieval")
    print("="*60)
    
    # Prompt for candidate ID
    candidate_id = input("\nEnter a candidate ID to test (or press Enter to skip): ").strip()
    
    if not candidate_id:
        print("⏭️  SKIPPED: No candidate ID provided")
        return None
    
    try:
        candidate_id = int(candidate_id)
    except ValueError:
        print("❌ FAILED: Invalid candidate ID format")
        return False
    
    candidate_info = get_candidate_basic_info(candidate_id)
    
    if candidate_info:
        print("\n✅ SUCCESS: Retrieved candidate information")
        print("\nCandidate Details:")
        print(f"  - ID: {candidate_info.get('candidate_id')}")
        print(f"  - Name: {candidate_info.get('full_name')}")
        print(f"  - Company ID: {candidate_info.get('company_id')}")
        print(f"  - LinkedIn: {candidate_info.get('linkedin_profile') or 'N/A'}")
        print(f"  - DOB: {candidate_info.get('date_of_birth') or 'N/A'}")
        print(f"  - Resume Content: {'Available' if candidate_info.get('resume_content') else 'Not Available'}")
        return True
    else:
        print(f"❌ FAILED: Could not retrieve candidate with ID: {candidate_id}")
        return False

def test_jd_retrieval():
    """Test retrieving job description."""
    print("\n" + "="*60)
    print("Test 3: Job Description Retrieval")
    print("="*60)
    
    # Prompt for candidate ID
    candidate_id = input("\nEnter a candidate ID to test JD retrieval (or press Enter to skip): ").strip()
    
    if not candidate_id:
        print("⏭️  SKIPPED: No candidate ID provided")
        return None
    
    try:
        candidate_id = int(candidate_id)
    except ValueError:
        print("❌ FAILED: Invalid candidate ID format")
        return False
    
    jd_text = get_job_description(candidate_id)
    
    if jd_text:
        print("\n✅ SUCCESS: Retrieved Job Description")
        print(f"\nJD Preview (first 200 characters):")
        print(f"  {jd_text[:200]}...")
        print(f"\nTotal Length: {len(jd_text)} characters")
        return True
    else:
        print(f"⚠️  WARNING: No Job Description found for candidate ID: {candidate_id}")
        print("  (This might be expected if the candidate has no JD assigned)")
        return None

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TGApps Database Integration - Connection Test")
    print("="*60)
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    results = []
    
    # Test 1: Connection
    results.append(("Database Connection", test_connection()))
    
    # Test 2: Candidate Retrieval
    if results[0][1]:  # Only if connection succeeded
        results.append(("Candidate Retrieval", test_candidate_retrieval()))
        
        # Test 3: JD Retrieval
        if results[1][1]:  # Only if candidate retrieval succeeded
            results.append(("Job Description Retrieval", test_jd_retrieval()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results:
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⏭️  SKIPPED"
        print(f"{test_name}: {status}")
    
    # Overall result
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    print("\n" + "="*60)
    print(f"Tests Run: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print("="*60 + "\n")
    
    if failed == 0 and passed > 0:
        print("🎉 All tests passed! Database integration is ready.")
        return 0
    elif failed > 0:
        print("❌ Some tests failed. Please review the errors above.")
        return 1
    else:
        print("⚠️  No tests were executed. Please provide candidate IDs to test.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
