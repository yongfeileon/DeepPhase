"""ClaudeSDKClient 管理器 - 统一创建和管理所有 Claude 客户端实例"""

from typing import TYPE_CHECKING
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

if TYPE_CHECKING:
    from .env_manager import EnvManager


class ClaudeSDKClientManager:
    """Claude SDK Client 管理器"""

    def __init__(self,
                 main_options: ClaudeAgentOptions,
                 subagent_options: ClaudeAgentOptions,
                 env_manager: 'EnvManager'):
        """初始化客户端管理器

        Args:
            main_options: 主Agent的options
            subagent_options: SubAgent的options
            env_manager: 环境变量管理器
        """
        self.main_options = main_options
        self.subagent_options = subagent_options
        self.env_manager = env_manager

    def create_main_client(self):
        """创建主Agent的ClaudeSDKClient"""
        return ClaudeSDKClient(self.main_options)

    def create_subagent_client(self):
        """创建SubAgent的ClaudeSDKClient（自动注入环境变量）"""
        return ClaudeSDKClient(self.env_manager.inject_env(self.subagent_options))
