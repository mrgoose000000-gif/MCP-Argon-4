"""
MCP Server (Model Context Protocol) cho Google Gemini Web (gemini.google.com/app).
Tích hợp trực tiếp vào Antigravity IDE và Antigravity CLI (agy) với khả năng quản lý bể tài khoản.
"""

import sys
import json
import logging
from typing import Optional
try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    from mcp.server.mcpserver import MCPServer as FastMCP

from gemini2anti.client import bridge
from gemini2anti.account_manager import account_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiWebMCP")

mcp = FastMCP(
    name="gemini-web",
    instructions="Cầu nối tích hợp trực tiếp các model AI từ Google Gemini Web (gemini.google.com/app) vào Antigravity / agy"
)


@mcp.tool()
async def gemini_web_ask(
    prompt: str,
    model: str = "gemini-4",
    extended_thinking: bool = True
) -> str:
    """
    Gửi câu hỏi hoặc yêu cầu trực tiếp đến Google Gemini Web (gemini.google.com/app).
    Mặc định sử dụng model Gemini 4 High (Gemini 4 Argon kèm Extended Thinking suy luận sâu cao nhất).
    Hỗ trợ Auto-Failover: tự động chuyển tài khoản khác nếu tài khoản hiện tại hết quota.
    
    Args:
        prompt: Nội dung câu hỏi, prompt hoặc tài liệu cần phân tích.
        model: Tên model Gemini Web ('gemini-4' (mặc định - Gemini 4 Argon), 'gemini-flash', 'gemini-pro', 'auto').
        extended_thinking: Bật chế độ suy nghĩ mở rộng (Gemini Extended Thinking). Mặc định luôn là True (Gemini 4 High).
    
    Returns:
        Câu trả lời hoàn chỉnh từ Gemini Web kèm danh sách ảnh (nếu có).
    """
    try:
        res = await bridge.generate(prompt=prompt, model=model, extended_thinking=extended_thinking)
        text = res.get("text", "")
        images = res.get("images", [])
        if images:
            text += "\n\n**Ảnh đính kèm từ Gemini:**\n" + "\n".join([f"- {url}" for url in images])
        return text
    except Exception as e:
        logger.error(f"Lỗi khi gọi gemini_web_ask: {e}")
        return f"Lỗi kết nối Gemini Web: {str(e)}"


@mcp.tool()
async def gemini_web_chat(
    message: str,
    session_id: str = "default",
    model: str = "gemini-4",
    extended_thinking: bool = True
) -> str:
    """
    Trò chuyện nhiều lượt liên tục (Multi-turn Conversation) với Gemini Web.
    Mặc định sử dụng model Gemini 4 High (Gemini 4 Argon kèm Extended Thinking).
    """
    try:
        res = await bridge.chat(message=message, session_id=session_id, model=model, extended_thinking=extended_thinking)
        text = res.get("text", "")
        images = res.get("images", [])
        if images:
            text += "\n\n**Ảnh đính kèm:**\n" + "\n".join([f"- {url}" for url in images])
        return text
    except Exception as e:
        logger.error(f"Lỗi khi gọi gemini_web_chat: {e}")
        return f"Lỗi phiên chat Gemini Web: {str(e)}"


@mcp.tool()
async def gemini_web_account_info() -> str:
    """
    Kiểm tra trạng thái tài khoản Gemini Web đang kích hoạt: quota còn lại, thời gian reset, danh sách tài khoản trong Pool.
    
    Returns:
        Bản tóm tắt JSON định dạng đẹp về tình trạng tài khoản và model.
    """
    try:
        status = await bridge.get_status()
        accounts = account_manager.get_all_accounts()
        status["pool_summary"] = {
            "total_accounts": len(accounts),
            "accounts": [
                {
                    "name": a.get("name"),
                    "email": a.get("email"),
                    "is_active": a.get("is_active"),
                    "status": a.get("status"),
                    "quota_remaining": a.get("quota_remaining"),
                    "quota_reset_at": a.get("quota_reset_at")
                }
                for a in accounts
            ]
        }
        return json.dumps(status, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Lỗi kiểm tra thông tin tài khoản: {str(e)}"


@mcp.tool()
async def gemini_web_list_accounts() -> str:
    """
    Xem danh sách tất cả các tài khoản Google Gemini đã lưu trong hệ thống kèm Quota và trạng thái.
    """
    accounts = account_manager.get_all_accounts()
    if not accounts:
        return "Hiện chưa có tài khoản nào được lưu."

    lines = ["**Danh sách tài khoản Google Gemini:**\n"]
    for i, a in enumerate(accounts, 1):
        active_tag = "⭐ [ĐANG KÍCH HOẠT]" if a.get("is_active") else ""
        lines.append(
            f"{i}. **{a.get('name')}** (`{a.get('email')}`) {active_tag}\n"
            f"   - Trạng thái: `{a.get('status', 'UNKNOWN')}` | Gói: `{a.get('tier', 'PRO')}`\n"
            f"   - Quota còn lại: **{a.get('quota_remaining', 0)}/{a.get('quota_total', 600)} credits**\n"
            f"   - Thời gian Reset: `{a.get('quota_reset_at', 'Chưa rõ')}`\n"
            f"   - ID tài khoản: `{a.get('id')}`"
        )
    return "\n\n".join(lines)


@mcp.tool()
async def gemini_web_switch_account(account_id_or_email: str) -> str:
    """
    Chuyển đổi tài khoản Google Gemini đang sử dụng trong Antigravity.
    
    Args:
        account_id_or_email: ID tài khoản (ví dụ 'acc_primary') hoặc địa chỉ email tài khoản cần kích hoạt.
    """
    accounts = account_manager.get_all_accounts()
    target_id = None
    target_email = ""
    for a in accounts:
        if a.get("id") == account_id_or_email or a.get("email") == account_id_or_email:
            target_id = a.get("id")
            target_email = a.get("email")
            break

    if not target_id:
        return f"Không tìm thấy tài khoản tương ứng với '{account_id_or_email}'."

    acc = account_manager.switch_account(target_id)
    if acc:
        return f"Đã chuyển thành công sang tài khoản: **{acc.get('name')}** (`{acc.get('email')}`)."
    return "Lỗi khi chuyển tài khoản."


@mcp.tool()
async def gemini_web_deep_research(topic: str) -> str:
    """
    Kích hoạt tính năng Deep Research từ tài khoản Google Gemini Web.
    """
    try:
        res = await bridge.deep_research(topic=topic)
        return res.get("result", "")
    except Exception as e:
        logger.error(f"Lỗi khi chạy deep_research: {e}")
        return f"Lỗi Deep Research: {str(e)}"


@mcp.tool()
async def gemini_web_reset_session(session_id: str = "default") -> str:
    """
    Xóa lịch sử một phiên chat với Gemini Web để bắt đầu lại ngữ cảnh mới.
    """
    success = await bridge.reset_session(session_id=session_id)
    if success:
        return f"Đã xóa thành công phiên chat '{session_id}'."
    return f"Không tìm thấy phiên chat '{session_id}' hoặc phiên đã trống."


def main():
    """Hàm khởi chạy MCP Server qua stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
