import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import json
import re
import string
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from llm_caller import generate_answer, classify_scope
from prompt_builder import (
    build_anchored_success_prompt,
    build_anchored_not_found_prompt,
    build_unanchored_rag_prompt,
)
from security import sanitize_user_input, wrap_untrusted, sanitize_output, guard_protected_data

app = FastAPI(title="VLearn Tutor API - Dual Engine")

# Chỉ trả về prompt nội bộ (final_prompt_template) khi bật debug tường minh.
# Mặc định TẮT để không rò rỉ system prompt cho người tấn công.
DEBUG_EXPOSE_PROMPT = os.getenv("DEBUG_EXPOSE_PROMPT", "0") == "1"

# Bật/tắt lớp phân loại phạm vi bằng LLM (gate cứng cho câu lạc đề). Mặc định BẬT.
SCOPE_GUARD_ENABLED = os.getenv("SCOPE_GUARD_ENABLED", "1") == "1"

# Thông điệp từ chối cố định cho câu hỏi ngoài phạm vi (không gọi LLM sinh).
OUT_OF_SCOPE_REPLY = (
    "Mình là trợ giảng AI của khoá học, nên chỉ hỗ trợ các câu hỏi liên quan tới "
    "nội dung slide và bài giảng (AI, LLM, cách xác định và thiết kế bài toán cho AI...). "
    "Câu hỏi này nằm ngoài phạm vi đó nên mình xin phép không trả lời. "
    "Bạn thử hỏi mình về nội dung khoá học nhé!"
)

def _out_of_scope_response(mode="out_of_scope"):
    return {
        "mode": mode,
        "detected_page": None,
        "answer": OUT_OF_SCOPE_REPLY,
        "follow_up": [
            "Bạn muốn mình giải thích khái niệm nào trong bài giảng?",
            "Bạn đang xem slide ở trang nào và cần làm rõ phần gì?",
        ],
        "citations": [],
        "external_links": [],
    }

# --- 1. STARTUP: LOAD DATABASES ---
_CODEBASE_DIR = os.path.dirname(os.path.dirname(__file__))
SLIDE_DB_PATH = os.path.join(_CODEBASE_DIR, "data", "slide_db.json")
QDRANT_PATH = os.path.join(_CODEBASE_DIR, "data", "qdrant_db")

slide_db = {}
if os.path.exists(SLIDE_DB_PATH):
    with open(SLIDE_DB_PATH, "r", encoding="utf-8") as f:
        slide_db = json.load(f)

# Load Qdrant Client & Embedding Model
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if qdrant_url and qdrant_api_key:
        print("Connecting to Qdrant Cloud...")
        qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        print("Connecting to Qdrant Local...")
        qdrant = QdrantClient(path=QDRANT_PATH)
        
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    print(f"Warning: Qdrant or Encoder not fully initialized: {e}")
    qdrant = None
    encoder = None

# --- 2. MODELS ---
class ChatRequest(BaseModel):
    message: str

# --- 3. HELPER: DETERMINISTIC LOOKUP ---
def normalize_text(text):
    if not text: return ""
    return re.sub(r'\s+', '', text).lower()

def exact_match_lookup(highlighted_text):
    norm_highlight = normalize_text(highlighted_text)
    for page_id, content in slide_db.items():
        if norm_highlight in normalize_text(content):
            return page_id, content
    return None, None

def find_best_slide_for_free_chat(query):
    if not slide_db: return "1" # Fallback
    
    # Tokenize query bỏ dấu câu và in thường
    query_tokens = set(re.findall(r'\w+', query.lower()))
    if not query_tokens: return "1"
    
    best_page = "1"
    max_score = -1
    
    for page_id, content in slide_db.items():
        # Trọng số nhẹ cho slide
        slide_tokens = set(re.findall(r'\w+', content.lower()))
        score = len(query_tokens.intersection(slide_tokens))
        
        if score > max_score:
            max_score = score
            best_page = page_id
            
    # Dù score = 0 vẫn trả về 1 page bất kỳ (thường là page đầu) hoặc trang có score cao nhất
    return best_page

def _finalize_response(response_dict, llm_response, prompt, security_meta, protected_texts=None):
    """Gộp kết quả LLM, chạy lớp phòng thủ đầu ra, và ẩn/hiện prompt nội bộ."""
    if isinstance(llm_response, dict):
        # Lớp output guard: chỉ giữ citation trỏ tới trang có thật, lọc rò rỉ prompt
        llm_response = sanitize_output(llm_response, slide_db.keys())
        # Lớp TẤT ĐỊNH chống rò rỉ tài liệu: chặn nếu answer sao chép nguyên văn đoạn dài
        # của slide/transcript (hoạt động kể cả khi model bị jailbreak).
        if protected_texts:
            llm_response = guard_protected_data(llm_response, protected_texts)
        response_dict.update(llm_response)
    else:
        response_dict["llm_response"] = llm_response

    # Chỉ lộ prompt nội bộ khi bật debug tường minh (tránh rò rỉ system prompt)
    if DEBUG_EXPOSE_PROMPT:
        response_dict["final_prompt_template"] = prompt

    # Gắn cờ bảo mật (không lộ chi tiết pattern ra ngoài)
    if security_meta.get("suspicious"):
        response_dict["security_flag"] = True
    return response_dict

