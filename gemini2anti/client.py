"""
Module lõi quản lý kết nối và phiên làm việc với Google Gemini Web (gemini.google.com/app).
"""

import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Any
from gemini_webapi import GeminiClient
from gemini2anti.config import get_gemini_credentials, get_default_model, get_proxy


class GeminiWebBridge:
    """
    Quản lý phiên kết nối, xác thực và các tác vụ sinh nội dung với Gemini Web.
    """
    def __init__(self):
        self._client: Optional[GeminiClient] = None
        self._lock = asyncio.Lock()
        self._sessions: Dict[str, Any] = {}
        self._auth_source: str = ""
        self._available_models: List[str] = ["gemini-pro", "gemini-flash", "gemini-flash-lite", "gemini-argon"]

    async def init_client(self, force_refresh: bool = False) -> GeminiClient:
        """
        Khởi tạo hoặc trả về client hiện tại.
        Tự động lấy cookies và kết nối với Gemini Web.
        """
        async with self._lock:
            if self._client and not force_refresh:
                return self._client

            psid, psidts, psidcc, source = get_gemini_credentials()
            if not psid:
                raise ValueError(
                    "Không tìm thấy Cookie đăng nhập Gemini! "
                    "Hãy đăng nhập https://gemini.google.com trên Microsoft Edge/Chrome/Firefox "
                    "hoặc cấu hình GEMINI_SECURE_1PSID trong file .env."
                )

            self._auth_source = source
            proxy = get_proxy()

            client = GeminiClient(
                secure_1psid=psid,
                secure_1psidts=psidts,
                secure_1psidcc=psidcc,
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
                quotas_info[k] = {
                    "remaining": getattr(v, "remaining", None),
                    "total": getattr(v, "total", None),
                    "reset_time": str(getattr(v, "reset_time", None)),
                }

        abuse_status = getattr(client, "abuse_status", "clean")
        
        return {
            "status": "connected",
            "auth_source": self._auth_source,
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
        extended_thinking: bool = False,
        files: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Tạo phản hồi hoàn chỉnh từ Gemini Web.
        """
        last_err = None
        for attempt in range(3):
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
                if attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))

        raise last_err

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        extended_thinking: bool = False,
        files: Optional[List[Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream từng mẩu phản hồi (token delta) từ Gemini Web.
        """
        client = await self.init_client()
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
        extended_thinking: bool = False,
    ) -> Dict[str, Any]:
        """
        Gửi tin nhắn trong phiên hội thoại nhiều lượt (Multi-turn Chat Session).
        """
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
