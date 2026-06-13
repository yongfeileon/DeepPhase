"""Phase Runner 主控制器"""

import asyncio
from pathlib import Path
import time
from typing import Optional

from claude_agent_sdk import AssistantMessage, ResultMessage

from .config import Config
from .prompt_builder import PromptBuilder
from .progress_tracker import ProgressTracker
from .client_manager import ClaudeSDKClientManager


class PhaseRunner:
    """Phase Runner 主控制器"""

    def __init__(self, progress_path: str, design_doc_path: str, config: Config, task_type: str, client_mgr: ClaudeSDKClientManager, channel_mgr=None):
        self.progress_path = Path(progress_path)
        self.design_doc_path = Path(design_doc_path)
        self.config = config
        self.task_type = task_type
        self.builder = PromptBuilder(config, task_type)
        self.tracker = ProgressTracker(str(self.progress_path))
        self.user_input_queue = asyncio.Queue()
        self.channel_mgr = channel_mgr
        self.client_mgr = client_mgr
        self.execution_history = []
        print("\n" + "="*60)
        print("[主Agent] 创建 PhaseRunner")
        print(f"  任务类型: {task_type}")
        print(f"  进度文档: {self.progress_path}")
        print(f"  设计文档: {self.design_doc_path}")
        print("="*60 + "\n")

    def _create_client(self):
        """创建 ClaudeSDKClient"""
        return self.client_mgr.create_subagent_client()

    async def run_next_phase(self) -> str | None:
        """执行下一轮任务，返回SubAgent的输出；返回None表示已完成"""
        print("\n[主Agent] 启动新一轮 SubAgent 执行")

        # 1. 执行前状态检查
        check_result = await self._pre_execution_check()
        if check_result.startswith("stop"):
            print(f"\n[主Agent] 🛑 {check_result}")
            return None
        elif check_result.startswith("adjust"):
            print(f"\n[主Agent] ⚠️ {check_result}")

        # 2. 运行 subagent
        subagent_output = await self._run_subagent()

        # 3. 记录执行历史
        self._record_execution(subagent_output)

        # 4. 判断是否完成
        is_completed = await self._check_if_completed(subagent_output)

        if is_completed:
            print("\n[主Agent] 所有任务已完成，项目结束")
            return None

        return subagent_output

    async def _run_subagent(self) -> str:
        """运行 subagent 执行任务，返回最后的输出文本"""
        print(f"\n[SubAgent] 开始执行任务")
        print(f"  技术文档: {self.design_doc_path}")
        print(f"  进度文档: {self.progress_path}")

        # 保存进度文档快照
        self.tracker.save_snapshot()

        # 使用 PromptBuilder 构建 prompt
        prompt = self.builder.get_subagent_prompt(
            tech_doc_path=self.design_doc_path,
            progress_doc_path=self.progress_path
        )

        async with self._create_client() as client:
            print("\n[SubAgent] 完整任务提示词（执行前）")
            print("-" * 60)
            print(prompt)
            print("-" * 60)

            try:
                await client.query(prompt)
            except Exception as e:
                error_msg = f"API 错误: {str(e)}"
                print(f"\n[SubAgent] {error_msg}")
                if self.channel_mgr:
                    from .channels import Message, MessageType
                    await self.channel_mgr.broadcast(Message(
                        MessageType.ERROR,
                        error_msg
                    ))
                raise

            last_text = ""
            execution_time = 0.0
            last_token_time = time.time()
            token_timeout = self.config.get_runner_config()['token_timeout']

            async for message in client.receive_messages():
                current_time = time.time()

                # 检查token间隔超时
                if current_time - last_token_time > token_timeout:
                    print(f"\n[SubAgent] 超时：{token_timeout}秒内未收到新token")
                    raise TimeoutError(f"LLM响应超时：{token_timeout}秒内未收到新token")

                # 收到任何消息都更新时间戳，防止工具执行期间超时
                last_token_time = current_time

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, 'thinking'):
                            thinking_text = block.thinking
                            print(f"[SubAgent 思考] {thinking_text}")
                            if self.channel_mgr:
                                from .channels import Message, MessageType
                                await self.channel_mgr.broadcast(Message(
                                    MessageType.OUTPUT,
                                    f"[思考] {thinking_text}"
                                ))
                        elif hasattr(block, 'text'):
                            last_text = block.text
                            print(f"[SubAgent] {last_text[:200]}...")
                            if self.channel_mgr:
                                from .channels import Message, MessageType
                                await self.channel_mgr.broadcast(Message(
                                    MessageType.OUTPUT,
                                    last_text
                                ))

                    # 检查用户输入（在处理完消息后）
                    while not self.user_input_queue.empty():
                        user_input = await self.user_input_queue.get()
                        print(f"\n[用户输入] {user_input}")
                        # 注入到对话
                        await client.query(user_input)

                elif isinstance(message, ResultMessage):
                    execution_time = message.duration_ms / 1000
                    break

            print(f"\n[SubAgent] 执行完成，用时: {execution_time:.2f}秒")

            # 检测进度文档变化
            diff = self.tracker.get_diff()
            if diff:
                print(f"\n[进度追踪] 进度文档已更新:")
                print(diff)
            else:
                print(f"\n[进度追踪] 进度文档无变化")

            return last_text

    async def _pre_execution_check(self) -> str:
        """执行前状态检查，返回 continue/adjust:reason/stop:reason"""
        progress_content = self.progress_path.read_text(encoding='utf-8')
        recent_history = self._format_recent_history()

        prompt = self.builder.get_pre_execution_check_prompt(
            progress_content=progress_content,
            recent_history=recent_history
        )

        async with self._create_client() as client:
            await client.query(prompt)
            result = ""
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            result = block.text.strip()
                            break
                elif isinstance(message, ResultMessage):
                    break

            first_line = result.split('\n')[0]
            print(f"[主Agent] 状态检查: {first_line}")
            return first_line

    def _record_execution(self, output: str):
        """记录执行历史"""
        progress_content = self.progress_path.read_text(encoding='utf-8')
        self.execution_history.append({
            'progress': progress_content,
            'output': output[:500]
        })
        if len(self.execution_history) > 5:
            self.execution_history.pop(0)

    def _format_recent_history(self) -> str:
        """格式化最近3轮执行历史"""
        if not self.execution_history:
            return "无历史记录（首次执行）"

        lines = []
        for i, rec in enumerate(self.execution_history[-3:], 1):
            lines.append(f"### 第 {i} 轮\n输出: {rec['output']}\n进度:\n{rec['progress'][:300]}...\n")
        return "\n".join(lines)

    async def _check_if_completed(self, subagent_output: str) -> bool:
        """判断整个目标是否已完成"""
        progress_content = self.progress_path.read_text(encoding='utf-8')

        prompt = self.builder.get_completion_check_prompt(
            subagent_output=subagent_output,
            progress_content=progress_content
        )

        async with self._create_client() as client:
            await client.query(prompt)
            result = ""
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            result = block.text.strip().lower()
                            break
                elif isinstance(message, ResultMessage):
                    break

            is_completed = 'completed' in result and 'not_completed' not in result
            print(f"[主Agent] 判断结果: {'已完成' if is_completed else '未完成，需要继续'}")
            return is_completed

