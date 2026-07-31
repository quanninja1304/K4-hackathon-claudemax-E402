# Báo cáo Trải nghiệm (Reflection) - Nguyễn Đại Quân

**Họ và tên:** Nguyễn Đại Quân
**Mã Học Viên:** 2A202601933
**Vai trò:** Backend Lead (Xây dựng RAG, API, Knowledge Graph)

## 1. Những gì tôi đã làm
Trong Hackathon lần này, tôi chịu trách nhiệm chính về mảng Backend và luồng dữ liệu AI:
- **Xây dựng kiến trúc Dual-mode RAG:** Tôi đã tách bạch luồng xử lý `Anchored` (dựa trên slide cụ thể được bôi đen) và `Unanchored` (hỏi tự do). Quyết định này giúp hệ thống phản hồi cực nhanh khi có ngữ cảnh cụ thể mà không phải tốn thời gian search Vector DB.
- **Tích hợp Qdrant & Gemini API:** Thiết lập kết nối ổn định giữa Qdrant để lưu trữ transcript và Gemini 2.5 Flash để sinh câu trả lời.
- **Tính năng mở rộng - Mock Knowledge Graph:** Tôi đã viết một Background Task chạy ngầm trên FastAPI. Mỗi khi học sinh hỏi, hệ thống sẽ log lại thành các Graph Edges (User - Asked -> Question -> On_Slide). Dù hiện tại chỉ là file `.jsonl` giả lập, nó chứng minh tính khả thi cho Phase 2 của dự án.

## 2. Bài học lớn nhất (Lessons Learned)
- **RAG không phải là "Chén thánh":** Ban đầu tôi nghĩ cứ ném toàn bộ PDF vào Vector DB là AI tự hiểu. Nhưng qua quá trình test, tôi nhận ra Vector Search rất hay bị nhiễu. Bài học rút ra là phải kết hợp thuật toán truyền thống (Token-overlap) với Semantic Search để nội suy chính xác trang slide.
- **Quản lý Rate Limit:** Tôi nhận ra khi đẩy app lên môi trường thực tế, Gemini bị lỗi 429 (Too Many Requests) liên tục nếu call liên tiếp. Bài học là phải xây dựng cơ chế Handle Exception ở Backend và trả về mã lỗi rõ ràng cho Frontend xử lý.

## 3. Nếu có thêm thời gian, tôi sẽ làm gì?
Tôi sẽ chuyển file `knowledge_graph_mock.jsonl` thành dữ liệu thật bắn thẳng vào Neo4j Database. Từ đó, tôi muốn viết một API `/analytics` để vẽ biểu đồ trực tiếp (Dashboard) cho Giảng viên xem sinh viên đang học yếu ở phần nào.
