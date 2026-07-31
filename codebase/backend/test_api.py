import os
from fastapi.testclient import TestClient
from main import app
import json
import time

client = TestClient(app)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

def test_chat():
    out_file = open(os.path.join(BACKEND_DIR, "test_llm_out.txt"), "w", encoding="utf-8")
    
    def log(text):
        # Bỏ print(text) để terminal Windows không bị lỗi font chữ
        out_file.write(text + "\n")
        
    log("--- TESTING API /chat ---")
    
    # --- TEST NHÁNH A (BÔI ĐEN TỒN TẠI) ---
    log("\n[TEST 1] Anchored Flow (Found in DB)")
    req1 = {
        "message": "(Trang 5, đoạn được chọn: \"Hệ chuyên gia (expert system)\")\nGiải thích cho mình phần này với?"
    }
    res1 = client.post("/chat", json=req1)
    log(f"Result:\n{json.dumps(res1.json(), indent=2, ensure_ascii=False)}")
    time.sleep(5)

    # --- TEST NHÁNH A (BÔI ĐEN BỊ CẮT TRONG HACKATHON) ---
    log("\n[TEST 2] Anchored Flow (Truncated in Hackathon PDF)")
    req2 = {
        "message": "(Trang 45, đoạn được chọn: \"giải thích 4 chiến lược\")\nChiến lược 3 là gì?"
    }
    res2 = client.post("/chat", json=req2)
    log(f"Result:\n{json.dumps(res2.json(), indent=2, ensure_ascii=False)}")
    time.sleep(5)

    # --- TEST NHÁNH B (CHAT TỰ DO - DÙNG RAG VÀ SLIDE MAPPING) ---
    log("\n[TEST 3] Unanchored Flow (Test Slide Mapping)")
    free_queries = [
        "Hệ chuyên gia là gì?",               # Kì vọng map về Slide 5
        "Token có giá vé vào rẻ là sao?",    # Kì vọng map về Slide 26
        "Hành trình khóa học LLM",           # Kì vọng map về Slide 3 hoặc 4
        "Prompt Injection trong LLM là gì?"           # Câu hỏi chung chung
    ]
    
    for q in free_queries:
        safe_q = q.encode('ascii', 'ignore').decode('ascii')
        log(f"\n--- Query: '{safe_q}' ---")
        req = {"message": q}
        res = client.post("/chat", json=req)
        
        rag_result = res.json()
        log(f"-> Mapped Slide Page: {rag_result.get('detected_page')}")
        
        # In rút gọn context
        if 'retrieved_context' in rag_result:
            rag_result['retrieved_context'] = [c[:100] + "..." for c in rag_result['retrieved_context']]
            
        log(f"Result:\n{json.dumps(rag_result, indent=2, ensure_ascii=False)}")
        
        # Nghỉ 5 giây để tránh lỗi 429 RESOURCE_EXHAUSTED của Gemini Free Tier
        time.sleep(5)
        
    out_file.close()
    print("\n>>> Đã lưu kết quả LLM vào file: codebase/backend/test_llm_out.txt")


if __name__ == "__main__":
    test_chat()
