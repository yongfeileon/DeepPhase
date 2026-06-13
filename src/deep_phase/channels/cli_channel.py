"""CLI Channel 实现"""

import sys
import asyncio
import threading
from .base import Channel, Message, MessageType


class CLIChannel(Channel):
    """命令行交互 Channel"""

    def __init__(self):
        super().__init__("CLI")
        self._input_queue = asyncio.Queue()
        self._listener_thread = None
        self._stop_event = threading.Event()

    async def send(self, message: Message):
        """输出到终端"""
        stream = sys.stderr if message.type == MessageType.ERROR else sys.stdout
        prefix = {
            MessageType.ERROR: "[错误] ",
            MessageType.STATUS: "[状态] ",
            MessageType.OUTPUT: ""
        }.get(message.type, "")
        print(f"{prefix}{message.content}", file=stream, flush=True)

    async def receive(self) -> str:
        """接收 stdin 输入"""
        try:
            return self._input_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def start(self):
        """启动 stdin 监听"""
        self._listener_thread = threading.Thread(target=self._listen_stdin_thread, daemon=True)
        self._listener_thread.start()

    def _listen_stdin_thread(self):
        """在独立线程中监听 stdin"""
        while not self._stop_event.is_set() and self.active:
            try:
                line = sys.stdin.readline()
                if line:
                    # 使用 call_soon_threadsafe 在事件循环中安全地添加到队列
                    asyncio.get_event_loop().call_soon_threadsafe(
                        self._input_queue.put_nowait, line.strip()
                    )
            except Exception:
                break
