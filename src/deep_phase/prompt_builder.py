"""Prompt 构建器模块"""

from __future__ import annotations
from typing import Literal
from .config import Config


TaskType = Literal['coding', 'general']


class PromptBuilder:
    """根据任务类型构建 prompt"""

    def __init__(self, config: Config, task_type: TaskType):
        self.config = config
        self.task_type = task_type

    def get_analyzer_prompt(self, **kwargs) -> str:
        """获取分析器 prompt"""
        prompts = self.config.data.get('prompts', {})
        task_prompts = prompts.get(self.task_type, {})
        template = self._load_prompt_file(task_prompts.get('analyzer', ''))
        prompt = template.format(**kwargs)
        return self._add_security_warnings(prompt)

    def get_subagent_prompt(self, **kwargs) -> str:
        """获取子agent prompt"""
        prompts = self.config.data.get('prompts', {})
        task_prompts = prompts.get(self.task_type, {})
        template = self._load_prompt_file(task_prompts.get('subagent_task', ''))
        prompt = template.format(**kwargs)
        return self._add_security_warnings(prompt)

    def get_intent_detector_prompt(self, goal_content: str) -> str:
        """获取意图识别 prompt"""
        prompts = self.config.data.get('prompts', {})
        template = self._load_prompt_file(prompts.get('intent_detector', ''))
        return template.format(goal_content=goal_content)

    def get_pre_execution_check_prompt(self, progress_content: str, recent_history: str) -> str:
        """获取执行前状态检查 prompt"""
        prompts = self.config.data.get('prompts', {})
        template = self._load_prompt_file(prompts.get('pre_execution_checker', ''))
        return template.format(progress_content=progress_content, recent_history=recent_history)

    def get_completion_check_prompt(self, subagent_output: str, progress_content: str) -> str:
        """获取完成判断 prompt"""
        prompts = self.config.data.get('prompts', {})
        template = self._load_prompt_file(prompts.get('completion_checker', ''))
        return template.format(subagent_output=subagent_output, progress_content=progress_content)

    def _load_prompt_file(self, prompt_value: str) -> str:
        """加载 prompt 文件内容"""
        if not prompt_value:
            return ''
        if '/' in prompt_value or '\\' in prompt_value:
            prompt_file = self.config.config_path.parent / prompt_value
            if prompt_file.exists():
                return prompt_file.read_text(encoding='utf-8')
        return prompt_value

    def _add_security_warnings(self, prompt: str) -> str:
        """添加安全警告"""
        if self.config.is_git_denied():
            prompt += "\n\n⚠️ **IMPORTANT SECURITY RESTRICTION**: Git operations are DISABLED (security.deny_git=true). Do NOT attempt to use git commands via Bash tool. Any git command will be blocked by the pre-tool hook."
        return prompt
