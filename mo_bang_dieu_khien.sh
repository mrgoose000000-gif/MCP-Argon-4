#!/usr/bin/env bash
# ==============================================================================
# KHỞI CHẠY BẢNG ĐIỀU KHIỂN QUẢN LÝ TÀI KHOẢN GEMINI 4 ARGON (MACOS / LINUX)
# ==============================================================================

cd "$(dirname "$0")"

if [ -f ".venv/bin/python" ]; then
    PY_CMD=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY_CMD=python3
else
    PY_CMD=python
fi

echo "=============================================================================="
echo "  🚀 ĐANG MỞ BẢNG ĐIỀU KHIỂN GEMINI 4 ARGON MULTI-ACCOUNT..."
echo "  🌐 URL: http://127.0.0.1:8000/dashboard"
echo "=============================================================================="

$PY_CMD run_dashboard.py
