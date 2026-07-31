# AI SPEC — VLearn AI Tutor · Nhóm 01 · Zone 1
Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- **Job executor + workflow:** Học viên đang xem bài giảng / slide, gặp khái niệm khó hiểu và muốn được giải thích ngay tại ngữ cảnh đó.
- **Core JTBD:** "Khi đang xem tài liệu học tập và gặp chỗ không hiểu, tôi muốn được giải thích ngay lập tức dựa trên đúng nội dung bài giảng để không bị đứt mạch học."
- **Problem statement:** Học viên phải tự ra ngoài Google tìm kiếm khái niệm, dẫn đến việc bị sai lệch nội dung so với khoá học, mất tập trung và tốn thời gian đối chiếu.
- **Evidence:** 
  - Số liệu khảo sát: Khảo sát 20 học viên, 85% xác nhận thường xuyên phải tra Google khi gặp từ khoá khó trên slide.
  - Quote: "Nhiều lúc thầy nói lướt qua thuật ngữ, mình phải pause video lại để tìm Google, tìm xong quay lại thì quên mất thầy đang nói gì." (Học viên VLearn)

## §2. Impact & quyết định chọn
- **Bảng impact:**
  - *Ứng viên 1 (Chatbot RAG gắn với slide):* 85% học viên cần, tần suất cao (mỗi bài giảng), tiết kiệm 5-10p tra cứu mỗi lần, khả thi cao.
  - *Ứng viên 2 (Hệ thống tự động tóm tắt bài giảng):* 50% cần, tần suất trung bình, khả thi vừa.
  - *Ứng viên 3 (Quiz tự động):* 60% cần, tần suất cuối mỗi bài, khả thi cao.
- **Ứng viên ĐÃ LOẠI + vì sao:** Loại Tóm tắt và Quiz vì nó không giải quyết trực tiếp "nỗi đau" bị đứt mạch học của học viên khi đang xem slide.
- **Ứng viên CHỌN + vì sao:** Chọn Chatbot RAG (Ứng viên 1). Nó mang lại impact lớn nhất (giải quyết 100% pain-point đứt mạch học) và có thể mở rộng (Knowledge Graph) sau này.

## §3. Giải pháp tương tự đã nghiên cứu
- **ChatGPT / Gemini (Dùng thuần):** Nhanh, thông minh NHƯNG hay bịa (hallucinate) và không bám sát nội dung slide khoá học. (Đáng né)
- **Coursera In-course Coach:** Bám sát bài học, có follow-up questions. Rất đáng học hỏi cách họ hiển thị UI ngay cạnh video mà không che khuất màn hình.

## §4. Thiết kế
- **Lát cắt MỘT CÂU:** Một học viên hỏi về một khái niệm trên slide, AI quyết định dùng RAG (và Google Search nếu cần) để trả về câu trả lời kèm thẻ trích dẫn chính xác và các câu hỏi gợi mở.
- **Non-goals:** Không giải quyết các câu hỏi lạc đề (nấu ăn, thời tiết), không làm hộ bài tập, không thay thế hoàn toàn giảng viên.
- **Mức prototype nhắm tới:** [ ] Sketch [ ] Mock [x] Working — Hoạt động thật bằng API Gemini, kết nối Qdrant Vector DB, phần Knowledge Graph được Mock bằng log file.
- **Automation:** [x] augment [ ] conditional [ ] automate — AI đóng vai trò Augment (Tăng cường) khả năng tự học, quyết định học vẫn nằm ở học viên. Cost-of-error thấp.
- **§4b. Nguyên tắc áp dụng:**
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | Hiển thị nguồn rõ ràng | Các câu trả lời của LLM luôn có thẻ trích dẫn (ví dụ: Trang slide 8) và External links. |
  | Gợi mở tư duy | Cung cấp 2-3 câu `follow_up` (chips) để dẫn dắt học viên hỏi tiếp. |

## §5. Kiểu lỗi — Kịch bản rủi ro
1. Học viên hỏi câu ngoài phạm vi -> Phân loại `SCOPE CLASSIFIER` bắt lỗi và từ chối.
2. AI tự bịa kiến thức -> Ép prompt BẮT BUỘC dùng `<citation>` và RAG context.
3. Không tìm thấy thông tin trong Slide -> Tự động kích hoạt Google Search Grounding để bổ sung.
4. Lỗi API (Rate Limit 429) -> UI hiển thị thông báo lỗi rõ ràng thay vì bong bóng chat trống.

## §6. Bốn đường đi của trải nghiệm
- **Happy path:** Hỏi đúng bài -> AI trả lời bằng Slide + Trích dẫn + External Links + Câu hỏi gợi mở.
- **Low-confidence (②):** Thông tin lờ mờ -> AI báo không chắc và tự Google Search bù đắp.
- **Failure/không căn cứ (①):** Câu hỏi khó, không có slide, không search được -> AI trung thực báo "Không có thông tin trong bài giảng" và mời đặt câu hỏi khác.
- **Khi bị đòi ngoài phạm vi (③):** Đòi làm thơ, hỏi thời tiết -> AI chối lịch sự, mời quay lại bài học.

## §7. Kiểm thử
- **Chiều chất lượng:** Độ chính xác của Trích dẫn (Citation accuracy) và Khả năng chặn lạc đề.
- **Golden set:** 25 câu hỏi (15 câu trong bài, 5 câu lạc đề, 5 câu mưu đồ jailbreak).
- **Quality bar:** Đạt khi ≥ 90% qua bộ, và không có case jailbreak nào thành công.

## §8. Phân công & kế hoạch
- **Nguyễn Văn A (Nhóm trưởng):** Code Backend (RAG, Gemini API), thiết kế kiến trúc Knowledge Graph.
- **Trần Thị B:** Code Frontend (React, giao diện chat, thẻ hover links).
- **Lê Văn C:** Viết Spec, Prompt Engineering (System Prompt, Scope Classifier).
- **Phạm Thị D:** Gom dữ liệu, làm Golden Set (Evidence), chuẩn bị Demo Slides.
- **Willing users (vòng validation):** Bạn X, Bạn Y, Bạn Z.
- **Kế hoạch validation:** Hỏi 3 câu (Tính năng này có giúp bạn hiểu bài hơn không? Thẻ trích dẫn có dễ nhìn không? Nút bấm gợi ý có tiện không?)

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| Hackathon Day 1 | Thêm UI Hover Card cho External Links | UI cũ chiếm diện tích, che slide. |
| Hackathon Day 1 | Bổ sung Mock Knowledge Graph | Mở rộng tính năng phân tích học viên cho Phase 2. |
| Hackathon Day 1 | Bắt lỗi Rate Limit 429 trên UI | Để không bị "bong bóng chat tàng hình". |
