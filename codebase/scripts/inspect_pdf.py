import os
import fitz

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODEBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

doc = fitz.open(os.path.join(REPO_ROOT, "data", "vlearn-pack", "slides", "d1-slide-hackathon.pdf"))
text = doc[5].get_text() # Try page index 5
with open(os.path.join(CODEBASE_DIR, "data", "page5_dump.txt"), "w", encoding="utf-8") as f:
    f.write(text)
