---
name: kg4
description: Gọi trực tiếp mô hình Google Gemini 4 (Gemini 4 Argon) từ Google Gemini Web qua MCP gemini-web để giải quyết bài toán hoặc trả lời trực tiếp.
version: 1.0.0
---

# /kg4 - Trò Chuyện & Thực Thi Trực Tiếp Với Gemini 4 Argon (Gemini Web)

$ARGUMENTS

---

## 🎯 Mục Đích
Kích hoạt trực tiếp mô hình **Google Gemini 4 (Gemini 4 Argon)** từ tài khoản Google Gemini Web cá nhân thông qua MCP Server `gemini-web`.

---

## ⚡ Quy Tắc Bắt Buộc (Mandatory Rules)

1. **Trích xuất nội dung (Query Extraction):**
   - Lấy toàn bộ phần câu hỏi hoặc yêu cầu sau lệnh `/kg4` từ biến `$ARGUMENTS`.
   - Nếu `$ARGUMENTS` để trống: Hỏi lại người dùng: *"Bạn muốn Gemini 4 phân tích hoặc giải quyết bài toán gì?"*.

2. **Gọi MCP Tool Trực Tiếp:**
   - Agent **BẮT BUỘC** gọi tool `gemini_web_ask` (Server: `gemini-web`):
     - `prompt`: Nội dung câu hỏi/yêu cầu từ `$ARGUMENTS`.
     - `model`: `"gemini-4"` (đảm bảo gọi đúng Gemini 4 Argon).
     - `extended_thinking`: `false` (hoặc `true` nếu người dùng yêu cầu deep reasoning / suy nghĩ chuyên sâu).

3. **Phản hồi trực tiếp (Direct Response):**
   - Trả lời trực tiếp và trọn vẹn kết quả nhận được từ Gemini 4.
   - Không cần thêm lời dẫn giải thích trung gian rườm rà.

---

## 💡 Ví Dụ Sử Dụng (Usage Examples)

```
/kg4 xin chào, bạn là ai và phiên bản nào?
/kg4 viết script python tự động hóa crawl dữ liệu
/kg4 phân tích thiết kế hệ thống microservices tối ưu
/kg4 giải thích đoạn code này giúp tôi
```
