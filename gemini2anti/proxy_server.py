"""
OpenAI-Compatible HTTP Proxy Server & Multi-Account Visual Dashboard cho Google Gemini Web.
Cung cấp các endpoint:
  - GET  / hoặc /dashboard (Giao diện bảng điều khiển trực quan quản lý đa tài khoản & quota)
  - GET  /api/accounts
  - POST /api/accounts/switch
  - POST /api/accounts/add
  - DELETE /api/accounts/{id}
  - POST /api/accounts/{id}/check-quota
  - POST /api/accounts/check-all
  - POST /api/accounts/scan-browsers
  - POST /api/accounts/toggle-failover
  - GET  /v1/models
  - POST /v1/chat/completions (hỗ trợ cả streaming SSE và non-streaming)
  - GET  /health
"""

import time
import uuid
import json
import logging
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gemini2anti.client import bridge
from gemini2anti.config import get_gemini_credentials, get_default_model
from gemini2anti.account_manager import account_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiProxyServer")

app = FastAPI(
    title="Gemini Web Multi-Account Bridge & Dashboard",
    description="Cầu nối quản lý đa tài khoản Google Gemini Web và OpenAI API Proxy",
    version="2.0.0"
)

# Cho phép CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# DATA MODELS
# ==============================================================================

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Any]]


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    extended_thinking: Optional[bool] = True


class SwitchAccountRequest(BaseModel):
    account_id: str


class AddAccountRequest(BaseModel):
    secure_1psid: str
    secure_1psidts: str
    secure_1psidcc: Optional[str] = ""
    name: Optional[str] = ""
    email: Optional[str] = ""
    browser_source: Optional[str] = "Thủ công"


class UpdateCookiesRequest(BaseModel):
    secure_1psid: str
    secure_1psidts: str
    secure_1psidcc: Optional[str] = ""


class ToggleFailoverRequest(BaseModel):
    enabled: bool


# ==============================================================================
# DASHBOARD HTML & UI (Hallmark Compliant)
# ==============================================================================

