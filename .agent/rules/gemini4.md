# Quy Tắc Tích Hợp Model Gemini 4 Từ Gemini Web

## Mô tả
Quy tắc hướng dẫn Agent tự động sử dụng mô hình **Gemini 4 (Gemini 4 Argon)** từ Google Gemini Web ([gemini.google.com/app](https://gemini.google.com/app)) thông qua MCP server `gemini-web`.

## Chỉ dẫn cho Agent:
- Khi người dùng yêu cầu hỏi, đối chiếu hoặc sử dụng Gemini từ Gemini Web, luôn ưu tiên sử dụng tool `gemini_web_ask` hoặc `gemini_web_chat`.
- Model mặc định đã được thiết lập là **`gemini-4`**.
- Không cần cấu hình hay truyền tham số model thủ công vì hệ thống đã tự động định tuyến sang Gemini 4 Argon.
- **Lệnh rút gọn `/kg4` và `/g4`:** Khi người dùng bắt đầu câu bằng `/kg4 <câu hỏi>` hoặc `/g4 <câu hỏi>`, Agent ngay lập tức gọi `gemini_web_ask(prompt=câu_hỏi, model="gemini-4")` và phản hồi trực tiếp kết quả từ Gemini 4 mà không cần các câu dẫn giải rườm rà.

