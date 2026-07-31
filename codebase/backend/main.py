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
from llm_caller import generate_answer

app = FastAPI(title="VLearn Tutor API - Dual Engine")

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
    # Tên file tài liệu học viên đang xem trên UI, ví dụ "d1-slide-hackathon.pdf".
    # Đây là field BẮT BUỘC về mặt logic để Fast Path build đúng key -- không được
    # suy luận / hardcode filename từ phía backend nữa, vì DB giờ có nhiều tài liệu.
    doc_id: Optional[str] = None


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


def exact_match_lookup(highlighted_text: str, doc_prefix: Optional[str], near_idx: Optional[int]):
    """Tìm TẤT CẢ trang chứa đoạn bôi đen (đã strip boilerplate), giới hạn đúng
    tài liệu đang xem (doc_prefix). Nếu có nhiều trang cùng match, ưu tiên trang
    có idx GẦN near_idx nhất (thường là reported_page đã convert sang idx),
    thay vì luôn lấy kết quả đầu tiên theo thứ tự dict như code cũ.
    """
    norm_highlight = normalize_text(highlighted_text)
    if not norm_highlight:
        return None, None

    candidates = []
    for page_id, content in iter_db_for_doc(doc_prefix):
        if norm_highlight in normalize_text(content):
            candidates.append(page_id)

    if not candidates:
        return None, None

    if near_idx is not None:
        candidates.sort(key=lambda pid: abs((page_num_from_key(pid) or 0) - near_idx))
    # else: giữ nguyên thứ tự tìm thấy (không có mỏ neo để ưu tiên)

    best = candidates[0]
    return best, slide_db.get(best)


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
    user_message = request.message
    doc_prefix = resolve_doc_prefix(request.doc_id)

    if request.doc_id and doc_prefix is None:
        # FE gửi 1 doc_id lạ, không có trong KNOWN_DOCS -> báo lỗi rõ ràng thay vì
        # âm thầm coi như "không biết tài liệu nào" (dễ che giấu bug tích hợp).
        raise HTTPException(status_code=400, detail=f"Unknown doc_id: {request.doc_id}")

    match = re.search(r'\((?:Trang|Page)\s*(\d+),\s*(?:đoạn được chọn|highlighted):\s*"(.*?)"\)', user_message, re.IGNORECASE)

    if match:
        # ==========================================
        # NHÁNH A: ANCHORED (DETERMINISTIC LOOKUP)
        # ==========================================
        reported_page = match.group(1)
        raw_highlighted_text = match.group(2)
        real_question = user_message[match.end():].strip()

        # Đoạn bôi đen sau khi loại watermark/footer -- dùng cho MỌI bước phía dưới
        # (độ dài, so khớp Fast Path, so khớp Slow Path).
        highlighted_text = strip_boilerplate(raw_highlighted_text)

        try:
            reported_idx = int(reported_page) - 1  # UI 1-index -> DB 0-index
        except ValueError:
            reported_idx = None

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

        # 1. FAST PATH: đúng file + đúng index + text thực sự nằm trong trang đó
        if slide_context and norm_highlight and norm_highlight in normalize_text(slide_context):
            final_context = slide_context
            final_page_id = page_key
            mode = "anchored_success"

        # 2. SLOW PATH: chỉ chạy khi text đủ dài (đã trừ boilerplate) để tránh
        #    false positive, và CHỈ scan trong đúng tài liệu đang xem.
        elif len(highlighted_text) >= MIN_LEN_FOR_SLOW_PATH:
            true_page_id, true_context = exact_match_lookup(
                highlighted_text, doc_prefix, near_idx=reported_idx
            )
            if true_context:
                final_context = true_context
                final_page_id = true_page_id
                mode = "anchored_success_corrected"
                print(f"[WARNING] Page Offset Detected! UI reported {reported_page} "
                      f"but text found at {true_page_id} instead.")
            elif slide_context:
                # Lớp 4: không verify được, nhưng page_X hợp lệ trong đúng tài liệu -> vẫn dùng
                final_context = slide_context
                final_page_id = page_key
                unverified_highlight = True
                mode = "anchored_unverified"
            else:
                mode = "anchored_not_found"

        # 3. Text quá ngắn để scan an toàn, nhưng page_X vẫn hợp lệ -> tin tưởng có kiểm soát
        elif slide_context:
            final_context = slide_context
            final_page_id = page_key
            unverified_highlight = True
            mode = "anchored_unverified"

        else:
            mode = "anchored_not_found"

        # 4. Build prompt theo kết quả
        if final_context is not None:
            confidence_note = (
                ""
                if not unverified_highlight
                else "\n(Lưu ý: không xác minh được đoạn bôi đen khớp chính xác trong trang này, "
                     "trả lời thận trọng và có thể nhắc học viên xác nhận lại nếu cần.)"
            )
            prompt = (
                f"Ngữ cảnh Slide:\n{final_context}\n\n"
                f"Đoạn học viên đang chú ý: \"{highlighted_text}\"\n"
                f"Câu hỏi: {real_question}{confidence_note}\n"
                f"Bắt buộc trích dẫn bằng thẻ <citation>{final_page_id}</citation> ở cuối câu trả lời."
            )
            enable_search = True
        else:
            prompt = (
                f"Học viên hỏi: {real_question}. Đoạn bôi đen không tìm thấy trong cơ sở dữ liệu "
                f"(có thể do lỗi phiên bản tài liệu). Trả lời khéo léo yêu cầu làm rõ và tuyệt đối "
                f"không tạo thẻ citation."
            )
            enable_search = False

        llm_response = generate_answer(prompt, enable_search=enable_search)

        response_dict = {
            "mode": mode,
            "detected_page": reported_page,
            "doc_id": request.doc_id,
            "unverified_highlight": unverified_highlight,
            "final_prompt_template": prompt,
        }
        if isinstance(llm_response, dict):
            response_dict.update(llm_response)
        else:
            response_dict["llm_response"] = llm_response

        return response_dict

    else:
        # ==========================================
        # NHÁNH B: UNANCHORED (QDRANT RAG)
        # ==========================================
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

        prompt = f"""Bạn là gia sư AI khóa học. Học viên hỏi: "{user_message}"

[NGỮ CẢNH TỪ LỜI GIẢNG] (Dùng để lấy kiến thức trả lời):
{combined_context}

[THÔNG TIN TRÍCH DẪN]
Slide liên quan nhất: Trang {best_slide_page}

Nhiệm vụ:
1. Trả lời câu hỏi trên dựa vào lời giảng.
2. Nếu ngữ cảnh lời giảng không có thông tin, bạn PHẢI SỬ DỤNG CÔNG CỤ TÌM KIẾM GOOGLE (Google Search) để lấy thông tin mới nhất và trả lời.
3. Nếu sử dụng thông tin từ lời giảng, BẮT BUỘC chèn trích dẫn bằng thẻ <citation>{best_slide_page}</citation> vào cuối câu trả lời. Nếu hoàn toàn dùng kiến thức độc lập (hoặc Google Search), TUYỆT ĐỐI KHÔNG tạo thẻ này."""

        llm_response = generate_answer(prompt, enable_search=True)

        response_dict = {
            "mode": "unanchored_rag",
            "detected_page": best_slide_page,
            "doc_id": request.doc_id,
            "final_prompt_template": prompt,
        }
        if isinstance(llm_response, dict):
            response_dict.update(llm_response)
        else:
            response_dict["llm_response"] = llm_response

        return response_dict


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