DASHBOARD_HTML = """<!DOCTYPE html>
<!-- Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V5 -->
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gemini 4 Argon · Account Pool & Quota Command Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --font-display: 'Space Grotesk', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      
      --color-bg: #090d16;
      --color-surface: #101626;
      --color-surface-elevated: #161f36;
      --color-surface-subtle: #1c2742;
      --color-border: #233152;
      --color-border-glow: #2f4577;
      
      --color-text-main: #f1f5f9;
      --color-text-muted: #94a3b8;
      --color-text-dim: #64748b;
      
      --color-accent: #10b981;
      --color-accent-glow: rgba(16, 185, 129, 0.2);
      --color-argon: #06b6d4;
      --color-argon-glow: rgba(6, 182, 212, 0.2);
      
      --color-warn: #f59e0b;
      --color-danger: #ef4444;
      --color-danger-glow: rgba(239, 68, 68, 0.2);

      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 16px;
      --radius-full: 9999px;
      
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.4);
      --shadow-md: 0 4px 12px -2px rgba(0, 0, 0, 0.5);
      --shadow-lg: 0 12px 28px -4px rgba(0, 0, 0, 0.6);
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      overflow-x: clip;
      background-color: var(--color-bg);
      color: var(--color-text-main);
      font-family: var(--font-display);
      font-size: 15px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    /* Layout */
    .app-container {
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px 20px 60px;
    }

    /* Top Navigation Bar */
    .top-nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--color-border);
      margin-bottom: 28px;
      gap: 16px;
      flex-wrap: wrap;
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-badge {
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 16px var(--color-argon-glow);
      font-size: 20px;
    }

    .brand-title {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
    }

    .brand-subtitle {
      font-size: 0.8rem;
      color: var(--color-text-dim);
      font-family: var(--font-mono);
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      font-family: var(--font-display);
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      white-space: nowrap;
      text-decoration: none;
    }

    .btn:focus-visible {
      outline: 2px solid var(--color-argon);
      outline-offset: 2px;
    }

    .btn-primary {
      background: var(--color-argon);
      color: #061727;
      border-color: #22d3ee;
      box-shadow: 0 0 12px var(--color-argon-glow);
    }
    .btn-primary:hover { background: #22d3ee; }
    .btn-primary:active { transform: translateY(1px); }

    .btn-secondary {
      background: var(--color-surface-elevated);
      color: var(--color-text-main);
      border-color: var(--color-border);
    }
    .btn-secondary:hover { background: var(--color-surface-subtle); border-color: var(--color-border-glow); }
    .btn-secondary:active { transform: translateY(1px); }

    .btn-accent {
      background: var(--color-accent);
      color: #022c22;
      border-color: #34d399;
      box-shadow: 0 0 10px var(--color-accent-glow);
    }
    .btn-accent:hover { background: #34d399; }

    .btn-danger {
      background: transparent;
      color: var(--color-danger);
      border-color: rgba(239, 68, 68, 0.3);
    }
    .btn-danger:hover { background: rgba(239, 68, 68, 0.15); border-color: var(--color-danger); }

    .btn:disabled, .btn[disabled] {
      opacity: 0.45;
      cursor: not-allowed;
      transform: none !important;
    }

    /* Metrics Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }

    .metric-card {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      position: relative;
      box-shadow: var(--shadow-sm);
    }

    .metric-label {
      font-size: 0.8rem;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .metric-val {
      font-size: 1.55rem;
      font-weight: 700;
      color: #fff;
      font-family: var(--font-mono);
    }

    .metric-sub {
      font-size: 0.8rem;
      color: var(--color-text-dim);
      margin-top: 4px;
    }

    /* Section Header */
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      gap: 12px;
      flex-wrap: wrap;
    }

    .section-title {
      font-size: 1.15rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .toggle-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--color-surface);
      padding: 6px 14px;
      border-radius: var(--radius-full);
      border: 1px solid var(--color-border);
      font-size: 0.85rem;
    }

    .switch {
      position: relative;
      display: inline-block;
      width: 40px;
      height: 22px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: var(--color-surface-subtle);
      transition: .2s;
      border-radius: 34px;
      border: 1px solid var(--color-border);
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 14px;
      width: 14px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: .2s;
      border-radius: 50%;
    }
    input:checked + .slider {
      background-color: var(--color-accent);
      border-color: var(--color-accent);
    }
    input:checked + .slider:before {
      transform: translateX(18px);
    }

    /* Accounts List / Cards */
    .accounts-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .account-card {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 20px;
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) auto;
      align-items: center;
      gap: 20px;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s ease;
      position: relative;
    }

    .account-card.is-active {
      border-color: var(--color-accent);
      box-shadow: 0 0 20px var(--color-accent-glow);
      background: linear-gradient(90deg, rgba(16, 185, 129, 0.05) 0%, var(--color-surface) 60%);
    }

    .account-info {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .account-avatar {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: var(--color-surface-subtle);
      border: 2px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.15rem;
      color: var(--color-argon);
      flex-shrink: 0;
    }

    .account-card.is-active .account-avatar {
      border-color: var(--color-accent);
      color: var(--color-accent);
    }

    .account-details {
      min-width: 0;
    }

    .account-name-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 2px;
      flex-wrap: wrap;
    }

    .account-name {
      font-weight: 700;
      font-size: 1.05rem;
      color: #fff;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: var(--radius-full);
      font-size: 0.72rem;
      font-weight: 700;
      font-family: var(--font-mono);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .badge-active {
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .badge-healthy {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
    }

    .badge-limited {
      background: rgba(245, 158, 11, 0.2);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }

    .badge-expired {
      background: rgba(239, 68, 68, 0.2);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.4);
    }

    .account-email {
      font-size: 0.88rem;
      color: var(--color-text-muted);
      font-family: var(--font-mono);
      word-break: break-all;
    }

    .account-meta {
      font-size: 0.75rem;
      color: var(--color-text-dim);
      margin-top: 3px;
    }

    /* Quota Column */
    .quota-box {
      background: var(--color-surface-elevated);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      padding: 12px 14px;
    }

    .quota-numbers {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 6px;
    }

    .quota-curr {
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      font-family: var(--font-mono);
    }

    .quota-tier {
      font-size: 0.72rem;
      font-family: var(--font-mono);
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 0.04em;
    }
    .tier-free {
      color: #94a3b8;
      background: rgba(148, 163, 184, 0.12);
    }
    .tier-advanced {
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      box-shadow: 0 0 8px rgba(56, 189, 248, 0.2);
    }

    .progress-bar-bg {
      width: 100%;
      height: 6px;
      background: var(--color-surface-subtle);
      border-radius: var(--radius-full);
      overflow: hidden;
      margin-bottom: 6px;
    }

    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, #10b981, #06b6d4);
      border-radius: var(--radius-full);
      transition: width 0.3s ease;
    }

    .quota-reset {
      font-size: 0.75rem;
      color: var(--color-text-dim);
      display: flex;
      align-items: center;
      gap: 4px;
    }

    /* Action buttons in card */
    .account-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Modal */
    .modal-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .modal-backdrop.is-open {
      display: flex;
    }

    .modal-box {
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      width: 100%;
      max-width: 580px;
      box-shadow: var(--shadow-lg);
      overflow: hidden;
      animation: modalFadeIn 0.2s ease-out;
    }

    @keyframes modalFadeIn {
      from { opacity: 0; transform: scale(0.96); }
      to { opacity: 1; transform: scale(1); }
    }

    .modal-header {
      padding: 20px;
      border-bottom: 1px solid var(--color-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .modal-title {
      font-size: 1.15rem;
      font-weight: 700;
    }

    .modal-body {
      padding: 20px;
    }

    .form-group {
      margin-bottom: 16px;
    }

    .form-label {
      display: block;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--color-text-muted);
      margin-bottom: 6px;
    }

    .form-input {
      width: 100%;
      background: var(--color-surface-elevated);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      color: #fff;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      transition: border-color 0.15s ease;
    }

    .form-input:focus {
      outline: none;
      border-color: var(--color-argon);
      box-shadow: 0 0 0 2px var(--color-argon-glow);
    }

    .guide-tip {
      background: var(--color-surface-elevated);
      border-left: 3px solid var(--color-argon);
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      font-size: 0.78rem;
      color: var(--color-text-muted);
      margin-bottom: 16px;
      line-height: 1.4;
    }

    .modal-footer {
      padding: 16px 20px;
      border-top: 1px solid var(--color-border);
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }

    /* Toast Notification */
    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 200;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .toast {
      background: var(--color-surface-elevated);
      border: 1px solid var(--color-border);
      border-left: 4px solid var(--color-argon);
      padding: 12px 18px;
      border-radius: var(--radius-sm);
      color: #fff;
      font-size: 0.88rem;
      box-shadow: var(--shadow-lg);
      animation: toastIn 0.25s ease-out;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .toast.success { border-left-color: var(--color-accent); }
    .toast.error { border-left-color: var(--color-danger); }

    @keyframes toastIn {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
      .account-card {
        grid-template-columns: 1fr;
        gap: 16px;
      }
      .account-actions {
        justify-content: flex-start;
        flex-wrap: wrap;
      }
      .top-nav {
        flex-direction: column;
        align-items: flex-start;
      }
      .nav-actions {
        width: 100%;
        justify-content: space-between;
      }
    }
  </style>
</head>
<body>
  <div class="app-container">
    
    <!-- Top Nav -->
    <header class="top-nav">
      <div class="brand-wrap">
        <div class="logo-badge">⚡</div>
        <div>
          <h1 class="brand-title">Gemini 4 Argon · Account Pool</h1>
          <div class="brand-subtitle">Antigravity Multi-Account Hub & Auto-Failover</div>
        </div>
      </div>
      <div class="nav-actions">
        <button class="btn btn-secondary" onclick="scanBrowsers()" id="btnScan">
          <span>🔍</span> Quét Trình Duyệt
        </button>
        <button class="btn btn-secondary" onclick="checkAllQuotas()" id="btnCheckAll">
          <span>🔄</span> Check Tất Cả
        </button>
        <button class="btn btn-primary" onclick="openAddModal()">
          <span>➕</span> Thêm Tài Khoản
        </button>
      </div>
    </header>

    <!-- Metrics Cards -->
    <section class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">👤 Tài khoản đang chạy</div>
        <div class="metric-val" id="metricActiveName">—</div>
        <div class="metric-sub" id="metricActiveEmail">Chưa kích hoạt</div>
      </div>
      
      <div class="metric-card">
        <div class="metric-label">📊 Tổng Quota khả dụng</div>
        <div class="metric-val" id="metricTotalQuota">—</div>
        <div class="metric-sub" id="metricHealthyCount">0 tài khoản khả dụng</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">⚡ Cơ chế Auto-Failover</div>
        <div class="metric-val" id="metricFailoverStatus" style="color: var(--color-accent);">BẬT</div>
        <div class="metric-sub">Tự động xoay vòng khi hết quota</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">🎯 Lệnh Antigravity</div>
        <div class="metric-val" style="color: var(--color-argon);">/kg4</div>
        <div class="metric-sub">Mặc định Gemini 4 High Reasoning</div>
      </div>
    </section>

    <!-- Section Header -->
    <div class="section-head">
      <div class="section-title">
        <span>📋</span> Danh Sách Tài Khoản Google Trong Pool (<span id="accCount">0</span>)
      </div>
      <div class="toggle-wrap">
        <span>Tự động chuyển khi hết Quota (Auto-Failover):</span>
        <label class="switch">
          <input type="checkbox" id="failoverToggle" checked onchange="toggleFailover(this.checked)">
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <!-- Accounts List Container -->
    <main class="accounts-list" id="accountsList">
      <!-- Dynamic render here -->
    </main>

  </div>

  <!-- Add Account Modal -->
  <div class="modal-backdrop" id="addModal">
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title" id="modalTitle">Thêm Tài Khoản Google Mới</h3>
        <button class="btn btn-secondary" style="padding: 4px 8px;" onclick="closeAddModal()">✕</button>
      </div>
      <div class="modal-body">
        <div class="guide-tip">
          <strong>💡 Hướng dẫn lấy Cookie từ Trình duyệt:</strong><br>
          1. Mở trình duyệt (hoặc Profile) đã đăng nhập tài khoản Google và vào <code>gemini.google.com/app</code>.<br>
          2. Bấm <strong>F12</strong> &rarr; chọn tab <strong>Application</strong> (Lưu trữ) &rarr; <strong>Cookies</strong> &rarr; <code>https://gemini.google.com</code>.<br>
          3. Copy giá trị <code>__Secure-1PSID</code> và <code>__Secure-1PSIDTS</code> dán vào ô dưới.
        </div>

        <div class="form-group" id="inpNameGroup">
          <label class="form-label">Tên hiển thị hoặc Ghi chú (Tùy chọn):</label>
          <input type="text" class="form-input" id="inpName" placeholder="Ví dụ: Tài khoản phụ 1, Clone A...">
        </div>

        <div class="form-group">
          <label class="form-label">Cookie __Secure-1PSID (*Bắt buộc):</label>
          <input type="text" class="form-input" id="inpPsid" placeholder="g.a000Egn...">
        </div>

        <div class="form-group">
          <label class="form-label">Cookie __Secure-1PSIDTS (Khuyên dùng):</label>
          <input type="text" class="form-input" id="inpPsidts" placeholder="sidts-CjEBN...">
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeAddModal()">Hủy</button>
        <button class="btn btn-primary" onclick="submitAddAccount()" id="btnSubmitAdd">Xác Nhận Thêm</button>
      </div>
    </div>
  </div>

  <!-- Toast Container -->
  <div class="toast-container" id="toastContainer"></div>

  <script>
    let globalData = { accounts: [], active_account_id: null, auto_failover_enabled: true };

    function showToast(msg, type = 'info') {
      const container = document.getElementById('toastContainer');
      const toast = document.createElement('div');
      toast.className = `toast ${type}`;
      toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '⚠' : 'ℹ'}</span> ${msg}`;
      container.appendChild(toast);
      setTimeout(() => { toast.remove(); }, 3500);
    }

    async function fetchAccounts() {
      try {
        const res = await fetch('/api/accounts');
        const json = await res.json();
        if (json.success) {
          globalData = json.data;
          renderUI();
        }
      } catch (e) {
        showToast('Không thể kết nối đến máy chủ: ' + e, 'error');
      }
    }

    function renderUI() {
      const accounts = globalData.accounts || [];
      const activeId = globalData.active_account_id;
      document.getElementById('accCount').innerText = accounts.length;
      document.getElementById('failoverToggle').checked = !!globalData.auto_failover_enabled;
      document.getElementById('metricFailoverStatus').innerText = globalData.auto_failover_enabled ? 'BẬT' : 'TẮT';
      document.getElementById('metricFailoverStatus').style.color = globalData.auto_failover_enabled ? 'var(--color-accent)' : 'var(--color-text-dim)';

      let activeAcc = accounts.find(a => a.id === activeId) || (accounts.length > 0 ? accounts[0] : null);
      if (activeAcc) {
        document.getElementById('metricActiveName').innerText = activeAcc.name || 'Account';
        document.getElementById('metricActiveEmail').innerText = activeAcc.email || '';
      } else {
        document.getElementById('metricActiveName').innerText = 'Chưa có';
        document.getElementById('metricActiveEmail').innerText = 'Hãy thêm tài khoản';
      }

      let totalQuota = 0;
      let healthyCount = 0;
      accounts.forEach(a => {
        totalQuota += (a.quota_remaining || 0);
        if (a.status === 'HEALTHY') healthyCount++;
      });
      document.getElementById('metricTotalQuota').innerText = totalQuota + ' credits';
      document.getElementById('metricHealthyCount').innerText = `${healthyCount}/${accounts.length} tài khoản khả dụng`;

      const listEl = document.getElementById('accountsList');
      if (accounts.length === 0) {
        listEl.innerHTML = `
          <div style="text-align: center; padding: 48px 20px; background: var(--color-surface); border-radius: var(--radius-lg); border: 1px dashed var(--color-border);">
            <div style="font-size: 2.2rem; margin-bottom: 12px;">📭</div>
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 4px;">Chưa có tài khoản nào trong Pool</div>
            <div style="color: var(--color-text-dim); margin-bottom: 16px;">Hãy bấm "Quét Trình Duyệt" hoặc "Thêm Tài Khoản" để bắt đầu.</div>
            <button class="btn btn-primary" onclick="openAddModal()">➕ Thêm Tài Khoản Đầu Tiên</button>
          </div>
        `;
        return;
      }

      listEl.innerHTML = accounts.map(a => {
        const isActive = (a.id === activeId || a.is_active);
        const initial = (a.name || a.email || 'G').charAt(0).toUpperCase();
        const percent = Math.min(100, Math.round(((a.quota_remaining || 0) / (a.quota_total || 600)) * 100));
        
        let statusBadge = '<span class="badge badge-healthy">HEALTHY</span>';
        if (a.status === 'RATE_LIMITED') statusBadge = '<span class="badge badge-limited">RATE LIMITED</span>';
        if (a.status === 'EXPIRED') statusBadge = '<span class="badge badge-expired">COOKIE HẾT HẠN</span>';

        const isExpired = (a.status === 'EXPIRED');
        const quotaBoxContent = isExpired ? `
            <div class="quota-numbers">
              <span class="quota-curr" style="color: #f87171; font-size: 0.95rem;">⚠️ Phiên Hết Hạn (Cookie Expired)</span>
              <span class="quota-tier" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.3);">MẤT KẾT NỐI</span>
            </div>
            <div class="quota-reset" style="color: #fca5a5; font-size: 0.8rem; margin-top: 6px;">
              <span>🔑</span> <em>Quota không bị mất</em>, vui lòng dán lại Cookie từ trình duyệt.
            </div>
        ` : `
            <div class="quota-numbers">
              <span class="quota-curr">${a.quota_remaining ?? '—'} / ${a.quota_total || 600} <small style="font-size:0.75rem; color:var(--color-text-dim);">credits</small></span>
              <span class="quota-tier ${a.tier === 'ADVANCED' ? 'tier-advanced' : 'tier-free'}">${a.tier || 'FREE'}</span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width: ${percent}%;"></div>
            </div>
            <div class="quota-reset">
              <span>⏱️</span> Reset: ${escapeHtml(a.quota_reset_at || 'Chưa cập nhật')}
            </div>
        `;

        return `
          <div class="account-card ${isActive ? 'is-active' : ''}">
            <div class="account-info">
              <div class="account-avatar">${initial}</div>
              <div class="account-details">
                <div class="account-name-row">
                  <span class="account-name">${escapeHtml(a.name || 'Google Account')}</span>
                  ${isActive ? '<span class="badge badge-active">⚡ ACTIVE NODE</span>' : ''}
                  ${statusBadge}
                </div>
                <div class="account-email">${escapeHtml(a.email || 'Email chưa định danh')}</div>
                <div class="account-meta">
                  Nguồn: ${escapeHtml(a.browser_source || 'Thủ công')} · ID: <code>${a.id}</code>
                </div>
              </div>
            </div>

            <div class="quota-box">
              ${quotaBoxContent}
            </div>

            <div class="account-actions">
              ${isExpired ? `
                <button class="btn btn-primary" onclick="openUpdateModal('${a.id}', '${escapeHtml(a.name || a.email)}')" style="background: #ef4444; border-color: #f87171;" title="Dán Cookie mới từ trình duyệt để kết nối lại">
                  <span>🔑</span> Cập Nhật Cookie
                </button>
              ` : `
                <button class="btn btn-secondary" onclick="checkQuota('${a.id}', this)" title="Kiểm tra Quota thời gian thực">
                  <span>🔄</span> Check Quota
                </button>
                
                ${isActive ? `
                  <button class="btn btn-secondary" disabled>
                    <span>✓</span> Đang Chạy
                  </button>
                ` : `
                  <button class="btn btn-accent" onclick="switchAccount('${a.id}', this)">
                    <span>⚡</span> Kích Hoạt
                  </button>
                `}
              `}

              <button class="btn btn-danger" onclick="deleteAccount('${a.id}')" title="Xóa tài khoản khỏi Pool">
                🗑️
              </button>
            </div>
          </div>
        `;
      }).join('');
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    async function switchAccount(id, btn) {
      if (btn) { btn.disabled = true; btn.innerText = 'Đang chuyển...'; }
      try {
        const res = await fetch('/api/accounts/switch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ account_id: id })
        });
        const json = await res.json();
        if (json.success) {
          showToast('Đã kích hoạt tài khoản thành công!', 'success');
          fetchAccounts();
        } else {
          showToast(json.detail || 'Lỗi khi chuyển tài khoản', 'error');
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      }
    }

    async function checkQuota(id, btn) {
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span>⌛</span> Đang đọc...';
      }
      try {
        const res = await fetch(`/api/accounts/${id}/check-quota`, { method: 'POST' });
        const json = await res.json();
        if (json.success) {
          showToast(`Đã cập nhật quota cho ${json.data.name || 'tài khoản'}: ${json.data.quota_remaining} credits`, 'success');
          fetchAccounts();
        } else {
          showToast(json.detail || 'Lỗi kiểm tra quota', 'error');
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<span>🔄</span> Check Quota';
        }
      }
    }

    async function checkAllQuotas() {
      const btn = document.getElementById('btnCheckAll');
      btn.disabled = true;
      btn.innerHTML = '<span>⌛</span> Đang kiểm tra...';
      try {
        const res = await fetch('/api/accounts/check-all', { method: 'POST' });
        const json = await res.json();
        if (json.success) {
          showToast('Đã hoàn tất kiểm tra quota toàn bộ tài khoản!', 'success');
          fetchAccounts();
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🔄</span> Check Tất Cả';
      }
    }

    async function scanBrowsers() {
      const btn = document.getElementById('btnScan');
      btn.disabled = true;
      btn.innerHTML = '<span>⌛</span> Đang quét...';
      try {
        const res = await fetch('/api/accounts/scan-browsers', { method: 'POST' });
        const json = await res.json();
        if (json.success) {
          showToast(`Đã quét xong trình duyệt! Tìm thấy và cập nhật ${json.imported_count} phiên.`, 'success');
          fetchAccounts();
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🔍</span> Quét Trình Duyệt';
      }
    }

    async function toggleFailover(checked) {
      try {
        const res = await fetch('/api/accounts/toggle-failover', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: checked })
        });
        const json = await res.json();
        if (json.success) {
          showToast(checked ? 'Đã BẬT cơ chế Auto-Failover!' : 'Đã TẮT cơ chế Auto-Failover', 'info');
          fetchAccounts();
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      }
    }

    async function deleteAccount(id) {
      if (!confirm('Bạn có chắc muốn xóa tài khoản này khỏi hệ thống?')) return;
      try {
        const res = await fetch(`/api/accounts/${id}`, { method: 'DELETE' });
        const json = await res.json();
        if (json.success) {
          showToast('Đã xóa tài khoản.', 'info');
          fetchAccounts();
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      }
    }

    let currentUpdatingAccountId = null;

    function openUpdateModal(id, name) {
      currentUpdatingAccountId = id;
      document.getElementById('modalTitle').innerText = '🔑 Cập Nhật Cookie Cho: ' + name;
      document.getElementById('inpNameGroup').style.display = 'none';
      document.getElementById('btnSubmitAdd').innerText = 'Lưu & Kiểm Tra Lại';
      document.getElementById('inpPsid').value = '';
      document.getElementById('inpPsidts').value = '';
      document.getElementById('addModal').classList.add('is-open');
    }

    function openAddModal() {
      currentUpdatingAccountId = null;
      document.getElementById('modalTitle').innerText = 'Thêm Tài Khoản Google Mới';
      document.getElementById('inpNameGroup').style.display = 'block';
      document.getElementById('btnSubmitAdd').innerText = 'Xác Nhận Thêm';
      document.getElementById('inpPsid').value = '';
      document.getElementById('inpPsidts').value = '';
      document.getElementById('inpName').value = '';
      document.getElementById('addModal').classList.add('is-open');
    }

    function closeAddModal() {
      document.getElementById('addModal').classList.remove('is-open');
    }

    async function submitAddAccount() {
      const psid = document.getElementById('inpPsid').value.trim();
      const psidts = document.getElementById('inpPsidts').value.trim();
      const name = document.getElementById('inpName').value.trim();

      if (!psid) {
        alert('Vui lòng nhập Cookie __Secure-1PSID!');
        return;
      }

      const btn = document.getElementById('btnSubmitAdd');
      btn.disabled = true;
      btn.innerText = 'Đang xác thực & kiểm tra quota...';

      const url = currentUpdatingAccountId 
        ? `/api/accounts/${currentUpdatingAccountId}/update-cookies`
        : '/api/accounts/add';

      const bodyData = currentUpdatingAccountId
        ? { secure_1psid: psid, secure_1psidts: psidts }
        : { secure_1psid: psid, secure_1psidts: psidts, name: name };

      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(bodyData)
        });
        const json = await res.json();
        if (json.success) {
          showToast(currentUpdatingAccountId ? 'Đã cập nhật Cookie thành công!' : 'Thêm tài khoản thành công!', 'success');
          closeAddModal();
          fetchAccounts();
        } else {
          showToast(json.detail || 'Lỗi khi cập nhật tài khoản', 'error');
        }
      } catch (e) {
        showToast('Lỗi: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerText = currentUpdatingAccountId ? 'Lưu & Kiểm Tra Lại' : 'Xác Nhận Thêm';
      }
    }

    // Auto-load on page ready
    fetchAccounts();
  </script>
</body>
</html>
"""


