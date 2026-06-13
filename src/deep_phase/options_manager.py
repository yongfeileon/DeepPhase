"""ClaudeAgentOptions 管理器 - 统一管理主Agent和SubAgent的配置"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

from .env_manager import EnvManager
from .client_manager import ClaudeSDKClientManager


class AgentOptionsManager:
    """Agent Options 管理器"""

    def __init__(self,
                 tools_config: Any,
                 pre_tool_hook: Any,
                 workspace_path: Path,
                 target_dir: Path):
        """初始化管理器

        Args:
            tools_config: 工具配置对象
            pre_tool_hook: PreToolUse hook
            workspace_path: 工作空间路径
            target_dir: 目标代码目录
        """
        self.tools_config = tools_config
        self.pre_tool_hook = pre_tool_hook
        self.workspace_path = workspace_path
        self.target_dir = target_dir

        # 读取主Agent配置
        self.main_base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.main_api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
        self.main_model = os.getenv("ANTHROPIC_MODEL", "glm-5")

        # 读取SubAgent配置
        subagent_base_url = os.getenv("SUBAGENT_BASE_URL")
        subagent_api_key = os.getenv("SUBAGENT_AUTH_TOKEN")
        subagent_model = os.getenv("SUBAGENT_MODEL")

        # 创建环境变量管理器
        self.env_manager = EnvManager()
        if subagent_base_url or subagent_api_key or subagent_model:
            self.env_manager.setup_subagent_env(
                subagent_base_url or self.main_base_url,
                subagent_api_key or self.main_api_key,
                subagent_model or self.main_model
            )
            self.subagent_model = subagent_model or self.main_model
        else:
            self.subagent_model = self.main_model

        # 创建客户端管理器
        self._client_manager = None

    def get_main_options(self) -> ClaudeAgentOptions:
        """获取主Agent的options"""
        return ClaudeAgentOptions(
            model=self.main_model,
            permission_mode="bypassPermissions",
            cwd=str(self.workspace_path),
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="*", hooks=[self.pre_tool_hook], timeout=30.0)
                ]
            },
            **self.tools_config.to_agent_options()
        )

    def get_subagent_options(self) -> ClaudeAgentOptions:
        """获取SubAgent的options"""
        return ClaudeAgentOptions(
            model=self.subagent_model,
            permission_mode="bypassPermissions",
            cwd=str(self.target_dir),
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="*", hooks=[self.pre_tool_hook], timeout=30.0)
                ]
            },
            **self.tools_config.to_agent_options()
        )

    def get_env_manager(self) -> EnvManager:
        """获取环境变量管理器"""
        return self.env_manager

    def get_client_manager(self) -> ClaudeSDKClientManager:
        """获取客户端管理器（单例）"""
        if self._client_manager is None:
            self._client_manager = ClaudeSDKClientManager(
                self.get_main_options(),
                self.get_subagent_options(),
                self.env_manager
            )
        return self._client_manager

    def print_info(self):
        """打印配置信息"""
        print(f"主Agent模型: {self.main_model}")
        if self.env_manager._subagent_env:
            print(f"SubAgent配置: {self.subagent_model} @ {os.getenv('SUBAGENT_BASE_URL', self.main_base_url)}")
