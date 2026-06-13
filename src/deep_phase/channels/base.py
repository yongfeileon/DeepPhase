"""Channel 基类和消息定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MessageType(Enum):
    """消息类型"""
    OUTPUT = "output"
    ERROR = "error"
    STATUS = "status"


@dataclass
class Message:
    """统一消息格式"""
    type: MessageType
    content: str


class Channel(ABC):
    """Channel 抽象基类"""

    def __init__(self, name: str):
        self.name = name
        self.active = True

    @abstractmethod
    async def send(self, message: Message):
        """发送消息"""
        pass

    @abstractmethod
    async def receive(self) -> Optional[str]:
        """接收命令（非阻塞）"""
        pass

    async def start(self):
        """启动 channel"""
        pass

    async def stop(self):
        """停止 channel"""
        self.active = False