# ==============================================================================
# ROUTE ENDPOINTS
# ==============================================================================

@app.get("/", response_class=RedirectResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Trả về giao diện bảng điều khiển trực quan."""
    return HTMLResponse(content=DASHBOARD_HTML, status_code=200)


@app.get("/api/accounts")
async def list_accounts():
    """Lấy danh sách tài khoản kèm trạng thái và quota."""
    data = account_manager.get_data()
    return {"success": True, "data": data}


@app.post("/api/accounts/switch")
async def switch_account(req: SwitchAccountRequest):
    """Kích hoạt sang tài khoản chỉ định."""
    acc = account_manager.switch_account(req.account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    
    # Ép buộc GeminiWebBridge kết nối lại với tài khoản mới
    await bridge.init_client(force_refresh=True)
    return {"success": True, "message": f"Đã chuyển sang tài khoản {acc.get('name')}", "data": acc}


@app.post("/api/accounts/add")
async def add_account(req: AddAccountRequest):
    """Thêm tài khoản Google mới bằng cookie và tự động kiểm tra quota."""
    try:
        acc = await account_manager.add_account(
            secure_1psid=req.secure_1psid,
            secure_1psidts=req.secure_1psidts,
            secure_1psidcc=req.secure_1psidcc or "",
            name=req.name or "",
            email=req.email or "",
            browser_source=req.browser_source or "Thủ công"
        )
        return {"success": True, "message": "Thêm tài khoản thành công", "data": acc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi thêm tài khoản: {str(e)}")


@app.post("/api/accounts/{account_id}/update-cookies")
async def update_account_cookies(account_id: str, req: UpdateCookiesRequest):
    """Cập nhật lại cookie mới cho một tài khoản cụ thể."""
    acc = await account_manager.update_cookies(
        account_id=account_id,
        psid=req.secure_1psid,
        psidts=req.secure_1psidts,
        psidcc=req.secure_1psidcc or ""
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản để cập nhật")
    return {"success": True, "message": "Đã cập nhật cookie thành công", "data": acc}


@app.post("/api/accounts/{account_id}/check-quota")
async def check_single_quota(account_id: str):
    """Kiểm tra quota và thời gian reset của một tài khoản cụ thể."""
    acc = await account_manager.check_quota(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    return {"success": True, "data": acc}


@app.post("/api/accounts/check-all")
async def check_all_quotas():
    """Kiểm tra quota toàn bộ các tài khoản."""
    updated = await account_manager.check_all_quotas()
    return {"success": True, "data": updated}


@app.post("/api/accounts/scan-browsers")
async def scan_browsers():
    """Tự động quét trình duyệt cục bộ và nạp tài khoản mới."""
    imported = await account_manager.scan_and_import_browsers()
    return {"success": True, "imported_count": len(imported), "data": imported}


@app.post("/api/accounts/toggle-failover")
async def toggle_failover(req: ToggleFailoverRequest):
    """Bật/tắt chế độ tự động chuyển tài khoản khi hết quota."""
    res = account_manager.toggle_auto_failover(req.enabled)
    return {"success": True, "auto_failover_enabled": res}


@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str):
    """Xóa một tài khoản khỏi Pool."""
    success = account_manager.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản để xóa")
    return {"success": True, "message": "Đã xóa tài khoản"}


# ==============================================================================
# OPENAI COMPATIBLE API & HEALTH
# ==============================================================================

@app.get("/health")
async def health_check():
    """Kiểm tra sức khỏe server và kết nối Gemini Web."""
    try:
        status_info = await bridge.get_status()
        return {"status": "ok", "gemini_web": status_info}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.get("/v1/models")
async def list_models():
    """Trả về danh sách models hỗ trợ theo chuẩn OpenAI API."""
    try:
        status_info = await bridge.get_status()
        available_models = status_info.get("available_models", ["gemini-pro", "gemini-flash"])
    except Exception:
        available_models = ["gemini-pro", "gemini-flash", "gemini-flash-lite", "gemini-argon"]

    models_data = []
    created_ts = int(time.time())
    for m in available_models:
        models_data.append({
            "id": m,
            "object": "model",
            "created": created_ts,
            "owned_by": "google-gemini-web",
            "permission": [],
            "root": m,
            "parent": None,
        })

    return {
        "object": "list",
        "data": models_data
    }


def format_messages_to_prompt(messages: List[ChatMessage]) -> str:
    if not messages:
        return ""

    if len(messages) == 1:
        c = messages[0].content
        return c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)

    system_instructions = []
    dialogue_turns = []

    for msg in messages:
        role = msg.role.lower()
        content = msg.content if isinstance(msg.content, str) else json.dumps(msg.content, ensure_ascii=False)
        if role == "system":
            system_instructions.append(content)
        elif role == "user":
            dialogue_turns.append(content)
        elif role == "assistant":
            dialogue_turns.append(f"Phản hồi trước: {content}")
        else:
            dialogue_turns.append(content)

    body = "\n\n".join(dialogue_turns)
    if system_instructions:
        sys_str = "\n".join(system_instructions)
        return f"{body}\n\n(Lưu ý & Hướng dẫn: {sys_str})"
    return body


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """Thực thi Chat Completions tương thích chuẩn OpenAI kèm Auto-Failover."""
    model_name = req.model or get_default_model()
    prompt = format_messages_to_prompt(req.messages)
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())

    if req.stream:
        async def event_generator():
            try:
                first_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(first_chunk, ensure_ascii=False)}\n\n"

                async for delta_text in bridge.generate_stream(
                    prompt=prompt,
                    model=model_name,
                    extended_thinking=True if req.extended_thinking is None else req.extended_thinking
                ):
                    chunk_obj = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model_name,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": delta_text},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_obj, ensure_ascii=False)}\n\n"

                final_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Lỗi stream: {e}")
                err_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"\n\n[Lỗi kết nối Gemini Web: {str(e)}]"},
                        "finish_reason": "error"
                    }]
                }
                yield f"data: {json.dumps(err_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    try:
        res = await bridge.generate(
            prompt=prompt,
            model=model_name,
            extended_thinking=True if req.extended_thinking is None else req.extended_thinking
        )
        content_text = res.get("text", "")
        images = res.get("images", [])
        if images:
            content_text += "\n\n**Ảnh từ Gemini:**\n" + "\n".join([f"- {url}" for url in images])

        return {
            "id": chat_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content_text.split()),
                "total_tokens": len(prompt.split()) + len(content_text.split())
            }
        }
    except Exception as e:
        logger.error(f"Lỗi khi xử lý completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi kết nối Gemini Web: {str(e)}"
        )


def start_proxy(host: str = "127.0.0.1", port: int = 8000):
    """Khởi chạy máy chủ Dashboard & Proxy."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_proxy()
