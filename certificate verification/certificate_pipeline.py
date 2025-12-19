from ocr_service import extract_text_from_image
from generic_parser import parse_generic_certificate

def process_certificate(image_path: str) -> dict:
    raw_text = extract_text_from_image(image_path)
    parsed = parse_generic_certificate(raw_text)
    parsed["raw_text"] = raw_text
    return parsed
