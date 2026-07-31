import os
import fitz
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pdf_files = [
    os.path.join(REPO_ROOT, "data", "vlearn-pack", "slides", "d1-slide-hackathon.pdf"),
    os.path.join(REPO_ROOT, "data", "vlearn-pack", "slides", "d2-slide-hackathon.pdf"),
]

for pdf in pdf_files:
    print(f"--- {pdf} ---")
    doc = fitz.open(pdf)
    for i, page in enumerate(doc):
        text = page.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if re.fullmatch(r'\d+', line):
                print(f"Page {i+1} has standalone number: {line}")
