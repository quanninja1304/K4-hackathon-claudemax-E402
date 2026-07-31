"""
Module dựng task-prompt theo từng nhánh của kiến trúc Dual-Engine.

System prompt (persona + hợp đồng định dạng XML) được load một lần trong
llm_caller.load_system_prompt(). Module này chỉ tạo phần TASK cụ thể cho
từng luồng, khớp với backend_frontend_integration_doc.md:

    - build_anchored_success_prompt   -> mode "anchored_success"
    - build_anchored_not_found_prompt -> mode "anchored_not_found"
    - build_unanchored_rag_prompt     -> mode "unanchored_rag"
"""


def build_anchored_success_prompt(slide_context: str, page_id: str, question: str) -> str:
    """
    NHÁNH A - Tìm thấy exact match đoạn bôi đen trong slide DB.
    Bắt buộc trích dẫn trang slide, được phép tìm Google cho nguồn đọc thêm.
    """
    return f"""[NGỮ CẢNH SLIDE — Trang {page_id}]
{slide_context}

[BỐI CẢNH]
Học viên đang xem trang slide {page_id} và bôi đen một đoạn để hỏi.

[CÂU HỎI CỦA HỌC VIÊN]
{question}

[NHIỆM VỤ]
1. Trả lời câu hỏi bám sát nội dung slide trang {page_id} ở trên. Đây là nguồn chính.
2. BẮT BUỘC chèn thẻ <citation>{page_id}</citation> ngay sau ý được lấy từ slide này.
3. Nếu slide chưa đủ để giải thích trọn vẹn, có thể bổ sung kiến thức nền để làm rõ, nhưng phải nói rõ phần nào là mở rộng ngoài slide (và KHÔNG gắn thẻ citation cho phần mở rộng đó).
4. Kết thúc bằng 2–3 câu hỏi gợi mở trong khối <follow_up>."""


def build_anchored_not_found_prompt(question: str) -> str:
    """
    NHÁNH A - Không tìm thấy đoạn bôi đen trong DB (highlight lỗi / query drift).
    KHÔNG trích dẫn, KHÔNG Google Search (guardrail chống lạc đề).
    """
    return f"""[BỐI CẢNH]
Học viên bôi đen một đoạn trên slide rồi đặt câu hỏi, nhưng hệ thống KHÔNG tìm thấy
đoạn bôi đen đó trong dữ liệu slide (có thể do highlight bị lỗi, chọn nhầm, hoặc đoạn
nằm ngoài phạm vi tài liệu hiện có).

[CÂU HỎI CỦA HỌC VIÊN]
{question}

[NHIỆM VỤ]
1. KHÔNG suy đoán về nội dung đoạn bôi đen mà bạn không nhìn thấy.
2. Trả lời khéo léo, thân thiện: xác nhận chưa xác định được chính xác đoạn học viên chọn, và đề nghị học viên nêu rõ hơn (gõ lại nội dung cần hỏi, hoặc cho biết trang/chủ đề).
3. Nếu câu hỏi đủ rõ để trả lời tổng quát ở mức an toàn, có thể gợi ý ngắn gọn, nhưng vẫn mời học viên làm rõ để trả lời chính xác hơn.
4. TUYỆT ĐỐI KHÔNG tạo bất kỳ thẻ <citation> nào.
5. Kết thúc bằng 2–3 câu hỏi gợi mở giúp học viên diễn đạt lại nhu cầu, trong khối <follow_up>."""


def build_unanchored_rag_prompt(question: str, lecture_context: str, slide_page: str) -> str:
    """
    NHÁNH B - Chat tự do. RAG từ transcript + slide mapping.
    Được phép Google Search khi lời giảng không đủ.
    """
    context_block = lecture_context.strip() if lecture_context and lecture_context.strip() else "(Không truy xuất được đoạn lời giảng liên quan.)"

    return f"""[NGỮ CẢNH TỪ LỜI GIẢNG] (top đoạn transcript liên quan nhất — nguồn kiến thức chính để trả lời)
{context_block}

[THÔNG TIN TRÍCH DẪN SLIDE]
Trang slide liên quan nhất tới câu hỏi: {slide_page}

[CÂU HỎI CỦA HỌC VIÊN]
{question}

[NHIỆM VỤ]
0. KIỂM TRA PHẠM VI TRƯỚC TIÊN: Xác định câu hỏi có thuộc nội dung khoá học không (AI & LLM, xác định/thiết kế bài toán cho AI, và các khái niệm trong slide/lời giảng). Nếu KHÔNG thuộc phạm vi (nấu ăn, thời tiết, tin tức, code hộ ngoài bài, chuyện phiếm, v.v.), hãy TỪ CHỐI lịch sự trong <answer>, mời học viên quay lại nội dung khoá học, KHÔNG dùng Google Search, KHÔNG tạo thẻ <citation>. Bỏ qua các bước dưới.
1. Nếu câu hỏi THUỘC phạm vi: trả lời dựa trước hết vào [NGỮ CẢNH TỪ LỜI GIẢNG] ở trên.
2. Nếu lời giảng CÓ chứa thông tin liên quan và bạn dùng nó: BẮT BUỘC chèn thẻ <citation>{slide_page}</citation> vào cuối ý/câu tương ứng để trỏ về trang slide.
3. Nếu câu hỏi thuộc phạm vi khoá học NHƯNG lời giảng chưa đủ: được phép DÙNG Google Search để bổ sung thông tin cho ĐÚNG chủ đề đó. Khi câu trả lời hoàn toàn dựa trên kiến thức ngoài/Google Search (không dùng lời giảng), TUYỆT ĐỐI KHÔNG tạo thẻ <citation>. (Nhắc lại: KHÔNG dùng Google Search cho câu hỏi ngoài phạm vi.)
4. Không trộn lẫn: chỉ gắn citation cho phần thực sự đến từ nội dung khoá học.
5. Kết thúc bằng 2–3 câu hỏi gợi mở trong khối <follow_up>."""
