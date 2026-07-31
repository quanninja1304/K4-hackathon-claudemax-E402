import os
import fitz

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

doc = fitz.open(os.path.join(REPO_ROOT, "data", "vlearn-pack", "slides", "d1-slide-hackathon.pdf"))
for i, page in enumerate(doc):
    text = page.get_text().strip()
    if text:
        last_line = text.split('\n')[-1]
        if last_line != "AI IN ACTION - HACKATHON":
            print(f"Page {i+1}: {last_line}")
