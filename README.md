# 🚀 geminiweb2antigravity — Cầu Nối Google Gemini 4 (Argon) Với Antigravity

[![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://www.python.org/)
[![Antigravity](https://img.shields.io/badge/Antigravity-IDE%20%7C%20App%20%7C%20CLI-purple.svg)](https://antigravity.google)
[![Gemini](https://img.shields.io/badge/Gemini%20Web-Gemini%204%20Argon-orange.svg)](https://gemini.google.com/app)

Đưa sức mạnh mô hình **Google Gemini 4 (Gemini 4 Argon)** từ tài khoản [Google Gemini Web](https://gemini.google.com/app) vào trực tiếp hệ sinh thái **Google Antigravity** (bao gồm **Antigravity IDE**, **Antigravity Desktop App 2.0**, và **Antigravity CLI `agy`**).

Chỉ với **1 cú click chuột**, hệ thống tự động nhận diện tài khoản, cấu hình MCP Server và kích hoạt lệnh slash command **`/kg4`** để bạn trò chuyện, lập trình và suy luận cùng Gemini 4 ở bất cứ đâu!

---

## 🌟 Điểm Nổi Bật

- ⚡ **1-Click Tự Động Kết Nối**: Bấm `ket_noi_gemini_antigravity.bat` (Windows) hoặc chạy `./ket_noi_gemini_antigravity.sh` (Linux/macOS) — Tự động cài đặt thư viện, quét cookie và đăng ký toàn diện.
- 🧠 **Mô hình Gemini 4 High (Argon Extended Thinking)**: Luôn mặc định kích hoạt chế độ suy luận mở rộng (Extended Thinking / High Reasoning) đỉnh cao nhất từ Google Gemini Web, phân tích code và giải quyết bài toán phức tạp vượt trội.
- 💬 **Lệnh Slash `/kg4`**: Trong bất kỳ khung chat nào của Antigravity, chỉ cần gõ `/kg4 <câu hỏi>` là Gemini 4 High lập tức phản hồi mà không cần thiết lập phức tạp.
- 🍪 **Zero-Config Live Cookie**: Tự động đồng bộ cookie phiên làm việc từ trình duyệt **Microsoft Edge**, **Google Chrome**, **Mozilla Firefox**, **Brave**, **Opera** — Không lo hết hạn token.
- 🌐 **Đa nền tảng, linh hoạt thư mục**: Chạy mượt mà trên Windows, macOS, Linux, đặt repo ở bất kỳ thư mục hay ổ đĩa nào đều tự động nhận diện đường dẫn động 100%.
- 🔌 **Tích hợp kép**:
  - **Native MCP Server**: Cung cấp các tools: `gemini_web_ask`, `gemini_web_chat`, `gemini_web_deep_research`, `gemini_web_account_info` (mặc định luôn chạy Gemini 4 High).
  - **OpenAI-Compatible Proxy**: Hỗ trợ endpoint `/v1/chat/completions` (Streaming & Non-streaming) tại `http://127.0.0.1:8000/v1`.


---

## 🚀 Hướng Dẫn Cài Đặt Nhanh (Dành Cho Mọi Người)

### Bước 1: Chuẩn bị trình duyệt
Mở trình duyệt bất kỳ (**Microsoft Edge**, **Chrome** hoặc **Firefox**) và đảm bảo bạn đã đăng nhập vào tài khoản [https://gemini.google.com/app](https://gemini.google.com/app).

### Bước 2: Tải repository về máy
```bash
git clone https://github.com/duykhanhbv-bit/geminiweb2antigravity.git
cd geminiweb2antigravity

```
*(Hoặc tải file ZIP từ GitHub và giải nén vào bất kỳ thư mục nào trên máy tính).*

### Bước 3: Chạy cài đặt 1-Click

#### 🪟 Trên Windows:
> **Click đúp (Double-click)** vào file:
> ```cmd
> ket_noi_gemini_antigravity.bat
> ```

#### 🍎 Trên macOS / 🐧 Linux:
Mở Terminal tại thư mục dự án và chạy:
```bash
chmod +x ket_noi_gemini_antigravity.sh
./ket_noi_gemini_antigravity.sh
```

#### 🐍 Hoặc chạy trực tiếp bằng Python (Mọi hệ điều hành):
```bash
python install_gemini_antigravity.py
```

---

## 🎯 Cách Sử Dụng Trong Antigravity

Sau khi chạy bộ cài xong, hãy mở **Antigravity IDE**, **Desktop App** hoặc **agy CLI**, tại khung chat bạn chỉ cần gõ:

```
/kg4 <nội dung câu hỏi hoặc yêu cầu cần thực hiện>
```

### Ví Dụ Thực Tế:
- `/kg4 Xin chào, bạn là model nào và có thế mạnh gì?`
- `/kg4 Viết cho tôi một module microservices bằng Python FastAPI kèm Dockerfile`
- `/kg4 Tối ưu hóa thuật toán sau đây giúp tôi`
- `/kg4 Phân tích cấu trúc thư mục của dự án này`

---

## 🛠️ Các Lệnh Bổ Trợ Dòng Lệnh (CLI)

Bộ công cụ `gemini2anti` cung cấp giao diện CLI quản trị mạnh mẽ:

| Lệnh CLI | Mô tả |
| :--- | :--- |
| `python gemini2anti.py check` | Kiểm tra trạng thái cookie, số credits còn lại và quota Gemini 4 |
| `python gemini2anti.py export-env` | Tự động xuất cookie trình duyệt ra file cấu hình `.env` |
| `python gemini2anti.py install-mcp` | Đăng ký lại MCP Server vào Antigravity |
| `python gemini2anti.py chat` | Trò chuyện trực tiếp với Gemini 4 trên Terminal |
| `python gemini2anti.py serve --port 8000` | Khởi chạy OpenAI-compatible API Proxy tại port 8000 |

---

## 📁 Cấu Trúc Thư Mục Repository

```text
gemini2anti/
├── ket_noi_gemini_antigravity.bat   # Bộ chạy 1-Click tự động cho Windows
├── ket_noi_gemini_antigravity.sh    # Bộ chạy 1-Click tự động cho Linux / macOS
├── install_gemini_antigravity.py    # Engine cài đặt tự động đa nền tảng
├── run_mcp.py                       # Điểm khởi chạy MCP Server cho Antigravity
├── run_proxy.py                     # Điểm khởi chạy OpenAI Proxy Server
├── gemini2anti.py                   # Trình điều khiển CLI quản trị
├── requirements.txt                 # Danh sách thư viện phụ thuộc
├── .env.example                     # Mẫu cấu hình môi trường tùy chọn
├── .gitignore                       # Bảo mật tuyệt đối cookie/token người dùng
├── workflows/                       # File định nghĩa Slash Command toàn cục
│   └── kg4.md                       # Lệnh /kg4
├── skills/                          # File kỹ năng Agent Antigravity
│   └── kg4/SKILL.md
└── gemini2anti/                     # Source code cốt lõi
    ├── client.py                    # Cầu nối phân giải model Gemini 4 Argon
    ├── config.py                    # Module quét cookie tự động từ trình duyệt
    ├── mcp_server.py                # MCP Server (tương thích cả mcp 1.x & 2.x)
    ├── proxy_server.py              # OpenAI API Proxy Server
    └── cli.py                       # CLI Handler
```

---

## 🔒 Bảo Mật & Quyền Riêng Tư (Security & Privacy)

- 🛡️ **Không lưu trữ mật khẩu**: Ứng dụng chỉ đọc phiên cookie đã xác thực sẵn từ trình duyệt cục bộ của bạn.
- 🚫 **Bảo vệ mã nguồn**: File cấu hình `.env` chứa token cá nhân được đưa vào `.gitignore`, tuyệt đối không bao giờ bị đẩy lên GitHub.
- 🔐 **Giao tiếp an toàn**: Toàn bộ kết nối được mã hóa trực tiếp giữa máy tính của bạn và máy chủ Google Gemini Web qua giao thức HTTPS chính thống.

---

## ⚠️ Khuyến Nghị Sử Dụng & Tuân Thủ Quy Chế Google (Disclaimer & Recommendations)

### 1. Về mặt Điều khoản Dịch vụ của Google (Google Terms of Service)
Nếu xét theo nghĩa đen và chặt chẽ nhất của quy chế: Cách làm này nằm ở "vùng xám" (grey zone) và về mặt kỹ thuật không được Google cấp phép chính thức.
- **Lý do:** Trong [Google Terms of Service](https://policies.google.com/terms) và [Google Generative AI Additional Terms of Service](https://policies.google.com/terms/generative-ai), Google có điều khoản cấm rõ: *"Không can thiệp, truy cập dịch vụ của chúng tôi bằng bất kỳ phương thức nào khác ngoài các giao diện được chúng tôi hỗ trợ công khai..."* (non-publicly supported interfaces / web automation / reverse engineering).
- Giao diện web `gemini.google.com` được thiết kế cho con người tương tác qua trình duyệt. Khi chúng ta trích xuất session/cookie để biến thành MCP Server cho Antigravity/CLI gọi tự động, về bản chất kỹ thuật đây là hình thức **Reverse Engineering Unofficial API**.
- Đối với nhu cầu lập trình/tự động hóa, Google yêu cầu nhà phát triển sử dụng kênh chính thống là **Google AI Studio** hoặc **Google Cloud Vertex AI** (dùng API Key chính thức).

### 2. Về mặt thực tế sử dụng (Dự án sạch & mục đích cá nhân)
Mặc dù về mặt kỹ thuật không thuộc kênh chính thống, nhưng bạn có thể an tâm ở các điểm sau:
- **Không có rủi ro pháp lý:** Bạn dùng để phục vụ công việc cá nhân, hỗ trợ lập trình dự án sạch, không phá hoại hệ thống, không trục lợi bằng cách mở dịch vụ bán lại API lậu, và không cào dữ liệu huấn luyện mô hình cạnh tranh. Google không bao giờ đi kiện tụng người dùng cá nhân trong trường hợp này.
- **Rủi ro duy nhất là ở cấp độ Tài khoản (Account Risk):**
  - **Văng phiên / Hết hạn Cookie:** Cookie web của Google có thời hạn hoặc sẽ bị vô hiệu hóa khi có sự thay đổi về IP, bảo mật.
  - **Cơ chế chống Bot tự động (Abuse Detection):** Nếu bạn gửi prompt quá dồn dập (ví dụ vòng lặp gọi hàng chục request/phút), hệ thống bảo mật của Google có thể nhận diện lưu lượng bất thường và tạm khóa/chặn tính năng Gemini của tài khoản đó, hoặc bắt giải CAPTCHA.

### 3. Khuyến nghị thực tế để an tâm sử dụng
- **Sử dụng tài khoản Google phụ (Secondary Account):** Tuyệt đối không dùng tài khoản Google chính (chứa Gmail làm việc lâu năm, Google Drive quan trọng, tài khoản liên kết Google Pay/ngân hàng) để trích xuất cookie web. Hãy dùng một tài khoản Google riêng biệt để đăng nhập Gemini Web và lấy session cho Antigravity. Nếu tài khoản này có bị gắn cờ hạn chế thì công việc chính của bạn hoàn toàn không bị ảnh hưởng.
- **Kiểm soát tần suất gọi:** Tránh các kịch bản loop tự động bắn request liên tục không có độ trễ nghỉ (delay).

---

## 🤝 Đóng Góp & Bản Quyền (License & Copyright)

- **Tác quyền & Bản quyền**: Copyright (c) 2026 **NDKBVH**. All rights reserved.
- **Giấy phép**: Dự án được phát hành theo giấy phép mã nguồn mở **[MIT License](LICENSE)**. Mọi đóng góp (Pull Request, Issue, Feature Request) đều được chào đón!


