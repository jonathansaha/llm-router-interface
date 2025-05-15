from PyPDF2 import PdfReader
import os
import glob

def extract_text_from_pdfs():
    directory = "/home/middleware/documents"
    pdf_paths = sorted(glob.glob(os.path.join(directory, "*.pdf")))

    combined_text = ""
    for path in pdf_paths:
        if os.path.exists(path):
            try:
                reader = PdfReader(path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        combined_text += text + "\n"
            except Exception as e:
                print(f"Failed to read {path}: {e}")
    return combined_text.strip()

