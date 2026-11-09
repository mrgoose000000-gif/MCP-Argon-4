#!/usr/bin/env python3
"""
Khởi chạy Bảng Điều Khiển Quản Lý Tài Khoản (Visual Dashboard) cho Gemini 4 Argon.
Tự động mở trình duyệt web tại: http://127.0.0.1:8000/dashboard
"""

import sys
import time
import webbrowser
import threading
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import uvicorn
from gemini2anti.proxy_server import app


def open_browser_delayed(url: str, delay: float = 1.0):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}/dashboard"

    print("=" * 72)
    print("  🚀 ĐANG KHỞI ĐỘNG BẢNG ĐIỀU KHIỂN GEMINI 4 ARGON MULTI-ACCOUNT...")
    print(f"  🌐 Truy cập trực tiếp tại: {url}")
    print("  ⭐ Hỗ trợ: Quản lý nhiều tài khoản, Check Quota, Kích hoạt & Auto-Failover")
    print("=" * 72)

    # Mở trình duyệt sau 1 giây
    threading.Thread(target=open_browser_delayed, args=(url, 1.2), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
