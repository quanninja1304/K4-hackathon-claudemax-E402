# Báo cáo Trải nghiệm (Reflection) - Trần Tuấn Linh

**Họ và tên:** Trần Tuấn Linh
**Mã Học Viên:** 2A2026001612
**Vai trò:** Eval, Validation & Pitch Deck

## 1. Những gì tôi đã làm
Sản phẩm làm ra phải có người kiểm chứng, và đó là nhiệm vụ của tôi:
- **Xây dựng Golden Set:** Tôi đã lọc từ data thô của VLearn để xây dựng 25 câu hỏi test (Evidence). Không chỉ là các câu hỏi "Happy Path", tôi cố tình đưa vào 5 câu lạc đề và 5 câu mài dũa (mưu đồ lừa AI nói sai) để test giới hạn của hệ thống.
- **Đo lường Quality Bar:** Tôi đã trực tiếp cầm file Golden Set để chat thử với hệ thống, ghi nhận tỷ lệ Pass > 90% đúng như Spec đã cam kết.
- **Chuẩn bị Pitch Deck & Validation:** Tôi đã tham gia kịch bản thuyết trình, tổng hợp báo cáo chi tiết và lấy feedback từ một số user thử nghiệm (Validation) để hoàn thiện luồng UX.

## 2. Bài học lớn nhất (Lessons Learned)
- **Edge Cases quan trọng hơn Happy Path:** Khi làm sản phẩm AI, việc AI trả lời đúng một câu bình thường rất dễ. Cái khó nhất là dạy AI biết nói câu *"Tôi không biết"* khi thông tin không có thật. Quá trình làm Golden Set giúp tôi thấm thía giá trị của việc test các ca "khó đỡ".
- **Giá trị của dữ liệu thật:** Ban đầu nhóm định tự nghĩ ra câu hỏi để test. Nhưng khi nhìn vào Log chat thật của VLearn, tôi mới thấy học viên hỏi rất nhiều câu ngô nghê và sai chính tả. Đưa dữ liệu thật vào test giúp sản phẩm sát với thực tế hơn rất nhiều.

## 3. Nếu có thêm thời gian, tôi sẽ làm gì?
Hiện tại tôi đang phải test thủ công 25 câu hỏi bằng cách gõ tay và đọc bằng mắt. Nếu có Phase 2, tôi sẽ ứng dụng mô hình **LLM-as-a-judge**, dùng một con AI khác để tự động chấm điểm độ chính xác (Accuracy) và độ ảo giác (Hallucination) của con Bot hiện tại.
