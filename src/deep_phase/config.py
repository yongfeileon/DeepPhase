"""配置文件加载模块"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


class Config:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置

        Args:
            config_path: 配置文件路径（可选，默认为当前目录的 config.yaml）
        """
        if config_path is None:
            config_path = "config.yaml"

        self.config_path = Path(config_path)
        self.data: Dict[str, Any] = {}

        if self.config_path.exists():
            self._load()

    def _load(self) -> None:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f) or {}

    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置

        Returns:
            工具配置字典
        """
        return self.data.get('tools', {})

    def is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否启用

        Args:
            tool_name: 工具名称

        Returns:
            是否启用
        """
        tools = self.get_tools_config()
        tool_config = tools.get(tool_name, {})
        return tool_config.get('enabled', False)

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """获取指定工具的配置

        Args:
            tool_name: 工具名称

        Returns:
            工具配置字典
        """
        tools = self.get_tools_config()
        return tools.get(tool_name, {})

    def get_prompts_config(self) -> Dict[str, Any]:
        """获取所有 prompts 配置

        Returns:
            prompts 配置字典
        """
        return self.data.get('prompts', {})

    def get_prompt(self, prompt_name: str) -> str:
        """获取指定的 prompt 模板

        Args:
            prompt_name: prompt 名称（如 'analyzer', 'subagent_system' 等）

        Returns:
            prompt 模板字符串
        """
        prompts = self.get_prompts_config()
        prompt_value = prompts.get(prompt_name, '')

        # 如果值看起来像文件路径，则读取文件内容
        if prompt_value and ('/' in prompt_value or '\\' in prompt_value):
            prompt_file = self.config_path.parent / prompt_value
            if prompt_file.exists():
                return prompt_file.read_text(encoding='utf-8')

        return prompt_value

    def is_git_denied(self) -> bool:
        """检查是否禁止 git 操作

        Returns:
            是否禁止 git 操作
        """
        security = self.data.get('security', {})
        return security.get('deny_git', False)

    def set_deny_git(self, value: bool) -> None:
        """设置是否禁止 git 操作

        Args:
            value: 是否禁止 git 操作
        """
        if 'security' not in self.data:
            self.data['security'] = {}
        self.data['security']['deny_git'] = value

    def detect_task_type(self, goal_content: str) -> str:
        """根据 goal 内容判断任务类型

        Args:
            goal_content: goal 文件内容

        Returns:
            'coding' 或 'general'
        """
        coding_keywords = [
            '代码', '开发', '实现', '编程', 'bug', '功能', 'API',
            '函数', '类', '模块', '接口', '测试', '调试', '重构',
            'code', 'develop', 'implement', 'function', 'class', 'test'
        ]
        content_lower = goal_content.lower()
        for keyword in coding_keywords:
            if keyword in content_lower:
                return 'coding'
        return 'general'

    def get_runner_config(self) -> Dict[str, Any]:
        """获取执行器配置

        Returns:
            执行器配置字典（包含默认值）
        """
        runner = self.data.get('runner', {})
        return {
            'max_retries': runner.get('max_retries', 3),
            'retry_delay': runner.get('retry_delay', 2),
            'token_timeout': runner.get('token_timeout', 120)
        }
