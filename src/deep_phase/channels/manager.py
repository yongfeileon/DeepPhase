"""Channel 管理器"""

import asyncio
from typing import List, Dict, Callable, Optional
from .base import Channel, Message


class ChannelManager:
    """管理所有 channels 的消息广播和命令处理"""

    def __init__(self):
        self.channels: List[Channel] = []
        self.command_handlers: Dict[str, Callable] = {}
        self.natural_language_handler: Optional[Callable] = None
        self._listening = False

    def register_channel(self, channel: Channel):
        """注册 channel"""
        self.channels.append(channel)

    def register_command(self, command: str, handler: Callable):
        """注册命令处理函数"""
        self.command_handlers[command] = handler

    def set_natural_language_handler(self, handler: Callable):
        """设置自然语言处理器"""
        self.natural_language_handler = handler

    async def broadcast(self, message: Message):
        """广播消息到所有 channel"""
        await asyncio.gather(
            *[ch.send(message) for ch in self.channels if ch.active],
            return_exceptions=True
        )

    async def start_listening(self):
        """启动监听循环"""
        self._listening = True

        # 启动所有 channels
        for ch in self.channels:
            await ch.start()

        # 监听所有输入
        asyncio.create_task(self._listen_loop())

    async def _listen_loop(self):
        """监听循环"""
        while self._listening:
            for ch in self.channels:
                if not ch.active:
                    continue
                try:
                    cmd = await ch.receive()
                    if cmd:
                        await self._handle_input(cmd.strip())
                except Exception:
                    pass
            await asyncio.sleep(0.1)

    async def _handle_input(self, text: str):
        """处理用户输入（命令或自然语言）"""
        if text.startswith('/'):
            # 命令
            handler = self.command_handlers.get(text)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
        else:
            # 自然语言，传给处理器
            if self.natural_language_handler:
                if asyncio.iscoroutinefunction(self.natural_language_handler):
                    await self.natural_language_handler(text)
                else:
                    self.natural_language_handler(text)
