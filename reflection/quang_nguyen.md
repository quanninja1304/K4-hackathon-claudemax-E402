# Báo cáo Trải nghiệm (Reflection) - Nguyễn Phú Quang

**Họ và tên:** Nguyễn Phú Quang
**Mã Học Viên:** 2A202602017
**Vai trò:** Prompt Engineering & Technical Spec Writer

## 1. Những gì tôi đã làm
Trong dự án này, tôi là người "dạy" cho AI cách cư xử và nói chuyện chuẩn mực:
- **Xây dựng System Prompt:** Tôi đã thiết kế bộ lệnh cực kỳ khắt khe yêu cầu AI luôn phải sử dụng thẻ `<citation>` để trích dẫn nguồn từ khóa học, và từ chối trả lời nếu không có bằng chứng.
- **Phát triển Scope Classifier (Lá chắn lạc đề):** Thay vì nhồi nhét mọi thứ vào 1 prompt khổng lồ, tôi đề xuất chia làm 2 bước. Bước 1 dùng một prompt nhỏ gọn, tốc độ cao để phân loại xem câu hỏi có thuộc phạm vi bài giảng không (IN/OUT). Điều này chặn đứng 100% các case Jailbreak và hỏi nhảm.
- **Tối ưu hóa file Spec:** Tôi chịu trách nhiệm quy hoạch và viết bản `spec.md` sao cho mô tả rõ ràng nhất ý đồ thiết kế sản phẩm của nhóm để nộp cho Ban tổ chức.

## 2. Bài học lớn nhất (Lessons Learned)
- **Prompt Engineering không phải là văn mẫu:** Ban đầu tôi viết prompt rất dài kiểu "Mày là một người thầy giáo tận tâm...". Nhưng AI hay bịa (Hallucinate). Bài học rút ra là: Thay vì bảo AI phải làm gì, hãy chỉ cho nó **những gì tuyệt đối không được làm**. Càng giới hạn chặt chẽ (Constraints), AI chạy càng ổn định.
- **Chia nhỏ bài toán (Chain of Prompts):** Dùng 1 prompt to xử lý cả phân loại + tìm kiếm + sinh câu trả lời thường xuyên bị quá tải ngữ cảnh. Việc đẻ ra Scope Classifier chạy độc lập là quyết định sáng suốt nhất của nhóm.

## 3. Nếu có thêm thời gian, tôi sẽ làm gì?
Tôi sẽ tối ưu thêm cơ chế Multi-turn (Nhớ ngữ cảnh chat cũ). Hiện tại prompt đang xử lý rất tốt các câu hỏi Single-turn, nhưng nếu học sinh chat liên tiếp 4-5 câu, prompt cần được thiết kế lại để giữ được luồng hội thoại mượt mà hơn.
