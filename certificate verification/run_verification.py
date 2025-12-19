from certificate_pipeline import process_certificate, verify_claim

if __name__ == "__main__":
    path_to_uploaded_file = r"C:\Users\aishw\Downloads\hackathon\certificate (2).jpg"

    parsed = process_certificate(path_to_uploaded_file)

    claimed_name = "Dhruthi Rudrangi"
    claimed_course = "Introduction to Graph Algorithms"

    checks = verify_claim(parsed, claimed_name, claimed_course)

    print("PARSED:", parsed)
    print("CHECKS:", checks)
