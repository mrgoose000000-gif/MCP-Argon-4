"""
Quản lý cấu hình và bóc tách Cookie cho Gemini Web (gemini.google.com/app).
Hỗ trợ cả trích xuất tự động từ trình duyệt (Edge, Chrome, Firefox, Brave...) và cấu hình thủ công.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Tải cấu hình từ .env tại thư mục làm việc hoặc thư mục dự án
load_dotenv(override=False)

try:
    import rookiepy
    HAS_ROOKIEPY = True
except ImportError:
    HAS_ROOKIEPY = False


def extract_cookies_from_browser(browser_name: str = "edge") -> Dict[str, str]:
    """
    Trích xuất cookies của Google từ trình duyệt được chỉ định.
    Hỗ trợ: edge, chrome, firefox, brave, opera, vivaldi.
    """
    if not HAS_ROOKIEPY:
        return {}

    browser_map = {
        "edge": rookiepy.edge,
        "chrome": rookiepy.chrome,
        "firefox": rookiepy.firefox,
        "brave": rookiepy.brave,
        "opera": rookiepy.opera,
        "vivaldi": rookiepy.vivaldi,
    }

    getter = browser_map.get(browser_name.lower())
    if not getter:
        return {}

    try:
        cookies = getter(["google.com"])
        res = {}
        for c in cookies:
            name = c.get("name")
            value = c.get("value")
            if name in ["__Secure-1PSID", "__Secure-1PSIDTS", "__Secure-1PSIDCC"]:
                res[name] = value
        return res
    except Exception as e:
        return {}


def get_gemini_credentials() -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """
    Lấy thông tin đăng nhập Gemini Web theo thứ tự ưu tiên:
    1. Biến môi trường (.env hoặc OS environment):
       - GEMINI_SECURE_1PSID
       - GEMINI_SECURE_1PSIDTS
       - GEMINI_SECURE_1PSIDCC
    2. Tự động trích xuất từ trình duyệt (Edge, Chrome, Firefox, Brave...)
    
    Trả về tuple: (psid, psidts, psidcc, source_description)
    """
    # 1. Tự động quét trình duyệt nếu bật GEMINI_AUTO_BROWSER_COOKIES (mặc định là True)
    auto_enabled = os.getenv("GEMINI_AUTO_BROWSER_COOKIES", "true").lower() in ["1", "true", "yes"]
    preferred_browser = os.getenv("GEMINI_PREFERRED_BROWSER", "edge").lower()

    if auto_enabled and HAS_ROOKIEPY:
        browsers_to_try = [preferred_browser] + [b for b in ["edge", "firefox", "chrome", "brave"] if b != preferred_browser]
        for b in browsers_to_try:
            cookies = extract_cookies_from_browser(b)
            psid = cookies.get("__Secure-1PSID")
            psidts = cookies.get("__Secure-1PSIDTS")
            psidcc = cookies.get("__Secure-1PSIDCC")
            if psid and psidts:
                return psid, psidts, psidcc, f"Tự động trích xuất từ trình duyệt {b.upper()}"

    # 2. Dự phòng: Kiểm tra biến môi trường (.env hoặc OS environment)
    env_psid = os.getenv("GEMINI_SECURE_1PSID", "").strip()
    env_psidts = os.getenv("GEMINI_SECURE_1PSIDTS", "").strip()
    env_psidcc = os.getenv("GEMINI_SECURE_1PSIDCC", "").strip()

    if env_psid:
        return env_psid, env_psidts or None, env_psidcc or None, "Cấu hình thủ công (.env/Environment Variables)"

    return None, None, None, "Không tìm thấy Cookie đăng nhập Gemini"


def get_default_model() -> str:
    """Trả về model mặc định được cấu hình."""
    return os.getenv("GEMINI_DEFAULT_MODEL", "gemini-4")


def get_default_extended_thinking() -> bool:
    """
    Trả về chế độ suy nghĩ mở rộng mặc định (Extended Thinking / High reasoning).
    Mặc định luôn là True (Gemini 4 High).
    """
    val = os.getenv("GEMINI_EXTENDED_THINKING", "true").lower()
    return val in ["1", "true", "yes", "high", "on"]


def get_proxy() -> Optional[str]:
    """Trả về proxy nếu có."""
    proxy = os.getenv("GEMINI_PROXY", "").strip()
    return proxy if proxy else None

