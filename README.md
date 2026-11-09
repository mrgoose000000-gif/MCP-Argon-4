# 🚀 MCP-Argon-4 — Cầu Nối Google Gemini 4 (Argon) Với Antigravity IDE

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://www.python.org/)
[![Antigravity](https://img.shields.io/badge/Antigravity-IDE%20%7C%20App%20%7C%20CLI-purple.svg)](https://antigravity.google)
[![Gemini](https://img.shields.io/badge/Gemini%20Web-Gemini%204%20Argon-orange.svg)](https://gemini.google.com/app)

Đưa sức mạnh mô hình **Google Gemini 4 High (Gemini 4 Argon kèm Extended Thinking suy luận sâu cao nhất)** từ tài khoản [Google Gemini Web](https://gemini.google.com/app) vào trực tiếp hệ sinh thái **Google Antigravity IDE**.

Tích hợp sẵn:
- 📊 **Visual Dashboard (Bảng điều khiển trực quan)** quản lý danh sách tài khoản & quota.
- ⚡ **Multi-Account Pool & Auto-Failover**: Tự động xoay vòng tài khoản khi tài khoản hiện tại hết quota.
- 🛡️ **Self-Healing Cookie**: Tự động trích xuất và làm mới cookie từ trình duyệt khi phiên đăng nhập hết hạn.
- 💬 **Lệnh Slash `/kg4`**: Chỉ cần gõ `/kg4 <câu hỏi>`, Antigravity tự động kích hoạt Gemini 4 High trả lời ngay lập tức.

---

## 🤖 Cách Cài Đặt Dễ Nhất: Nhờ AI Cài Đặt Tự Động (1 Prompt)

Nếu bạn chia sẻ repo này cho bạn bè, bạn của bạn **chỉ cần copy dòng bên dưới và dán vào khung chat của Antigravity IDE**:

> *"Hãy clone repository https://github.com/mrgoose000000-gif/MCP-Argon-4 về máy và chạy script `python3 install.py` để tự động cài đặt MCP Server `gemini-web` và Skill `/kg4` cho tôi."*

AI Agent trong Antigravity sẽ tự động đọc `install.py`, cài đặt thư viện và đăng ký toàn bộ vào hệ thống mà không cần làm thủ công!

---

## 🛠️ Hướng Dẫn Cài Đặt Thủ Công

### Bước 1: Clone Repository
```bash
git clone https://github.com/mrgoose000000-gif/MCP-Argon-4.git
cd MCP-Argon-4
```

### Bước 2: Chạy bộ cài đặt tự động (1-Click Auto-Installer)
```bash
# Trên macOS / Linux:
python3 install.py

# Trên Windows:
python install.py
```
*Script sẽ tự động tạo môi trường ảo `.venv`, cài đặt thư viện, đăng ký MCP Server vào `~/.gemini/config/mcp_config.json` và cài đặt Skill `/kg4`.*

### Bước 3: Mở Dashboard nạp tài khoản
- **macOS / Linux:**
  ```bash
  ./mo_bang_dieu_khien.sh
  ```
- **Windows:** Nhấp đúp vào `mo_bang_dieu_khien.bat` (hoặc chạy trong CMD/PowerShell).
- Trình duyệt sẽ mở **Bảng Điều Khiển Quản Lý Tài Khoản** tại: `http://127.0.0.1:8000/dashboard`
  - Bấm **"Quét Trình Duyệt"** nếu bạn đã đăng nhập sẵn tài khoản Google trên Chrome/Edge.
  - Hoặc bấm **"Thêm Tài Khoản"** để dán cookie (`__Secure-1PSID` và `__Secure-1PSIDTS`).
  - Bạn có thể thêm 2, 3 hoặc nhiều tài khoản tùy thích — hệ thống sẽ tự động chuyển tài khoản khi hết quota!

---

## 🎯 Cách Sử Dụng Trong Antigravity IDE

Sau khi cài đặt xong, khởi động lại **Antigravity IDE**.

Trong khung chat bất kỳ, bạn chỉ cần gõ tiền tố **`/kg4`**:

```text
/kg4 hãy viết hàm Python crawl dữ liệu phân tích thị trường
```
hoặc:
```text
/kg4 giải thích đoạn code kiến trúc này
```

Antigravity sẽ tự động kích hoạt **Google Gemini 4 Argon** thông qua MCP Server nội bộ với chế độ suy luận sâu nhất.

---

## 🌟 Các Tính Năng Nổi Bật

### 1. Multi-Account Pool & Tự Động Xoay Vòng (Auto-Failover)
- Quản lý đồng thời nhiều tài khoản Google Gemini (tài khoản Free 600 credits/5h, tài khoản Google One AI Premium 2400 credits/5h).
- Khi tài khoản đang dùng hết quota, hệ thống tự động tìm tài khoản còn quota trong pool và tiếp tục trả lời mà không làm gián đoạn công việc của bạn.

### 2. Tự Động Làm Mới Cookie (Self-Healing)
- Google Gemini Web thường xuyên làm mới token `__Secure-1PSIDTS`.
- Khi phát hiện cookie hết hạn, hệ thống tự động kích hoạt thư viện `rookiepy` đọc phiên mới nhất từ Chrome cục bộ và cập nhật lại pool ngay lập tức mà không cần bạn phải thao tác lại bằng tay.

### 3. Visual Dashboard Hiện Đại (FastAPI + Dark UI)
- Theo dõi quota theo chu kỳ 5 giờ của từng tài khoản.
- Nút kiểm tra quota đơn lẻ hoặc kiểm tra toàn bộ chỉ với 1 click.
- Nút Bật/Tắt Auto-Failover linh hoạt.

---

## 🔒 Bảo Mật & Quyền Riêng Tư
- **Dữ liệu cục bộ 100%:** Toàn bộ cookie và token được lưu trữ tại file cục bộ `accounts.json` trên máy tính của bạn (đã được đưa vào `.gitignore`, không bao giờ bị đẩy lên GitHub).
- Không chia sẻ hay gửi cookie đến bất kỳ bên thứ ba nào ngoại trừ trực tiếp đến máy chủ Google Gemini Web.

---

## 📄 Bản Quyền
Phát hành theo giấy phép [MIT License](LICENSE).
Tự do chia sẻ, sử dụng và đóng góp cho cộng đồng!
