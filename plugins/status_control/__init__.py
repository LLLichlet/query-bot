"""
状态控制插件

管理员功能：查看和控制各功能开关状态、用户管理。
使用一次性令牌验证，令牌通过私聊 "/申请令牌" 获取，5分钟内有效。
"""
from typing import List, Tuple

try:
    from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PrivateMessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    BanServiceProtocol,
    TokenServiceProtocol,
    SystemMonitorProtocol,
    config,
)
from plugins.common.base import Result


class RequestTokenHandler(PluginHandler):
    """申请令牌处理器（私聊）"""
    
    name = "申请令牌"
    description = "私聊申请管理员操作令牌"
    command = "token"
    aliases = {"申请令牌"}
    priority = 10
    feature_name = None
    hidden_in_help = True
    
    ERROR_MESSAGES = {
        "not_private_chat": "Please send this command in private chat",
        "not_admin": "You don't have admin permission",
        "token_service_unavailable": "Token service unavailable",
    }
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理令牌申请（仅私聊）"""
        if not isinstance(event, PrivateMessageEvent):
            await self.reply(self.get_error_message("not_private_chat"))
            return
        
        user_id = event.user_id
        
        if user_id not in config.admin_user_ids_set:
            await self.reply(self.get_error_message("not_admin"))
            return
        
        token_service = ServiceLocator.get(TokenServiceProtocol)
        if token_service is None:
            await self.reply(self.get_error_message("token_service_unavailable"))
            return
        
        token = token_service.generate_token(user_id)
        
        await self.send(
            f"Your token: {token}\n"
            f"Valid for: 5 minutes\n"
            f"Usage: Send \"admin {token} [operation]\" in group\n"
            f"Available: toggle/ban/unban/status/system",
            finish=True
        )


class StatusControlHandler(PluginHandler):
    """状态控制处理器"""
    
    name = "状态控制"
    description = "管理员功能：查看和控制各功能开关状态"
    command = "admin"
    aliases = {"状态控制", "状态", "控制"}
    priority = 100
    feature_name = None
    hidden_in_help = True
    
    CONTROLLABLE_FEATURES: List[Tuple[str, str, str]] = [
        ("math", "数学定义", "数学"),
        ("random", "随机回复", "随机"),
        ("highnoon", "午时已到", "午时已到"),
        ("pjskpartiton", "PJSK谱面", "PJSK"),
        ("math_soup", "数学谜题", "数学谜"),
    ]
    
    ERROR_MESSAGES = {
        "not_admin": "You don't have admin permission",
        "token_service_unavailable": "Token service unavailable",
        "token_invalid": "Invalid or expired token. Please request a new one via private chat.",
        "ban_service_unavailable": "Ban service unavailable",
        "monitor_service_unavailable": "System monitor unavailable",
        "invalid_user_id": "User ID must be a number",
    }
    
    def _check_admin(self, user_id: int) -> bool:
        """检查是否为管理员"""
        return user_id in config.admin_user_ids_set
    
    def _verify_token(self, user_id: int, token: str) -> Result[bool]:
        """验证令牌"""
        token_service = ServiceLocator.get(TokenServiceProtocol)
        if token_service is None:
            return self.err("token_service_unavailable")
        
        if not token_service.verify_token(user_id, token):
            return self.err("token_invalid")
        
        return self.ok(True)
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理状态控制命令"""
        user_id = event.user_id
        
        if not self._check_admin(user_id):
            await self.reply(self.get_error_message("not_admin"))
            return
        
        if not args:
            await self._show_status()
            return
        
        parts = args.split(maxsplit=1)
        token = parts[0]
        remaining = parts[1] if len(parts) > 1 else ""
        
        # 验证令牌
        token_result = self._verify_token(user_id, token)
        if token_result.is_failure:
            await self.reply(self.get_error_message(token_result.error))
            return
        
        if not remaining:
            await self._show_status()
            return
        
        action_parts = remaining.split(maxsplit=1)
        action = action_parts[0].lower()
        action_args = action_parts[1] if len(action_parts) > 1 else ""
        
        if action == "toggle":
            await self._handle_toggle(action_args)
        elif action == "ban":
            await self._handle_ban(action_args)
        elif action == "unban":
            await self._handle_unban(action_args)
        elif action == "status":
            await self._show_status()
        elif action == "system":
            await self._show_system_status()
        else:
            await self.reply(f"Unknown operation: {action}. Available: toggle/ban/unban/status/system")
    
    async def _show_status(self) -> None:
        """显示所有功能状态"""
        lines = ["Feature status:"]
        
        for feature_key, display_name, _ in self.CONTROLLABLE_FEATURES:
            is_enabled = config.is_enabled(feature_key)
            status = "[ON]" if is_enabled else "[OFF]"
            lines.append(f"  {display_name}: {status}")
        
        ban = ServiceLocator.get(BanServiceProtocol)
        banned_count = ban.get_banned_count() if ban else 0
        lines.append(f"\nBanned users: {banned_count}")
        
        await self.send("\n".join(lines), finish=True)
    
    async def _handle_toggle(self, args: str) -> None:
        """处理功能开关"""
        if not args:
            await self.reply("Please specify feature name, e.g.: toggle math")
            return
        
        target = args.strip().lower()
        
        matched_feature = None
        for feature_key, display_name, short_name in self.CONTROLLABLE_FEATURES:
            if target in feature_key or target in display_name.lower() or target == short_name.lower():
                matched_feature = (feature_key, display_name)
                break
        
        if not matched_feature:
            available = ", ".join([name for _, name, _ in self.CONTROLLABLE_FEATURES])
            await self.send(f"Unknown feature. Available: {available}", finish=True)
            return
        
        feature_key, display_name = matched_feature
        
        current_value = getattr(config, f"{feature_key}_enabled", True)
        setattr(config, f"{feature_key}_enabled", not current_value)
        new_status = "ON" if not current_value else "OFF"
        
        await self.send(f"{display_name} is now {new_status}", finish=True)
    
    async def _handle_ban(self, user_id_str: str) -> None:
        """处理拉黑用户"""
        if not user_id_str.strip():
            await self.reply("Please specify user ID, e.g.: ban 123456")
            return
        
        try:
            target_user_id = int(user_id_str.strip())
        except ValueError:
            await self.reply(self.get_error_message("invalid_user_id"))
            return
        
        ban = ServiceLocator.get(BanServiceProtocol)
        if ban is None:
            await self.reply(self.get_error_message("ban_service_unavailable"))
            return
        
        if ban.is_banned(target_user_id):
            await self.send(f"User {target_user_id} is already banned", finish=True)
            return
        
        result = ban.ban(target_user_id)
        if result.is_success:
            await self.send(f"User {target_user_id} has been banned", finish=True)
        else:
            await self.send(f"Ban failed: {result.error}", finish=True)
    
    async def _handle_unban(self, user_id_str: str) -> None:
        """处理解封用户"""
        if not user_id_str.strip():
            await self.reply("Please specify user ID, e.g.: unban 123456")
            return
        
        try:
            target_user_id = int(user_id_str.strip())
        except ValueError:
            await self.reply(self.get_error_message("invalid_user_id"))
            return
        
        ban = ServiceLocator.get(BanServiceProtocol)
        if ban is None:
            await self.reply(self.get_error_message("ban_service_unavailable"))
            return
        
        if not ban.is_banned(target_user_id):
            await self.send(f"User {target_user_id} is not banned", finish=True)
            return
        
        result = ban.unban(target_user_id)
        if result.is_success:
            await self.send(f"User {target_user_id} has been unbanned", finish=True)
        else:
            await self.send(f"Unban failed: {result.error}", finish=True)
    
    async def _show_system_status(self) -> None:
        """显示系统状态"""
        monitor = ServiceLocator.get(SystemMonitorProtocol)
        if monitor is None:
            await self.send(self.get_error_message("monitor_service_unavailable"), finish=True)
            return
        
        status_text = monitor.get_status_text()
        await self.send(status_text, finish=True)


# 创建处理器和接收器
request_token_handler = RequestTokenHandler()
status_control_handler = StatusControlHandler()

request_token_receiver = CommandReceiver(request_token_handler)
status_control_receiver = CommandReceiver(status_control_handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="状态控制",
        description="管理员功能：查看和控制各功能开关状态（需令牌）",
        usage="私聊: /token (申请令牌) | 群内: /admin (状态控制) [令牌] [操作] [参数]",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
