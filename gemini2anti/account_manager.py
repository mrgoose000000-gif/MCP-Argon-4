"""
Quản lý bể tài khoản (Account Pool), kiểm tra quota, tự động chuyển đổi khi hết hạn mức (Auto-Failover).
Đã chuẩn hóa phân biệt giữa Hạn ngạch 5 Giờ (5h Window) và Hạn ngạch Tuần (Weekly Cap).
"""

import os
import sys
import json
import time
import re
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import httpx
from gemini_webapi import GeminiClient
from gemini_webapi.client import AccountStatus
from gemini2anti.config import extract_cookies_from_browser, HAS_ROOKIEPY

REPO_DIR = Path(__file__).resolve().parent.parent
ACCOUNTS_FILE = REPO_DIR / "accounts.json"
ENV_FILE = REPO_DIR / ".env"


class AccountManager:
    """Quản lý danh sách tài khoản Google Gemini Web và điều phối Auto-Failover."""

    def __init__(self, filepath: Path = ACCOUNTS_FILE):
        self.filepath = filepath
        self._lock = asyncio.Lock()
        self._init_storage()

    def _init_storage(self):
        """Khởi tạo accounts.json nếu chưa có."""
        if not self.filepath.exists():
            default_data = {
                "active_account_id": None,
                "auto_failover_enabled": True,
                "accounts": []
            }
            self._save_data(default_data)

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"active_account_id": None, "auto_failover_enabled": True, "accounts": []}

    def _save_data(self, data: Dict[str, Any]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_data(self) -> Dict[str, Any]:
        return self._load_data()

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        return self._load_data().get("accounts", [])

    def get_active_account(self) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        active_id = data.get("active_account_id")
        accounts = data.get("accounts", [])
        for acc in accounts:
            if acc["id"] == active_id:
                return acc
        if accounts:
            return accounts[0]
        return None

    def switch_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        target_acc = None
        for acc in data.get("accounts", []):
            if acc["id"] == account_id:
                acc["is_active"] = True
                target_acc = acc
            else:
                acc["is_active"] = False

        if target_acc:
            data["active_account_id"] = account_id
            self._save_data(data)
            self._sync_to_env(target_acc)
            return target_acc
        return None

    def _sync_to_env(self, acc: Dict[str, Any]):
        try:
            env_content = (
                f"# Tự động cập nhật bởi Dashboard AccountManager ({acc.get('email', 'Account')})\n"
                f"GEMINI_AUTO_BROWSER_COOKIES=false\n"
                f"GEMINI_SECURE_1PSID={acc.get('secure_1psid', '')}\n"
                f"GEMINI_SECURE_1PSIDTS={acc.get('secure_1psidts', '')}\n"
                f"GEMINI_SECURE_1PSIDCC={acc.get('secure_1psidcc', '')}\n"
                f"GEMINI_DEFAULT_MODEL=gemini-4\n"
                f"GEMINI_EXTENDED_THINKING=true\n"
            )
            ENV_FILE.write_text(env_content, encoding="utf-8")
        except Exception:
            pass

    async def fetch_account_profile_and_quota(
        self, psid: str, psidts: str, psidcc: str = ""
    ) -> Dict[str, Any]:
        """Gọi thực tế đến Google Gemini Web để lấy thông tin Email, Tên, Quota và Reset Time."""
        profile_info = {"name": "", "email": ""}
        quota_info = {
            "tier": "FREE",
            "quota_remaining": 0,
            "quota_total": 600,
            "quota_reset_at": "Chưa cập nhật",
            "quota_reset_raw": None,
            "status": "UNKNOWN"
        }

        # 1. Thử lấy thông tin Email & Name từ HTML gemini.google.com/app
        try:
            cookies = {"__Secure-1PSID": psid}
            if psidts:
                cookies["__Secure-1PSIDTS"] = psidts
            if psidcc:
                cookies["__Secure-1PSIDCC"] = psidcc

            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as http_client:
                r = await http_client.get(
                    "https://gemini.google.com/app",
                    cookies=cookies,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                    }
                )
                html = r.text
                email_match = re.search(r"<div>([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)</div>", html)
                name_match = re.search(r"<div class=\"gb_[a-zA-Z0-9]+\">([^<]+)</div><div>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+</div>", html)
                if email_match:
                    profile_info["email"] = email_match.group(1)
                if name_match:
                    profile_info["name"] = name_match.group(1)
        except Exception:
            pass

        # 2. Khởi tạo GeminiClient để bóc tách Quotas thực tế từ Google RPC
        try:
            client = GeminiClient(
                secure_1psid=psid,
                secure_1psidts=psidts or None,
                secure_1psidcc=psidcc or None
            )
            await client.init(timeout=15)

            # Kiểm tra trạng thái xác thực
            if client.account_status == AccountStatus.UNAUTHENTICATED:
                quota_info.update({
                    "status": "EXPIRED",
                    "tier": "EXPIRED",
                    "quota_remaining": 0,
                    "quota_total": 0,
                    "quota_reset_at": "Cookie hết hạn - Cần dán lại"
                })
                return {"profile": profile_info, "quota": quota_info}

            raw_quotas = getattr(client, "quotas", {}) or {}
            abuse = getattr(client, "abuse_status", None)
            usage_info = raw_quotas.get("usage_info") or {}
            current_5h = usage_info.get("current_5h") or {}
            weekly = usage_info.get("weekly") or {}

            # ƯU TIÊN 1: Lấy hạn ngạch chu kỳ 5 giờ (Chuẩn nhất của Google Gemini Web)
            if current_5h and current_5h.get("remaining_credits") is not None:
                remaining = current_5h.get("remaining_credits", 600)
                usage_level = current_5h.get("usage_level", 0)
                
                # Tính tổng hạn ngạch:
                # - Nếu usage_level == 0 (chưa dùng credit nào trong chu kỳ), total = remaining (ví dụ 2400 hoặc 600)
                # - Nếu đang dùng dở (0 < usage_level < 1), total = remaining / (1 - usage_level)
                if usage_level > 0 and usage_level < 1:
                    calc_total = int(round(remaining / (1 - usage_level)))
                    total = max(remaining, calc_total)
                else:
                    total = max(600, remaining)

                reset_at_str = current_5h.get("reset_at", "")
                formatted_reset = ""
                if reset_at_str:
                    try:
                        dt = datetime.fromisoformat(reset_at_str)
                        formatted_reset = dt.strftime("%H:%M") + " (Chu kỳ 5h)"
                    except Exception:
                        formatted_reset = str(reset_at_str)

                # Xác định hạng tài khoản:
                # Nếu chu kỳ 5h có từ 1500 credits trở lên -> Tài khoản Advanced / Google One AI Premium
                tier = "ADVANCED" if (total >= 1500 or remaining >= 1500) else "FREE"

                status = "HEALTHY"
                if remaining <= 0:
                    status = "RATE_LIMITED"
                elif abuse and isinstance(abuse, dict) and not abuse.get("is_clean", True):
                    status = "FLAGGED"

                quota_info.update({
                    "tier": tier,
                    "quota_remaining": remaining,
                    "quota_total": total,
                    "quota_reset_at": formatted_reset,
                    "quota_reset_raw": reset_at_str,
                    "status": status
                })
            else:
                # Dự phòng: Trường hợp không có current_5h, lấy từ action limits
                q_pro = raw_quotas.get("None-4") or raw_quotas.get("None-11") or {}
                rem = q_pro.get("remaining", 600)
                tot = q_pro.get("total", 600)
                if tot > 5000:
                    # Nếu là số tuần (ví dụ 12096), chuẩn hóa về chu kỳ 5h
                    tot = 600
                    rem = min(600, rem)

                quota_info.update({
                    "tier": "FREE",
                    "quota_remaining": rem,
                    "quota_total": tot,
                    "quota_reset_at": "Chu kỳ 5h",
                    "status": "HEALTHY" if rem > 0 else "RATE_LIMITED"
                })

        except Exception as e:
            err_str = str(e).lower()
            if "unauthenticated" in err_str or "cookie" in err_str or "login" in err_str:
                quota_info["status"] = "EXPIRED"
                quota_info["quota_reset_at"] = "Cookie hết hạn"
            else:
                quota_info["status"] = "ERROR"

        return {"profile": profile_info, "quota": quota_info}

    async def add_account(
        self,
        secure_1psid: str,
        secure_1psidts: str,
        secure_1psidcc: str = "",
        name: str = "",
        email: str = "",
        browser_source: str = "Thủ công"
    ) -> Dict[str, Any]:
        data = self._load_data()
        for acc in data.get("accounts", []):
            if acc.get("secure_1psid") == secure_1psid:
                acc["secure_1psidts"] = secure_1psidts
                acc["secure_1psidcc"] = secure_1psidcc
                self._save_data(data)
                await self.check_quota(acc["id"])
                return acc

        info = await self.fetch_account_profile_and_quota(secure_1psid, secure_1psidts, secure_1psidcc)
        prof = info["profile"]
        q = info["quota"]

        final_email = email.strip() or prof.get("email") or f"gemini_{int(time.time())}@google.com"
        final_name = name.strip() or prof.get("name") or final_email.split("@")[0]

        acc_id = f"acc_{int(time.time())}_{len(data.get('accounts', [])) + 1}"
        is_first = len(data.get("accounts", [])) == 0

        new_acc = {
            "id": acc_id,
            "name": final_name,
            "email": final_email,
            "secure_1psid": secure_1psid,
            "secure_1psidts": secure_1psidts,
            "secure_1psidcc": secure_1psidcc,
            "is_active": is_first,
            "status": q.get("status", "HEALTHY"),
            "tier": q.get("tier", "FREE"),
            "quota_remaining": q.get("quota_remaining", 600),
            "quota_total": q.get("quota_total", 600),
            "quota_reset_at": q.get("quota_reset_at", "Chưa cập nhật"),
            "quota_reset_raw": q.get("quota_reset_raw"),
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "browser_source": browser_source,
            "error_count": 0
        }

        data.setdefault("accounts", []).append(new_acc)
        if is_first:
            data["active_account_id"] = acc_id
            self._sync_to_env(new_acc)

        self._save_data(data)
        return new_acc

    async def check_quota(self, account_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            data = self._load_data()
            target = None
            for acc in data.get("accounts", []):
                if acc["id"] == account_id:
                    target = acc
                    break

            if not target:
                return None

            psid = target.get("secure_1psid", "")
            psidts = target.get("secure_1psidts", "")
            psidcc = target.get("secure_1psidcc", "")

        info = await self.fetch_account_profile_and_quota(psid, psidts, psidcc)
        prof = info["profile"]
        q = info["quota"]

        # CƠ CHẾ TỰ ĐỘNG LÀM MỚI (SELF-HEALING AUTO-REFRESH TỪ TRÌNH DUYỆT):
        # Nếu cookie bị hết hạn nhưng trình duyệt trên máy đã cập nhật cookie mới, tự động đồng bộ lại ngay lập tức!
        if q.get("status") == "EXPIRED" and HAS_ROOKIEPY:
            for b in ["chrome", "edge", "firefox", "brave"]:
                try:
                    cks = extract_cookies_from_browser(b)
                    fresh_psid = cks.get("__Secure-1PSID")
                    fresh_psidts = cks.get("__Secure-1PSIDTS")
                    fresh_psidcc = cks.get("__Secure-1PSIDCC", "")
                    if fresh_psid and fresh_psidts and (fresh_psidts != psidts or fresh_psid != psid):
                        fresh_info = await self.fetch_account_profile_and_quota(fresh_psid, fresh_psidts, fresh_psidcc)
                        if fresh_info["quota"].get("status") == "HEALTHY":
                            fresh_email = fresh_info["profile"].get("email")
                            target_email = target.get("email")
                            if not target_email or fresh_email == target_email or target.get("id") == "acc_primary":
                                psid, psidts, psidcc = fresh_psid, fresh_psidts, fresh_psidcc
                                info = fresh_info
                                prof = info["profile"]
                                q = info["quota"]
                                target["secure_1psid"] = fresh_psid
                                target["secure_1psidts"] = fresh_psidts
                                target["secure_1psidcc"] = fresh_psidcc
                                target["browser_source"] = f"{b.upper()} (Tự động đồng bộ)"
                                print(f"[Auto-Heal] 🔄 Đã tự động cập nhật cookie mới từ trình duyệt {b.upper()} cho tài khoản {target.get('name')}!")
                                break
                except Exception:
                    pass

        async with self._lock:
            data = self._load_data()
            target = None
            for acc in data.get("accounts", []):
                if acc["id"] == account_id:
                    target = acc
                    break
            if not target:
                return None

            if prof.get("email") and (not target.get("email") or "gemini_" in target.get("email")):
                target["email"] = prof["email"]
            if prof.get("name") and target.get("name") in ["", "User", "Mr Goose"]:
                target["name"] = prof["name"]

            target["status"] = q.get("status", "UNKNOWN")
            target["tier"] = q.get("tier", "FREE")
            target["quota_remaining"] = q.get("quota_remaining", 0)
            target["quota_total"] = max(target["quota_remaining"], q.get("quota_total", 600))
            if target["quota_total"] >= 1500:
                target["tier"] = "ADVANCED"
            target["quota_reset_at"] = q.get("quota_reset_at", "")
            target["quota_reset_raw"] = q.get("quota_reset_raw")
            target["last_checked"] = datetime.now(timezone.utc).isoformat()
            target["error_count"] = 0 if q.get("status") == "HEALTHY" else target.get("error_count", 0) + 1

            self._save_data(data)
            return target

    async def check_all_quotas(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        accounts = data.get("accounts", [])
        tasks = [self.check_quota(acc["id"]) for acc in accounts]
        await asyncio.gather(*tasks, return_exceptions=True)
        return self.get_all_accounts()

    def delete_account(self, account_id: str) -> bool:
        data = self._load_data()
        accounts = data.get("accounts", [])
        new_accs = [acc for acc in accounts if acc["id"] != account_id]
        if len(new_accs) == len(accounts):
            return False

        data["accounts"] = new_accs
        if data.get("active_account_id") == account_id:
            if new_accs:
                data["active_account_id"] = new_accs[0]["id"]
                new_accs[0]["is_active"] = True
                self._sync_to_env(new_accs[0])
            else:
                data["active_account_id"] = None

        self._save_data(data)
        return True

    def rotate_to_next_account(self) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        if not data.get("auto_failover_enabled", True):
            return None

        accounts = data.get("accounts", [])
        if len(accounts) <= 1:
            return None

        current_active_id = data.get("active_account_id")
        current_idx = 0
        for i, acc in enumerate(accounts):
            if acc["id"] == current_active_id:
                current_idx = i
                acc["status"] = "RATE_LIMITED"
                acc["quota_remaining"] = 0
                break

        for offset in range(1, len(accounts)):
            next_idx = (current_idx + offset) % len(accounts)
            candidate = accounts[next_idx]
            if candidate.get("status") in ["HEALTHY", "UNKNOWN"] and (candidate.get("quota_remaining", 0) > 0):
                self.switch_account(candidate["id"])
                print(f"[Auto-Failover] ⚡ Đã tự động đổi sang tài khoản: {candidate.get('email')} ({candidate.get('name')})")
                return candidate

        return None

    def toggle_auto_failover(self, enabled: bool) -> bool:
        data = self._load_data()
        data["auto_failover_enabled"] = enabled
        self._save_data(data)
        return enabled

    async def scan_and_import_browsers(self) -> List[Dict[str, Any]]:
        imported = []
        if not HAS_ROOKIEPY:
            return imported

        for b in ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]:
            try:
                cks = extract_cookies_from_browser(b)
                psid = cks.get("__Secure-1PSID")
                psidts = cks.get("__Secure-1PSIDTS")
                psidcc = cks.get("__Secure-1PSIDCC", "")
                if psid:
                    acc = await self.add_account(
                        secure_1psid=psid,
                        secure_1psidts=psidts or "",
                        secure_1psidcc=psidcc,
                        browser_source=f"Trình duyệt {b.upper()}"
                    )
                    imported.append(acc)
            except Exception:
                pass

        return imported


    async def update_cookies(
        self, account_id: str, psid: str, psidts: str, psidcc: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Cập nhật lại cookie mới cho một tài khoản cụ thể và kiểm tra lại quota."""
        async with self._lock:
            data = self._load_data()
            target = None
            for acc in data.get("accounts", []):
                if acc["id"] == account_id:
                    target = acc
                    break

            if not target:
                return None

            target["secure_1psid"] = psid
            target["secure_1psidts"] = psidts
            target["secure_1psidcc"] = psidcc
            self._save_data(data)

            if target.get("is_active"):
                self._sync_to_env(target)

        return await self.check_quota(account_id)


account_manager = AccountManager()
