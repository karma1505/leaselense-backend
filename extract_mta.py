from pypdf import PdfReader
import os

pdf_path = "../frontend/public/MTA_example.pdf"
output_path = "../frontend/public/MTA_full_text.txt"

def extract_pdf():
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF not found at {pdf_path}")
        return

    print(f"[INFO] Reading {pdf_path}...")
    reader = PdfReader(pdf_path)
    full_text = ""
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text += text + "\n\n"
        print(f" - Processed page {i+1}/{len(reader.pages)}")
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    print(f"[SUCCESS] Extracted {len(full_text)} characters to {output_path}")

if __name__ == "__main__":
    extract_pdf()
