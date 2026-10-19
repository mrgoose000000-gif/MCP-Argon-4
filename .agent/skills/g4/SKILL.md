---
name: g4
description: Kích hoạt trực tiếp mô hình Google Gemini 4 (Gemini 4 Argon) từ Google Gemini Web qua MCP gemini-web. Tự động kích hoạt khi người dùng gõ /g4 [câu hỏi], g4 [câu hỏi], hoặc muốn Gemini 4 trực tiếp giải quyết vấn đề mà không cần viết lời dẫn rườm rà.
---

# Lệnh /g4 — Kích Hoạt Nhanh Mô Hình Google Gemini 4 Argon

Kỹ năng này cho phép Antigravity tự động kết nối và ủy quyền cho **Google Gemini 4 (Gemini 4 Argon)** từ Google Gemini Web khi người dùng gõ lệnh rút gọn `/g4`.

## ⚡ Nguyên Tắc Xử Lý Bắt Buộc (Mandatory Rules)

1. **Trích xuất nội dung (Query Extraction):**
   - Lấy toàn bộ phần nội dung đứng sau tiền tố `/g4`, `"""/g4"""`, hoặc `g4:`.
   - Ví dụ: `/g4 viết script python crawl dữ liệu` ➔ Nội dung gửi đi: `viết script python crawl dữ liệu`.
   - Nếu người dùng chỉ gõ `/g4` mà không có nội dung đi kèm: Hãy hỏi nhanh: *"Bạn muốn Gemini 4 giải quyết bài toán hay phân tích nội dung gì?"*.

2. **Gọi Tool MCP Trực Tiếp:**
   - Agent **BẮT BUỘC** gọi tool `gemini_web_ask` (Server: `gemini-web`):
     - `prompt`: Nội dung câu hỏi của người dùng.
     - `model`: `"gemini-4"` (đảm bảo gọi đúng Gemini 4 Argon).
     - `extended_thinking`: `False` (hoặc `True` nếu người dùng yêu cầu suy nghĩ chuyên sâu/deep reasoning).

3. **Phong cách phản hồi (Direct Response):**
   - Trả lời trực tiếp và đầy đủ nội dung nhận được từ Gemini 4.
   - Tuyệt đối KHÔNG cần phải thêm các câu rào đón dài dòng (như *"Tôi đã chuyển câu hỏi đến Gemini Web..."*, *"Dưới đây là câu trả lời của Gemini 4..."*), trừ khi người dùng yêu cầu đối chiếu so sánh.
