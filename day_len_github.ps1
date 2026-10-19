# ==============================================================================
# SCRIPT ĐẨY MÃ NGUỒN LÊN GITHUB (POWERSHELL)
# ==============================================================================

Set-Location -Path $PSScriptRoot

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  TIẾN HÀNH ĐẨY MÃ NGUỒN LÊN GITHUB:" -ForegroundColor Yellow
Write-Host "  Repository: https://github.com/duykhanhbv-bit/geminiweb2antigravity" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host "  🎉 CHÚC MỪNG! ĐÃ ĐẨY MÃ NGUỒN LÊN GITHUB THÀNH CÔNG!" -ForegroundColor Green
    Write-Host "  👉 Xem repository tại: https://github.com/duykhanhbv-bit/geminiweb2antigravity" -ForegroundColor Yellow
    Write-Host "==============================================================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Red
    Write-Host "  ⚠️ Đẩy lên GitHub chưa hoàn tất." -ForegroundColor Yellow
    Write-Host "  Nếu trình duyệt hiện cửa sổ đăng nhập GitHub, vui lòng bấm 'Authorize/Sign in'." -ForegroundColor White
    Write-Host "==============================================================================" -ForegroundColor Red
}

Write-Host ""
pause
