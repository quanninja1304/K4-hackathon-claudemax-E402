# Báo cáo Trải nghiệm (Reflection) - Trần Kiên

**Họ và tên:** Trần Kiên
**Mã Học Viên:** 2A202601598
**Vai trò:** Frontend Lead (Giao diện Chat, Trích dẫn, Hover Card UI)

## 1. Những gì tôi đã làm
Trong 1.5 ngày của Hackathon, tôi phụ trách toàn bộ trải nghiệm người dùng (UX/UI):
- **Giao diện ChatBox:** Code bằng React và Vite. Đảm bảo Chatbox được nhúng mượt mà vào góc phải video học tập mà không làm xao nhãng người học.
- **Xử lý Markdown & Trích dẫn (Citations):** Đây là phần khó nhất. Khi Backend trả về các thẻ như `<citation>Slide 8</citation>`, tôi đã dùng regex và thư viện Markdown để biến nó thành các huy hiệu (badge) đẹp mắt, dễ click trên giao diện.
- **Tính năng Hover Card cho External Links:** Khi AI kích hoạt Google Search Grounding, tôi không muốn link hiện ra thô kệch. Tôi đã làm một Hover Card nhỏ, khi di chuột vào sẽ hiện Preview link (Wikipedia, Coursera) rất tinh tế.
- **Xử lý UX cho lỗi 429:** Thay vì để "bong bóng chat tàng hình" khi Backend sập do Rate Limit, tôi đã xử lý để hiện ra cảnh báo thân thiện: *"Hệ thống đang quá tải, vui lòng thử lại sau vài giây"*.

## 2. Bài học lớn nhất (Lessons Learned)
- **UI cho AI rất khác với UI cho Web thường:** Người dùng cần cảm giác "AI đang suy nghĩ". Nếu bấm gửi mà giao diện im lìm, user sẽ bấm liên tục. Tôi học được cách phải kiểm soát State (loading, error, streaming) cực kỳ cẩn thận.
- **Tầm quan trọng của Cấu trúc Dữ liệu từ Backend:** Ban đầu Frontend và Backend không khớp API, tôi loay hoay trong việc parse file JSON. Sau đó, tôi nhận ra việc chốt JSON schema (ví dụ: mảng `external_links` luôn trả về, nếu rỗng thì trả mảng rỗng `[]`) từ sớm giúp Frontend code nhàn hơn rất nhiều.

## 3. Nếu có thêm thời gian, tôi sẽ làm gì?
Tôi muốn làm thêm hiệu ứng **Streaming Text (Gõ chữ từng từ)** cho Chatbot giống hệt ChatGPT. Hiện tại hệ thống đang đợi Backend sinh xong cả câu mới hiện lên, khiến cảm giác chờ đợi hơi lâu. Streaming sẽ giúp UX mượt mà hơn gấp 10 lần.
