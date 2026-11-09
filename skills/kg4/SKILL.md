---
name: kg4
description: Kích hoạt Google Gemini 4 High (Gemini 4 Argon kèm Extended Thinking) từ Google Gemini Web qua MCP gemini-web trong vai trò Supreme Supervisor (Giám sát viên & Cố vấn tối cao), cầm tay chỉ việc và kiểm soát toàn bộ kế hoạch, mã nguồn, hành động thực thi của Antigravity Agent.
---

# Lệnh /kg4 — Argon 4 Supreme Supervisor & Co-Pilot Protocol

Kỹ năng này thiết lập mô hình **Dual-Agent khép kín**:
- **Gemini 4 Argon (Web / Cloud):** Đóng vai trò **Người Giám Sát Tối Cao (Supreme Supervisor) & Kiến Trúc Sư Trưởng**. Nắm quyền chỉ đạo chiến lược, suy luận sâu (Extended Thinking), phê duyệt từng phương án, bắt lỗi edge cases, và kiểm duyệt mã nguồn.
- **Antigravity Agent (Local):** Đóng vai trò **Kỹ Sư Thi Công Cục Bộ (Local Executor / Field Engineer)**. Chịu trách nhiệm tương tác môi trường, thao tác tệp tin, chạy lệnh shell và báo cáo phản hồi thực tế lên Argon 4.

---

## ⚡ Nguyên Tắc Xử Lý Bắt Buộc (Mandatory Rules)

### 1. Khi là câu hỏi / tham vấn logic thông thường:
- Gọi tool `gemini_web_ask` (Server: `gemini-web`):
  - `prompt`: Nội dung câu hỏi của người dùng.
  - `model`: `"gemini-4"` (đảm bảo gọi đúng Gemini 4 Argon).
  - `extended_thinking`: `True` (luôn kích hoạt chế độ **Gemini 4 High** suy luận sâu cao nhất).
- Trả lời trực tiếp và đầy đủ nội dung nhận được từ Gemini 4 High.

---

### 2. Khi là tác vụ Lập Trình / Kỹ Thuật / Thực Thi Hệ Thống (Hand-Holding Protocol):
Antigravity Agent **TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ Ý HÀNH ĐỘNG CẢM TÍNH**, mà phải tuân thủ nghiêm ngặt chu trình 4 bước giám sát khép kín:

#### Bước 1: Xin Chỉ Đạo & Kiến Trúc Gốc từ Argon 4 (Strategic Blueprint)
- Gửi toàn bộ yêu cầu dự án và ngữ cảnh sang Argon 4 qua `gemini_web_ask` (với `model: "gemini-4"`, `extended_thinking: true`).
- Yêu cầu Argon 4 vạch ra: Kiến trúc chuẩn mực, danh sách file cần tạo/sửa, logic thuật toán chi tiết và các edge cases bắt buộc phải xử lý.

#### Bước 2: Đệ Trình Kế Hoạch & Mã Nguồn Lên Argon 4 Trước Khi Chạy (Pre-Execution Audit)
- Trước khi ghi đè code phức tạp hoặc chạy các lệnh hệ thống nhạy cảm:
  - Antigravity soạn thảo giải pháp/diff code dự kiến.
  - Tham vấn Argon 4 kiểm duyệt tính an toàn, hiệu năng, bảo mật và logic chống lỗi.
  - Chỉ khi Argon 4 phê chuẩn thì mới tiến hành thao tác trên môi trường local.

#### Bước 3: Thực Thi & Gửi Phản Hồi Ngược Lại (Execution & Continuous Feedback Loop)
- Antigravity thực thi việc tạo file, ghi code, hoặc chạy lệnh terminal trên máy người dùng.
- Thu thập kết quả thực thi thực tế (terminal stdout, stderr, mã thoát exit code, kết quả test).
- Nếu phát sinh lỗi hoặc kết quả chưa đạt: Chuyển toàn bộ output log ngược về cho Argon 4 để phân tích nguyên nhân gốc rễ và nhận lệnh sửa đổi tiếp theo.

#### Bước 4: Nghiệm Thu Hoàn Thiện (Final Sign-off)
- Báo cáo kết quả hoàn thành với người dùng, làm rõ các điểm đã được Argon 4 trực tiếp giám sát, kiểm duyệt và phê chuẩn.
