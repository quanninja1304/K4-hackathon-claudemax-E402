import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import json
import re
import string
import unicodedata
from typing import Optional

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
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Trỏ về thư mục codebase/
SLIDE_DB_PATH = os.path.join(BASE_DIR, "data", "slide_db.json")
QDRANT_PATH = os.path.join(BASE_DIR, "data", "qdrant_db")

# Danh sách tài liệu hợp lệ mà UI có thể báo về. Key = doc_id gửi từ FE,
# value = prefix thật sự dùng trong slide_db.json.
# Thêm 1 dòng ở đây mỗi khi có tài liệu mới -- không hardcode rải rác trong code nữa.
KNOWN_DOCS = {
    "d1-slide-hackathon.pdf": "unmatched_d1-slide-hackathon.pdf_idx_",
    "d2-slide-hackathon.pdf": "unmatched_d2-slide-hackathon.pdf_idx_",
}

# Cụm boilerplate lặp lại trên gần như mọi trang (watermark/footer chương trình).
# Những cụm này không mang tín hiệu định vị trang -> phải loại bỏ trước khi so khớp,
# nếu không Slow Path sẽ luôn "trúng" trang đầu tiên trong DB một cách giả tạo.
BOILERPLATE_PATTERNS = [
    r"AI\s*IN\s*ACTION\s*-\s*HACKATHON",
    r"AI\s*IN\s*ACTION\s*-\s*Day\s*\d+",
    r"AI\s*IN\s*ACTION\s*[·.]?\s*DAY\s*0?\d+",
]
_BOILERPLATE_RE = re.compile("|".join(BOILERPLATE_PATTERNS), re.IGNORECASE)

# Ngưỡng độ dài tối thiểu (sau khi đã strip boilerplate) để cho phép chạy Slow Path.
# Dưới ngưỡng này, tín hiệu quá nhiễu -> nhảy thẳng sang fallback tin tưởng page_X.
MIN_LEN_FOR_SLOW_PATH = 15

# Hư từ tiếng Việt phổ biến -- không mang tín hiệu định vị nội dung, nhưng nếu không
# loại bỏ sẽ làm lệch điểm token-overlap trong find_best_slide_for_free_chat
# (VD: "là", "gì" khớp với rất nhiều slide bất kỳ, đủ để một slide sai điểm cao
# hơn slide đúng chỉ vì có thêm 2 hư từ này).
VI_STOPWORDS = {
    "là", "gì", "và", "của", "có", "được", "cho", "trong", "với", "một",
    "các", "để", "khi", "này", "đó", "như", "nên", "thì", "hay", "hoặc",
    "không", "vẫn", "sẽ", "đã", "đang", "ở", "về", "mà", "nếu", "vì",
    "bạn", "mình", "chúng", "ta", "họ", "nó", "ai", "sao", "thế", "nào",
}

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
    doc_id: Optional[str] = None
    highlighted_text: Optional[str] = None
    highlighted_page: Optional[int] = None


# --- 3. HELPERS ---

