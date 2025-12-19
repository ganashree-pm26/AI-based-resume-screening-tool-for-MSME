from PIL import Image
import pytesseract

# Point to your Tesseract installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_certificate_text(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"Error: {e}"

# Test with your certificate image
if __name__ == "__main__":
    image_path = r"C:\Users\aishw\Downloads\hackathon\certificate (2).jpg"

    extracted_text = extract_certificate_text(image_path)
    print("=== EXTRACTED CERTIFICATE TEXT ===")
    print(extracted_text)
    print("=== END ===")
