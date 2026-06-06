"""需求分析和文档生成模块"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ResultMessage

from .config import Config
from .prompt_builder import PromptBuilder


async def detect_task_type(goal_content: str, options: ClaudeAgentOptions, config: Config) -> str:
    """使用 LLM 识别任务类型

    Args:
        goal_content: 目标内容
        options: Claude Agent 配置选项
        config: 配置对象

    Returns:
        'coding' 或 'general'
    """
    builder = PromptBuilder(config, 'coding')  # task_type 暂时用任意值
    prompt = builder.get_intent_detector_prompt(goal_content)

    async with ClaudeSDKClient(options) as client:
        await client.query(prompt)

        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, 'text'):
                        result = block.text.strip().lower()
                        if 'coding' in result:
                            return 'coding'
                        elif 'general' in result:
                            return 'general'
            elif isinstance(message, ResultMessage):
                break

    # 默认返回 coding
    return 'coding'


async def analyze_goal_and_generate_docs(
    goal_file: Path,
    workspace_dir: Path,
    options: ClaudeAgentOptions,
    config: Config,
) -> Tuple[str, str, str]:
    """分析 goal 文件并生成技术文档和进度追踪文档

    Args:
        goal_file: goal 文件路径
        workspace_dir: workspace 目录路径
        options: Claude Agent 配置选项
        config: 配置对象

    Returns:
        (tech_path, progress_path, task_type): 生成的文档路径和任务类型
    """
    # 读取 goal 文件
    goal_content = goal_file.read_text(encoding='utf-8')

    print("\n[需求分析] 识别任务意图...")

    # 使用 LLM 判断任务类型
    task_type = await detect_task_type(goal_content, options, config)
    print(f"[需求分析] 任务类型: {task_type}")
    print(f"[需求分析] 开始分析需求...")

    # 创建 PromptBuilder
    builder = PromptBuilder(config, task_type)

    # 创建 _docs/design 目录
    docs_dir = workspace_dir / "_docs" / "design"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 使用主agent 分析需求并生成文档
    async with ClaudeSDKClient(options) as client:
        # 使用 PromptBuilder 构建 prompt
        prompt = builder.get_analyzer_prompt(
            goal_content=goal_content,
            docs_dir=docs_dir
        )

        await client.query(prompt)

        result_data = None
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, 'text') and '{' in block.text:
                        import json
                        try:
                            start = block.text.find('{')
                            end = block.text.rfind('}') + 1
                            json_str = block.text[start:end]
                            result_data = json.loads(json_str)
                            break
                        except json.JSONDecodeError:
                            continue
            elif isinstance(message, ResultMessage):
                break

    if not result_data:
        raise ValueError("需求分析失败：未能生成文档")

    progress_path = str(docs_dir / "progress.md")

    # 根据任务类型确定技术文档路径
    if task_type == 'coding':
        tech_path = str(docs_dir / "tech.md")
        print(f"[需求分析] 已生成技术实现文档: {Path(tech_path).name}")
        print(f"[需求分析] 已生成进度追踪文档: {Path(progress_path).name}")
        print(f"[需求分析] 共 {result_data.get('phase_count', '?')} 个阶段\n")
    else:
        # 通用任务只有进度文档
        tech_path = progress_path
        print(f"[需求分析] 已生成进度追踪文档: {Path(progress_path).name}\n")

    # 保存任务类型到文件
    task_type_file = docs_dir / ".task_type"
    task_type_file.write_text(task_type, encoding='utf-8')

    return tech_path, progress_path, task_type