def normalize_text(text: str) -> str:
    """Chuẩn hoá text trước khi so khớp: unicode NFKC, bỏ toàn bộ whitespace,
    lowercase, và bỏ một số dấu câu phổ biến hay bị lệch giữa các công cụ extract
    PDF khác nhau (dấu gạch ngang, ngoặc đơn, dấu chấm/phẩy...).

    Trước đây hàm này chỉ xử lý whitespace -> "AI IN ACTION - Day 1" và
    "AI IN ACTION  Day 1" (thiếu dấu -) bị coi là KHÁC NHAU, khiến Fast Path
    fail oan dù page/file đều đúng.
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', '', text)
    # Bỏ các dấu câu hay gây lệch giữa các nguồn extract (giữ lại chữ/số/dấu tiếng Việt)
    text = re.sub(r'[-_()\[\]{}.,;:!?"\'`]', '', text)
    return text.lower()


def strip_boilerplate(text: str) -> str:
    """Loại các cụm watermark/footer lặp lại trên mọi trang khỏi đoạn học viên
    bôi đen, trước khi tính độ dài và trước khi dùng làm tín hiệu tìm kiếm.
    Nếu không làm bước này, watermark 24 ký tự "AI IN ACTION - HACKATHON"
    (xuất hiện trên 100% slide) sẽ vượt ngưỡng độ dài và luôn match trang đầu DB.
    """
    if not text:
        return ""
    return _BOILERPLATE_RE.sub("", text).strip()


def resolve_doc_prefix(doc_id: Optional[str]) -> Optional[str]:
    """Map doc_id do FE gửi lên -> prefix key thật trong slide_db.
    Trả None nếu doc_id không xác định / không nằm trong danh sách tài liệu biết trước.
    """
    if not doc_id:
        return None
    return KNOWN_DOCS.get(doc_id)


def iter_db_for_doc(doc_prefix: Optional[str]):
    """Duyệt slide_db, giới hạn đúng 1 tài liệu nếu biết doc_prefix.
    Nếu doc_prefix=None (không rõ tài liệu), fallback duyệt toàn bộ -- nhưng
    trường hợp này chỉ nên xảy ra khi FE thực sự không gửi được doc_id, và
    kết quả trả về cần được đánh dấu kém tin cậy hơn ở tầng gọi.
    """
    if doc_prefix:
        for page_id, content in slide_db.items():
            if page_id.startswith(doc_prefix):
                yield page_id, content
    else:
        for page_id, content in slide_db.items():
            yield page_id, content


def page_num_from_key(page_id: str) -> Optional[int]:
    """Lấy số idx (0-based) từ key dạng '..._idx_12' -> 12."""
    m = re.search(r'_idx_(\d+)$', page_id)
    return int(m.group(1)) if m else None


def exact_match_lookup_all(highlighted_text: str, doc_prefix: Optional[str], near_idx: Optional[int]):
    """Tìm TẤT CẢ trang chứa đoạn bôi đen (đã strip boilerplate), giới hạn đúng tài liệu đang xem."""
    norm_highlight = normalize_text(highlighted_text)
    if not norm_highlight:
        return []

    candidates = []
    for page_id, content in iter_db_for_doc(doc_prefix):
        if norm_highlight in normalize_text(content):
            candidates.append(page_id)

    if not candidates:
        return []

    if near_idx is not None:
        candidates.sort(key=lambda pid: abs((page_num_from_key(pid) or 0) - near_idx))

    return candidates

def resolve_doc_id(page_id: str) -> Optional[str]:
    for doc_id, prefix in KNOWN_DOCS.items():
        if page_id.startswith(prefix):
            return doc_id
    return None


def find_best_slide_for_free_chat(query: str, doc_prefix: Optional[str] = None) -> str:
    """Token-overlap search cho luồng unanchored. Nếu biết doc_prefix (học viên
    đang mở 1 tài liệu cụ thể) thì chỉ tìm trong tài liệu đó; nếu không có
    context tài liệu nào (free chat ngoài trang slide) thì tìm toàn bộ DB.
    """
    pool = dict(iter_db_for_doc(doc_prefix)) if doc_prefix else slide_db
    if not pool:
        pool = slide_db
    if not pool:
        return "1"

    raw_query_tokens = set(re.findall(r'\w+', query.lower()))
    query_tokens = raw_query_tokens - VI_STOPWORDS
    # Nếu sau khi lọc stopword không còn token nào có nghĩa (câu hỏi toàn hư từ),
    # đành dùng lại token gốc để không mất khả năng tìm kiếm hoàn toàn.
    if not query_tokens:
        query_tokens = raw_query_tokens
    if not query_tokens:
        return next(iter(pool), "1")

    best_page = next(iter(pool))
    max_score = -1
    for page_id, content in pool.items():
        slide_tokens = set(re.findall(r'\w+', content.lower())) - VI_STOPWORDS
        score = len(query_tokens.intersection(slide_tokens))
        if score > max_score:
            max_score = score
            best_page = page_id

    return best_page


# --- 4. API ENDPOINT ---
@app.post("/chat")
def chat(request: ChatRequest):
    sec = sanitize_user_input(request.message)
    user_message = sec["clean"]

    if not user_message:
        return {"mode": "rejected", "answer": "Bạn vui lòng nhập câu hỏi nhé.", "citations": []}

    doc_prefix = resolve_doc_prefix(request.doc_id)
    if request.doc_id and doc_prefix is None:
        raise HTTPException(status_code=400, detail=f"Unknown doc_id: {request.doc_id}")

    # LỚP PHẠM VI CỨNG: phân loại IN/OUT trước khi làm bất cứ gì
    if SCOPE_GUARD_ENABLED and classify_scope(user_message) == "OUT":
        resp = _out_of_scope_response()
        if sec.get("suspicious"):
            resp["security_flag"] = True
        return resp

    if request.highlighted_text:
        # NHÁNH A: ANCHORED
        highlighted_text = strip_boilerplate(request.highlighted_text)
        
        reported_idx = None
        if request.highlighted_page is not None:
            reported_idx = request.highlighted_page - 1
            
        page_key = None
        slide_context = None
        if doc_prefix is not None and reported_idx is not None and reported_idx >= 0:
            page_key = f"{doc_prefix}{reported_idx}"
            slide_context = slide_db.get(page_key)

        norm_highlight = normalize_text(highlighted_text)
        final_context = None
        final_page_id = None
        unverified_highlight = False
        mode = None

        if slide_context and norm_highlight and norm_highlight in normalize_text(slide_context):
            final_context = slide_context
            final_page_id = page_key
            mode = "anchored_success"
        elif len(highlighted_text) >= MIN_LEN_FOR_SLOW_PATH:
            candidates = exact_match_lookup_all(highlighted_text, doc_prefix, near_idx=reported_idx)
            if candidates:
                final_page_id = candidates[0]
                final_context = slide_db.get(final_page_id)
                if len(candidates) > 1 and reported_idx is None:
                    mode = "anchored_ambiguous"
                else:
                    mode = "anchored_success_corrected"
            elif slide_context:
                final_context = slide_context
                final_page_id = page_key
                unverified_highlight = True
                mode = "anchored_unverified"
            else:
                mode = "anchored_not_found"
        elif slide_context:
            final_context = slide_context
            final_page_id = page_key
            unverified_highlight = True
            mode = "anchored_unverified"
        else:
            mode = "anchored_not_found"

        if final_context is not None:
            prompt = build_anchored_success_prompt(
                slide_context=final_context, 
                page_id=final_page_id, 
                question=user_message,
                highlighted_text=highlighted_text,
                unverified_highlight=unverified_highlight
            )
            enable_search = True
        else:
            prompt = build_anchored_not_found_prompt(user_message)
            enable_search = False

        llm_response = generate_answer(prompt, enable_search=enable_search)

        response_dict = {
            "mode": mode,
            "detected_page": str(request.highlighted_page) if request.highlighted_page else None,
            "doc_id": request.doc_id,
            "unverified_highlight": unverified_highlight,
        }
        
        if isinstance(llm_response, dict):
            llm_response = sanitize_output(llm_response, slide_db.keys())
            protected = [final_context] if final_context else []
            llm_response = guard_protected_data(llm_response, protected)
            
            if llm_response.get("citations") and final_page_id:
                page_num = page_num_from_key(final_page_id)
                page_num = page_num + 1 if page_num is not None else None
                doc_id = resolve_doc_id(final_page_id)
                llm_response["citations"] = [{
                    "doc_id": doc_id,
                    "page": page_num,
                    "raw_key": final_page_id
                }]
            else:
                llm_response["citations"] = []
                
            response_dict.update(llm_response)
        else:
            response_dict["llm_response"] = llm_response
            
        if sec.get("suspicious"):
            response_dict["security_flag"] = True
            
        if DEBUG_EXPOSE_PROMPT:
            response_dict["final_prompt_template"] = prompt

        return response_dict
        
    else:
        # NHÁNH B: UNANCHORED
        if qdrant is None or encoder is None:
            return {"mode": "unanchored", "error": "Qdrant not initialized"}

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

        best_slide_page = find_best_slide_for_free_chat(user_message, doc_prefix)

        prompt = build_unanchored_rag_prompt(user_message, combined_context, best_slide_page)

        llm_response = generate_answer(prompt, enable_search=True)

        response_dict = {
            "mode": "unanchored_rag",
            "detected_page": best_slide_page,
            "doc_id": request.doc_id,
        }
        
        if isinstance(llm_response, dict):
            llm_response = sanitize_output(llm_response, slide_db.keys())
            protected = list(retrieved_texts)
            mapped_slide = slide_db.get(best_slide_page)
            if mapped_slide:
                protected.append(mapped_slide)
            llm_response = guard_protected_data(llm_response, protected)
            
            if llm_response.get("citations") and best_slide_page:
                page_num = page_num_from_key(best_slide_page)
                page_num = page_num + 1 if page_num is not None else None
                doc_id = resolve_doc_id(best_slide_page)
                llm_response["citations"] = [{
                    "doc_id": doc_id,
                    "page": page_num,
                    "raw_key": best_slide_page
                }]
            else:
                llm_response["citations"] = []
                
            response_dict.update(llm_response)
        else:
            response_dict["llm_response"] = llm_response
            
        if sec.get("suspicious"):
            response_dict["security_flag"] = True

        if DEBUG_EXPOSE_PROMPT:
            response_dict["final_prompt_template"] = prompt

        return response_dict

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
