"""Phase Runner 主控制器"""

from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ResultMessage

from .config import Config
from .prompt_builder import PromptBuilder


class PhaseRunner:
    """Phase Runner 主控制器"""

    def __init__(self, options: ClaudeAgentOptions, progress_path: str, design_doc_path: str, config: Config, task_type: str):
        self.options = options
        self.progress_path = Path(progress_path)
        self.design_doc_path = Path(design_doc_path)
        self.config = config
        self.task_type = task_type
        self.builder = PromptBuilder(config, task_type)
        print("\n" + "="*60)
        print("[主Agent] 创建 PhaseRunner")
        print(f"  任务类型: {task_type}")
        print(f"  进度文档: {self.progress_path}")
        print(f"  设计文档: {self.design_doc_path}")
        print("="*60 + "\n")

    async def run_next_phase(self) -> str | None:
        """执行下一轮任务，返回SubAgent的输出；返回None表示已完成"""
        print("\n[主Agent] 启动新一轮 SubAgent 执行")

        # 1. 运行 subagent
        subagent_output = await self._run_subagent()

        # 2. 判断是否完成
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

        # 使用 PromptBuilder 构建 prompt
        prompt = self.builder.get_subagent_prompt(
            tech_doc_path=self.design_doc_path,
            progress_doc_path=self.progress_path
        )

        async with ClaudeSDKClient(self.options) as client:
            print("\n[SubAgent] 完整任务提示词（执行前）")
            print("-" * 60)
            print(prompt)
            print("-" * 60)

            await client.query(prompt)

            last_text = ""
            execution_time = 0.0

            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, 'thinking'):
                            print(f"[SubAgent 思考] {block.thinking}")
                        elif hasattr(block, 'text'):
                            last_text = block.text
                            print(f"[SubAgent] {last_text[:200]}...")
                elif isinstance(message, ResultMessage):
                    execution_time = message.duration_ms / 1000
                    break

            print(f"\n[SubAgent] 执行完成，用时: {execution_time:.2f}秒")
            return last_text

    async def _check_if_completed(self, subagent_output: str) -> bool:
        """判断整个目标是否已完成"""
        print("\n[主Agent] 判断任务是否完成...")

        # 读取最新的进度文档
        progress_content = self.progress_path.read_text(encoding='utf-8')

        async with ClaudeSDKClient(self.options) as client:
            prompt = f"""
请分析以下信息，判断整个项目目标是否已经全部完成。

SubAgent 最后输出：
{subagent_output}

当前进度文档：
{progress_content}

请直接回答：completed 或 not_completed
"""
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

