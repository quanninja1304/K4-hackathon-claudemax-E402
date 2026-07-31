import os
import json

CODEBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(CODEBASE_DIR, "data", "slide_db.json"), "r", encoding="utf-8") as f:
    slide_db = json.load(f)

with open(os.path.join(SCRIPTS_DIR, "search_out.txt"), "w", encoding="utf-8") as out:
    out.write("--- SEARCH RESULTS ---\n")
    for page_id, content in slide_db.items():
        if "chiến lược" in content.lower():
            out.write(f"FOUND IN {page_id}:\n{content}\n")
            out.write("-"*40 + "\n")
