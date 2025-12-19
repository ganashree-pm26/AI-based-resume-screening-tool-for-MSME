from certificate_service import handle_uploaded_certificate
import json

# Test cases: [image_path, expected_name, expected_course]
TEST_CASES = [
    [
        r"C:\Users\aishw\Downloads\hackathon\certificate (2).jpg",
        "DHRUTHI RUDRANGI",
        "Introduction to Graph Algorithms"
    ],
    # Add more test images here:
    # [r"path\to\coursera_cert.jpg", "John Doe", "Machine Learning"],
    # [r"path\to\udemy_cert.jpg", "Jane Smith", "Python Bootcamp"],
]

def run_tests():
    results = []
    
    for i, (image_path, expected_name, expected_course) in enumerate(TEST_CASES):
        print(f"\n=== TEST {i+1}: {image_path} ===")
        
        try:
            result = handle_uploaded_certificate(image_path, expected_name, expected_course)
            
            parsed = result["parsed"]
            checks = result["checks"]
            validity = result["validity"]
            
            # Print employer view
            print(f"Name extracted: {parsed.get('student_name')}")
            print(f"Course extracted: {parsed.get('course_title')}")
            print(f"Score: {parsed.get('score_percent')}%")
            print(f"ID: {parsed.get('roll_or_id')}")
            print(f"Name match: {checks.get('name_matches')}")
            print(f"Course match: {checks.get('course_matches')}")
            print(f"Valid till: {validity.get('valid_till')}")
            
            # Test PASS/FAIL
            name_correct = parsed.get('student_name', '').strip().lower() == expected_name.strip().lower()
            course_correct = parsed.get('course_title', '').strip().lower() == expected_course.strip().lower()
            
            test_passed = name_correct and course_correct
            print(f"✅ TEST PASSED" if test_passed else "❌ TEST FAILED")
            print(f"  Name correct: {name_correct}")
            print(f"  Course correct: {course_correct}")
            
            results.append({
                "test": i+1,
                "image": image_path,
                "passed": test_passed,
                "extracted": {
                    "name": parsed.get('student_name'),
                    "course": parsed.get('course_title'),
                    "score": parsed.get('score_percent'),
                }
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({"test": i+1, "image": image_path, "passed": False, "error": str(e)})
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    passed = sum(1 for r in results if r["passed"])
    print(f"✅ PASSED: {passed}/{len(results)} tests")
    
    # Save results for demo
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("📄 Results saved to test_results.json")
    
    return results

if __name__ == "__main__":
    run_tests()
