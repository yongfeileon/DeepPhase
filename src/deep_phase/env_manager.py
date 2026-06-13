"""环境变量管理器 - 统一处理 SubAgent 环境变量注入"""

import os
import copy
from typing import Optional, Dict
from claude_agent_sdk import ClaudeAgentOptions


class EnvManager:
    """环境变量管理器"""

    def __init__(self):
        self._subagent_env: Optional[Dict[str, str]] = None

    def setup_subagent_env(self,
                          base_url: Optional[str] = None,
                          api_key: Optional[str] = None,
                          model: Optional[str] = None) -> None:
        """配置 SubAgent 环境变量

        Args:
            base_url: SubAgent API base URL
            api_key: SubAgent API key
            model: SubAgent model
        """
        if not any([base_url, api_key, model]):
            self._subagent_env = None
            return

        self._subagent_env = dict(os.environ)

        if base_url:
            self._subagent_env['ANTHROPIC_BASE_URL'] = base_url
        if api_key:
            self._subagent_env['ANTHROPIC_API_KEY'] = api_key
            self._subagent_env['ANTHROPIC_AUTH_TOKEN'] = api_key
        if model:
            self._subagent_env['ANTHROPIC_MODEL'] = model

    def inject_env(self, options: ClaudeAgentOptions) -> ClaudeAgentOptions:
        """注入环境变量到 options

        Args:
            options: 原始 ClaudeAgentOptions

        Returns:
            注入环境变量后的新 options
        """
        if not self._subagent_env:
            return options

        new_options = copy.copy(options)
        new_options.env = self._subagent_env
        return new_options
