"""
Module lõi quản lý kết nối và phiên làm việc với Google Gemini Web (gemini.google.com/app).
Tích hợp quản lý đa tài khoản và Auto-Failover xoay vòng tài khoản khi hết quota.
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any
from gemini_webapi import GeminiClient
from gemini2anti.config import get_gemini_credentials, get_default_model, get_default_extended_thinking, get_proxy
from gemini2anti.account_manager import account_manager

logger = logging.getLogger("GeminiClient")


class GeminiWebBridge:
    """
    Quản lý phiên kết nối, xác thực và các tác vụ sinh nội dung với Gemini Web.
    Hỗ trợ xoay vòng tài khoản tự động (Auto-Failover).
    """
    def __init__(self):
        self._client: Optional[GeminiClient] = None
        self._current_account_id: Optional[str] = None
        self._lock = asyncio.Lock()
        self._sessions: Dict[str, Any] = {}
        self._auth_source: str = ""
        self._available_models: List[str] = ["gemini-pro", "gemini-flash", "gemini-flash-lite", "gemini-argon"]

    async def init_client(self, force_refresh: bool = False) -> GeminiClient:
        """
        Khởi tạo hoặc trả về client hiện tại.
        Ưu tiên lấy thông tin từ tài khoản đang Active trong AccountManager.
        """
        async with self._lock:
            active_acc = account_manager.get_active_account()
            active_id = active_acc["id"] if active_acc else None

            # Nếu tài khoản đã đổi hoặc force_refresh thì tạo mới client
            if self._client and not force_refresh and self._current_account_id == active_id:
                return self._client

            if active_acc and active_acc.get("secure_1psid"):
                psid = active_acc["secure_1psid"]
                psidts = active_acc.get("secure_1psidts")
                psidcc = active_acc.get("secure_1psidcc")
                source = f"Account Pool: {active_acc.get('email')} ({active_acc.get('name')})"
                self._current_account_id = active_id
            else:
                psid, psidts, psidcc, source = get_gemini_credentials()
                self._current_account_id = "default_env"

            if not psid:
                raise ValueError(
                    "Không tìm thấy Cookie đăng nhập Gemini! "
                    "Hãy mở Dashboard (http://127.0.0.1:8000/dashboard) để thêm tài khoản "
                    "hoặc đăng nhập https://gemini.google.com trên Chrome/Edge."
                )

            self._auth_source = source
            proxy = get_proxy()

            client = GeminiClient(
                secure_1psid=psid,
                secure_1psidts=psidts or None,
                secure_1psidcc=psidcc or None,
                proxy=proxy,
            )

            # Thử nghiệm kết nối với cơ chế retry tự động
            last_err = None
            for attempt in range(3):
                try:
                    await client.init(timeout=25)
                    self._client = client
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    if attempt < 2:
                        await asyncio.sleep(1.5 * (attempt + 1))

            if last_err is not None:
                raise last_err

            try:
                models = client.list_models()
                if models:
                    self._available_models = [m.model_name for m in models]
            except Exception:
                pass

            return self._client

    async def get_status(self) -> Dict[str, Any]:
        """
        Lấy thông tin trạng thái tài khoản, quota, abuse status và các model khả dụng.
        """
        client = await self.init_client()
        quotas_info = {}
        if hasattr(client, "quotas") and client.quotas:
            for k, v in client.quotas.items():
                if isinstance(v, dict):
                    quotas_info[k] = v
                else:
                    quotas_info[k] = {
                        "remaining": getattr(v, "remaining", None),
                        "total": getattr(v, "total", None),
                        "reset_time": str(getattr(v, "reset_time", None)),
                    }

        abuse_status = getattr(client, "abuse_status", "clean")
        active_acc = account_manager.get_active_account()

        return {
            "status": "connected",
            "auth_source": self._auth_source,
            "active_account": {
                "name": active_acc.get("name") if active_acc else "Unknown",
                "email": active_acc.get("email") if active_acc else "Unknown",
                "tier": active_acc.get("tier", "PRO") if active_acc else "PRO",
                "quota_remaining": active_acc.get("quota_remaining") if active_acc else None,
                "quota_reset_at": active_acc.get("quota_reset_at") if active_acc else None,
            },
            "abuse_status": abuse_status,
            "quotas": quotas_info,
            "available_models": self._available_models,
            "default_model": get_default_model(),
        }

    def _resolve_model(self, client: GeminiClient, model_name: Optional[str]) -> Optional[Any]:
        """Tìm model phù hợp trong registry của Gemini Web, mặc định tuyệt đối là Gemini 4 Argon."""
        if not model_name:
            model_name = get_default_model()

        name_clean = model_name.lower().strip()
        if name_clean in ["auto", "default", "gemini", "gemini-web", "current", "gemini-4", "gemini 4", "gemini4", "argon", "gemini-argon", "4-argon", "4 argon"]:
            try:
                return client.resolve_model("gemini-argon")
            except Exception:
                pass

        alias_map = {
            "gemini-4": "gemini-argon",
            "gemini 4": "gemini-argon",
            "gemini4": "gemini-argon",
            "gemini-4-argon": "gemini-argon",
            "4-argon": "gemini-argon",
            "4 argon": "gemini-argon",
            "argon": "gemini-argon",
            "gemini-3.8-flash": "gemini-flash",
            "gemini-flash": "gemini-flash",
            "flash": "gemini-flash",
            "gemini-3.1-pro": "gemini-pro",
            "gemini-pro": "gemini-pro",
            "pro": "gemini-pro",
            "gemini-flash-lite": "gemini-flash-lite",
            "flash-lite": "gemini-flash-lite",
            "gpt-4": "gemini-argon",
            "gpt-4o": "gemini-flash",
            "claude-3-5-sonnet": "gemini-argon",
        }
        target = alias_map.get(name_clean, name_clean)
        try:
            return client.resolve_model(target)
        except Exception:
            try:
                return client.resolve_model("gemini-argon")
            except Exception:
                return None

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
        files: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Tạo phản hồi hoàn chỉnh từ Gemini Web (mặc định Gemini 4 High - Extended Thinking).
        Hỗ trợ Auto-Failover: tự động xoay vòng sang tài khoản tiếp theo nếu tài khoản hiện tại hết quota.
        """
        if extended_thinking is None:
            extended_thinking = get_default_extended_thinking()

        max_attempts = 4
        last_err = None

        for attempt in range(max_attempts):
            try:
                client = await self.init_client(force_refresh=(attempt > 0))
                resolved_model = self._resolve_model(client, model)

                response = await client.generate_content(
                    prompt=prompt,
                    model=resolved_model,
                    extended_thinking=extended_thinking,
                    files=files,
                )
                return {
                    "text": response.text,
                    "model": model or get_default_model(),
                    "images": [getattr(img, "url", "") for img in getattr(response, "images", [])],
                    "thoughts": getattr(response, "thoughts", None),
                }
            except Exception as e:
                last_err = e
                err_msg = str(e).lower()
                logger.warning(f"Lỗi lượt {attempt+1}: {e}")

                # Nhận diện lỗi hết quota hoặc bị hạn chế lượt gọi
                is_quota_issue = any(term in err_msg for term in [
                    "quota", "429", "rate limit", "credits", "exhausted", "abuse", "limit exceeded"
                ])

                if is_quota_issue and attempt < max_attempts - 1:
                    next_acc = account_manager.rotate_to_next_account()
                    if next_acc:
                        logger.info(f"⚡ [Auto-Failover] Đã tự động chuyển sang tài khoản: {next_acc.get('email')}")
                        async with self._lock:
                            self._client = None
                        await asyncio.sleep(1)
                        continue

                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.5 * (attempt + 1))

        raise last_err

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
        files: Optional[List[Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream từng mẩu phản hồi (token delta) từ Gemini Web kèm Auto-Failover.
        """
        if extended_thinking is None:
            extended_thinking = get_default_extended_thinking()

        try:
            client = await self.init_client()
        except Exception:
            next_acc = account_manager.rotate_to_next_account()
            if next_acc:
                async with self._lock:
                    self._client = None
                client = await self.init_client()
            else:
                raise

        resolved_model = self._resolve_model(client, model)

        last_length = 0
        async for chunk in client.generate_content_stream(
            prompt=prompt,
            model=resolved_model,
            extended_thinking=extended_thinking,
            files=files,
        ):
            current_text = chunk.text or ""
            if len(current_text) > last_length:
                delta = current_text[last_length:]
                last_length = len(current_text)
                yield delta

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        model: Optional[str] = None,
        extended_thinking: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Gửi tin nhắn trong phiên hội thoại nhiều lượt (Multi-turn Chat Session).
        """
        if extended_thinking is None:
            extended_thinking = get_default_extended_thinking()

        client = await self.init_client()
        resolved_model = self._resolve_model(client, model)

        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = client.start_chat(model=resolved_model)
            chat_session = self._sessions[session_id]

        response = await chat_session.send_message(
            prompt=message,
            extended_thinking=extended_thinking,
        )

        return {
            "text": response.text,
            "session_id": session_id,
            "model": model or get_default_model(),
            "images": [getattr(img, "url", "") for img in getattr(response, "images", [])],
        }

    async def reset_session(self, session_id: str = "default") -> bool:
        """Đặt lại phiên hội thoại."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    async def deep_research(self, topic: str) -> Dict[str, Any]:
        """
        Kích hoạt tính năng Deep Research của Google Gemini Web.
        """
        client = await self.init_client()
        result = await client.deep_research(topic)
        return {
            "topic": topic,
            "result": getattr(result, "text", str(result)),
        }


# Global singleton instance
bridge = GeminiWebBridge()
