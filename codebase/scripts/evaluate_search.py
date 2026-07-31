import os
import json
import re

CODEBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def normalize_text(text):
    """Xóa bỏ mọi khoảng trắng thừa, dấu xuống dòng, in thường để so sánh."""
    if not text: return ""
    return re.sub(r'\s+', '', text).lower()

def exact_match_lookup(highlighted_text, slide_db):
    norm_highlight = normalize_text(highlighted_text)
    
    for page_id, content in slide_db.items():
        norm_content = normalize_text(content)
        if norm_highlight in norm_content:
            return page_id, content
    return None, None

def evaluate():
    with open(os.path.join(CODEBASE_DIR, "data", "slide_db.json"), "r", encoding="utf-8") as f:
        slide_db = json.load(f)
        
    test_cases = [
        "giải thích 4 chiến lược", 
        "tóm tắt nội dung chính trong slide này", 
        "Hệ chuyên gia (expert system)",
        "deep learning là gì",
        "Token có giá: vé vào rẻ, vé ra đắt gấp",
        "Hành trình khóa học: LLM Foundation"
    ]
    
    with open(os.path.join(SCRIPTS_DIR, "evaluate_out.txt"), "w", encoding="utf-8") as f:
        f.write("--- EVALUATING MATCHING ALGORITHM ---\n")
        for text in test_cases:
            page_id, content = exact_match_lookup(text, slide_db)
            if page_id:
                f.write(f"[FOUND] '{text[:20]}...' at physical page: {page_id}\n")
            else:
                f.write(f"[NOT FOUND] '{text[:20]}...'\n")

if __name__ == "__main__":
    evaluate()
