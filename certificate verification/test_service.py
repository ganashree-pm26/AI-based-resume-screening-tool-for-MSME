from certificate_service import handle_uploaded_certificate

if __name__ == "__main__":
    image_path = r"C:\Users\aishw\Downloads\hackathon\certificate (2).jpg"
    claimed_name = "DHRUTHI RUDRANGI"
    claimed_course = "Introduction to Graph Algorithms"

    result = handle_uploaded_certificate(image_path, claimed_name, claimed_course)

    parsed = result["parsed"]
    checks = result["checks"]
    validity = result["validity"]

    print("=== EMPLOYER VIEW ===")
    print(f"Student name : {parsed['student_name']}")
    print(f"Course       : {parsed['course_title']}")
    print(f"Platform     : {parsed['platform']}")
    print(f"Session      : {parsed['session']}")
    print(f"Instructor   : {parsed['instructor']}")
    print(f"Score        : {parsed['score_percent']}% "
          f"(Assignments {parsed['assignment_score']}, Exam {parsed['exam_score']})")
    print(f"Duration     : {parsed['duration']}")
    print(f"Credits      : {parsed['credits_recommended']}")
    print(f"Roll No      : {parsed['roll_no']}")

    print("\nValidity:")
    print(f"- Course end date : {validity['course_end_date']}")
    print(f"- Valid till      : {validity['valid_till']}")
    print(f"- Currently valid : {validity['is_currently_valid']}")

    print("\nVerification checks:")
    for k, v in checks.items():
        print(f"- {k}: {v}")