# --- 4. API ENDPOINT ---
@app.post("/chat")
def chat(request: ChatRequest):
    # BƯỚC 0: LÀM SẠCH ĐẦU VÀO (lớp phòng thủ input)
    sec = sanitize_user_input(request.message)
    user_message = sec["clean"]

    if not user_message:
        return {"mode": "rejected", "answer": "Bạn vui lòng nhập câu hỏi về nội dung khoá học nhé.",
                "follow_up": [], "citations": [], "external_links": []}

    # BƯỚC 1: Parse Regex tìm Anchor
    # Pattern VLearn: (Trang 37, đoạn được chọn: "tóm tắt nội dung")
    match = re.search(r'\(Trang\s*(\d+),\s*đoạn được chọn:\s*"(.*?)"\)', user_message, re.IGNORECASE)
    
    if match:
        # ==========================================
        # NHÁNH A: ANCHORED (DETERMINISTIC LOOKUP)
        # ==========================================
        reported_page = match.group(1)
        highlighted_text = match.group(2)
        real_question = user_message[match.end():].strip()

        # Bọc câu hỏi người dùng như DỮ LIỆU, không phải chỉ thị
        safe_question = wrap_untrusted(real_question)

        page_id, slide_context = exact_match_lookup(highlighted_text)
        
        if slide_context:
            prompt = build_anchored_success_prompt(slide_context, page_id, safe_question)
            mode = "anchored_success"
            enable_search = True
        else:
            prompt = build_anchored_not_found_prompt(safe_question)
            mode = "anchored_not_found"
            slide_context = None
            enable_search = False
            
        # GỌI GEMINI AI VỚI TÍNH NĂNG GOOGLE SEARCH
        llm_response = generate_answer(prompt, enable_search=enable_search)

        response_dict = {
            "mode": mode,
            "detected_page": reported_page,
        }
        # Nội dung được bảo vệ đã đưa vào prompt nhánh A: chính là slide_context (nếu có)
        protected = [slide_context] if slide_context else []
        return _finalize_response(response_dict, llm_response, prompt, sec, protected)
        
    else:
        # ==========================================
        # NHÁNH B: UNANCHORED (QDRANT RAG)
        # ==========================================
        # LỚP PHẠM VI CỨNG: phân loại IN/OUT trước khi làm bất cứ gì.
        # Câu lạc đề -> từ chối ngay, KHÔNG gọi LLM sinh, KHÔNG Google Search.
        if SCOPE_GUARD_ENABLED and classify_scope(user_message) == "OUT":
            resp = _out_of_scope_response()
            if sec.get("suspicious"):
                resp["security_flag"] = True
            return resp

        if qdrant is None or encoder is None:
            return {"mode": "unanchored", "error": "Qdrant not initialized"}
            
        # Tìm kiếm Semantic bằng Qdrant (Tri thức lời giảng)
        try:
            response = qdrant.query_points(
                collection_name="transcripts",
                query=encoder.encode(user_message).tolist(),
                limit=3,
                with_payload=True
            )
            hits = response.points
        except Exception as e:
            print("Lỗi truy vấn Qdrant:", e)
            hits = []
        
        retrieved_texts = [hit.payload.get('text', '') for hit in hits] if hits else []
        combined_context = "\n".join(retrieved_texts)
        
        # Tìm kiếm Slide (Nguồn trích dẫn)
        best_slide_page = find_best_slide_for_free_chat(user_message)

        # Bọc câu hỏi người dùng như DỮ LIỆU, không phải chỉ thị
        safe_question = wrap_untrusted(user_message)
        prompt = build_unanchored_rag_prompt(safe_question, combined_context, best_slide_page)
        
        # GỌI GEMINI AI VỚI TÍNH NĂNG GOOGLE SEARCH BẬT LÊN
        llm_response = generate_answer(prompt, enable_search=True)

        response_dict = {
            "mode": "unanchored_rag",
            "detected_page": best_slide_page,
        }
        # Nội dung được bảo vệ đã đưa vào prompt nhánh B: các đoạn transcript + slide được map
        protected = list(retrieved_texts)
        mapped_slide = slide_db.get(best_slide_page)
        if mapped_slide:
            protected.append(mapped_slide)
        return _finalize_response(response_dict, llm_response, prompt, sec, protected)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
