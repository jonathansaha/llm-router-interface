from PyPDF2 import PdfReader
import os
import glob

def extract_and_save_text_from_pdfs(output_filename="router_commands.txt"):
    directory = "/home/soap/be_u/nogfi/middleware/"
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

    # Save the combined text to a file for later use
    with open(output_filename, 'w') as output_file:
        output_file.write(combined_text)

    print(f"Text extracted and saved to {output_filename}")

