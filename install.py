#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
TỰ ĐỘNG CÀI ĐẶT MCP-ARGON-4 CHO ANTIGRAVITY IDE (Auto-Installer)
==============================================================================
Script này tự động:
1. Tạo môi trường ảo Python (.venv) và cài đặt thư viện cần thiết.
2. Cấu hình MCP Server 'gemini-web' vào ~/.gemini/config/mcp_config.json.
3. Cài đặt kỹ năng (Skill) /kg4 vào ~/.gemini/config/skills/kg4/SKILL.md.
4. Cấp quyền thực thi cho các script mở Dashboard.
==============================================================================
"""

import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path

# Màu sắc hiển thị Terminal
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def log_info(msg):
    print(f"{BLUE}[THÔNG BÁO]{RESET} {msg}")

def log_success(msg):
    print(f"{GREEN}[THÀNH CÔNG]{RESET} {msg}")

def log_warning(msg):
    print(f"{YELLOW}[CẢNH BÁO]{RESET} {msg}")

def log_error(msg):
    print(f"{RED}[LỖI]{RESET} {msg}")

def check_python_version():
    if sys.version_info < (3, 10):
        log_error("Yêu cầu Python tối thiểu 3.10 trở lên! Hiện tại: " + sys.version)
        sys.exit(1)

def setup_venv(repo_dir: Path) -> Path:
    venv_dir = repo_dir / ".venv"
    is_win = platform.system() == "Windows"
    venv_python = venv_dir / "Scripts" / "python.exe" if is_win else venv_dir / "bin" / "python"

    if not venv_dir.exists():
        log_info(f"Đang khởi tạo môi trường ảo Python tại {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        log_success("Đã tạo môi trường ảo .venv")

    log_info("Đang cài đặt / nâng cấp các thư viện phụ thuộc (requirements.txt)...")
    req_file = repo_dir / "requirements.txt"
    if req_file.exists():
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=False)
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(req_file)], check=True)
        log_success("Đã cài đặt xong toàn bộ thư viện cần thiết!")
    else:
        log_warning("Không tìm thấy requirements.txt, bỏ qua bước pip install.")

    return venv_python

def configure_antigravity_mcp(repo_dir: Path, venv_python: Path):
    home_dir = Path.home()
    config_dir = home_dir / ".gemini" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    mcp_config_path = config_dir / "mcp_config.json"
    mcp_data = {"mcpServers": {}}

    if mcp_config_path.exists():
        try:
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    mcp_data = loaded
                    if "mcpServers" not in mcp_data:
                        mcp_data["mcpServers"] = {}
        except Exception as e:
            log_warning(f"Không thể đọc mcp_config.json hiện tại ({e}), tạo cấu hình mới.")

    run_mcp_file = repo_dir / "run_mcp.py"

    mcp_data["mcpServers"]["gemini-web"] = {
        "command": str(venv_python.resolve()),
        "args": [str(run_mcp_file.resolve())],
        "env": {
            "PYTHONIOENCODING": "utf-8"
        }
    }

    with open(mcp_config_path, "w", encoding="utf-8") as f:
        json.dump(mcp_data, f, ensure_ascii=False, indent=4)

    log_success(f"Đã đăng ký MCP Server 'gemini-web' vào: {mcp_config_path}")

def install_kg4_skill(repo_dir: Path):
    home_dir = Path.home()
    source_skill = repo_dir / "skills" / "kg4" / "SKILL.md"
    target_skill_dir = home_dir / ".gemini" / "config" / "skills" / "kg4"
    target_skill_dir.mkdir(parents=True, exist_ok=True)
    target_skill_file = target_skill_dir / "SKILL.md"

    if source_skill.exists():
        shutil.copy2(source_skill, target_skill_file)
        log_success(f"Đã cài đặt Skill /kg4 vào: {target_skill_file}")
    else:
        log_warning("Không tìm thấy skills/kg4/SKILL.md trong repo để cài đặt.")

def make_scripts_executable(repo_dir: Path):
    if platform.system() != "Windows":
        sh_script = repo_dir / "mo_bang_dieu_khien.sh"
        if sh_script.exists():
            sh_script.chmod(0o755)
        run_mcp = repo_dir / "run_mcp.py"
        if run_mcp.exists():
            run_mcp.chmod(0o755)

def main():
    print(f"\n{BOLD}{CYAN}================================================================={RESET}")
    print(f"{BOLD}{GREEN}      BẮT ĐẦU CÀI ĐẶT MCP-ARGON-4 CHO ANTIGRAVITY IDE            {RESET}")
    print(f"{BOLD}{CYAN}================================================================={RESET}\n")

    check_python_version()
    repo_dir = Path(__file__).resolve().parent

    # 1. Setup Venv & Packages
    venv_python = setup_venv(repo_dir)

    # 2. Config MCP in Antigravity
    configure_antigravity_mcp(repo_dir, venv_python)

    # 3. Install Skill /kg4
    install_kg4_skill(repo_dir)

    # 4. Permissions
    make_scripts_executable(repo_dir)

    print(f"\n{BOLD}{GREEN}================================================================={RESET}")
    print(f"{BOLD}{GREEN}             CÀI ĐẶT HOÀN TẤT THÀNH CÔNG!                        {RESET}")
    print(f"{BOLD}{GREEN}================================================================={RESET}\n")

    is_win = platform.system() == "Windows"
    launch_cmd = "mo_bang_dieu_khien.bat" if is_win else "./mo_bang_dieu_khien.sh"

    print(f"{BOLD}Các bước tiếp theo rất đơn giản:{RESET}")
    print(f" 1. Chạy lệnh: {CYAN}{launch_cmd}{RESET} để mở Bảng Điều Khiển Quản Lý Tài Khoản (Visual Dashboard).")
    print(f" 2. Trên Dashboard ({BLUE}http://127.0.0.1:8000/dashboard{RESET}):")
    print(f"    - Bấm {GREEN}'Quét Trình Duyệt'{RESET} nếu bạn đã đăng nhập https://gemini.google.com trên Chrome.")
    print(f"    - Hoặc bấm {GREEN}'Thêm Tài Khoản'{RESET} để nạp cookie Google của bạn.")
    print(f" 3. Khởi động lại {BOLD}Antigravity IDE{RESET} và gõ {BOLD}{CYAN}/kg4 <câu hỏi>{RESET} trong khung chat để dùng ngay model Gemini 4 Argon!")
    print()

if __name__ == "__main__":
    main()
