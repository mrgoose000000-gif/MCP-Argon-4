@echo off
chcp 65001 >nul
title DAY MA NGUON LEN GITHUB

cd /d "%~dp0"

echo ==============================================================================
echo   DANG TIEN HANH DAY MA NGUON LEN GITHUB:
echo   Repository: https://github.com/duykhanhbv-bit/geminiweb2antigravity
echo ==============================================================================
echo.

git branch -M main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo   🎉 CHUC MUNG! DA DAY MA NGUON LEN GITHUB THANH CONG!
    echo   👉 Xem repository tai: https://github.com/duykhanhbv-bit/geminiweb2antigravity
    echo ==============================================================================
) else (
    echo.
    echo ==============================================================================
    echo   ⚠️ Day len GitHub chua hoan tat. 
    echo   Neu trinh duyet hien cua so dang nhap GitHub, vui long bam "Authorize/Sign in".
    echo ==============================================================================
)

echo.
pause
