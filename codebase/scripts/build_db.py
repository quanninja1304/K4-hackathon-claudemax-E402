import fitz  # PyMuPDF
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODEBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_slide_db():
    pdf_files = [
        os.path.join(REPO_ROOT, "data", "vlearn-pack", "slides", "d1-slide-hackathon.pdf"),
        os.path.join(REPO_ROOT, "data", "vlearn-pack", "slides", "d2-slide-hackathon.pdf"),
    ]
    
    db = {}
    
    for pdf_path in pdf_files:
        if not os.path.exists(pdf_path):
            print(f"File không tồn tại: {pdf_path}")
            continue
            
        doc = fitz.open(pdf_path)
        print(f"Processing: {os.path.basename(pdf_path)} ({len(doc)} pages)")
        
        for i, page in enumerate(doc):
            text = page.get_text()
            
            # TRICKY PART: Tìm số trang thật ở footer
            # Thường nằm ở cuối đoạn text. Ta lấy vài dòng cuối để tìm số.
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            real_page_number = None
            # Quét từ dưới lên để tìm dòng chứa mỗi một con số (số trang)
            for line in reversed(lines[-5:]):
                if line.isdigit():
                    real_page_number = line
                    break
            
            if not real_page_number:
                # Nếu không tìm thấy, đành dùng số thứ tự vật lý
                real_page_number = f"unmatched_{os.path.basename(pdf_path)}_idx_{i}"
                
            db[real_page_number] = text
            print(f"  - Physical page {i+1} -> Real page (Footer): {real_page_number}")
            
    # Save to JSON
    out_path = os.path.join(CODEBASE_DIR, "data", "slide_db.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        
    print(f"\nSaved DB to: {out_path}")
    print(f"Total indexed pages: {len(db)}")

if __name__ == "__main__":
    build_slide_db()
