from certificate_service import handle_uploaded_certificate

def simulate_submit_certificate():
    
    uploaded_image_path = r"C:\Users\aishw\Downloads\hackathon\certificate (2).jpg"
    claimed_name = "DHRUTHI RUDRANGI"  
    claimed_course = "Introduction to Graph Algorithms"  

    result = handle_uploaded_certificate(
        image_path=uploaded_image_path,
        claimed_name=claimed_name,
        claimed_course=claimed_course,
    )

    parsed = result["parsed"]
    checks = result["checks"]

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
    print("\nVerification checks:")
    for k, v in checks.items():
        print(f"- {k}: {v}")

if __name__ == "__main__":
    simulate_submit_certificate()
