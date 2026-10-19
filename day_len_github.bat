@echo off
setlocal
title DAY MA NGUON LEN GITHUB

:: Chuyen den thu muc chua script an toan
cd /d "%~dp0"

echo ==============================================================================
echo   TIEN HANH DAY MA NGUON LEN GITHUB:
echo   Repository: https://github.com/duykhanhbv-bit/geminiweb2antigravity
echo ==============================================================================
echo.

git branch -M main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo   [HOAN TAT] DA DAY MA NGUON LEN GITHUB THANH CONG!
    echo   Dia chi repo: https://github.com/duykhanhbv-bit/geminiweb2antigravity
    echo ==============================================================================
) else (
    echo.
    echo ==============================================================================
    echo   [CHU Y] Day len GitHub chua hoan tat.
    echo   Neu trinh duyet hien cua so dang nhap GitHub, vui long bam "Authorize/Sign in".
    echo ==============================================================================
)

echo.
pause
