"""DeepGoal Phase Runner 主程序

从 goal 文件自动分析需求，生成技术文档和进度追踪文档，然后执行 phase。
"""

import sys
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_agent_sdk import HookMatcher
from deep_phase import PhaseRunner
from deep_phase.hooks import create_pre_tool_use_hook
from deep_phase.config import Config
from deep_phase.tool_loader import load_tools_from_config
from deep_phase.analyzer import analyze_goal_and_generate_docs
from deep_phase.channels import ChannelManager, CLIChannel, Message, MessageType
from deep_phase.options_manager import AgentOptionsManager

import shutil


async def main():
    """主函数"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='DeepGoal Phase Runner')
    parser.add_argument('goal_file', help='goal.md 文件路径')
    parser.add_argument('target_dir', nargs='?', help='目标代码目录（可选，默认为 goal 文件所在目录）')
    parser.add_argument('--deny-git', action='store_true', help='禁止 git 操作')
    args = parser.parse_args()

    goal_path = Path(args.goal_file).resolve()

    # 如果传入的是目录，自动查找 goal.md
    if goal_path.is_dir():
        workspace_path = goal_path
        # 查找 goal 文件
        goal_file = None
        for name in ["goal.md", "goal.txt"]:
            candidate = workspace_path / name
            if candidate.exists():
                goal_file = candidate
                break
        if not goal_file:
            print(f"错误: 在目录 {workspace_path} 中未找到 goal.md 或 goal.txt")
            return
    else:
        # 传入的是文件
        goal_file = goal_path
        if not goal_file.exists():
            print(f"错误: goal 文件不存在: {goal_file}")
            return
        workspace_path = goal_file.parent

    # 确定 target_dir
    if args.target_dir:
        target_dir = Path(args.target_dir).resolve()
    else:
        target_dir = workspace_path

    # 创建 Channel Manager
    channel_mgr = ChannelManager()
    channel_mgr.register_channel(CLIChannel())

    # 控制状态
    paused = False
    stopped = False

    def pause_cmd():
        nonlocal paused
        paused = True

    def resume_cmd():
        nonlocal paused
        paused = False

    def stop_cmd():
        nonlocal stopped
        stopped = True

    channel_mgr.register_command("/pause", pause_cmd)
    channel_mgr.register_command("/resume", resume_cmd)
    channel_mgr.register_command("/stop", stop_cmd)

    # 自然语言处理器
    async def handle_natural_language(text: str):
        # 放入 runner 的输入队列
        await runner.user_input_queue.put(text)
        await channel_mgr.broadcast(Message(
            MessageType.STATUS,
            "已接收，将在下一条消息后注入"
        ))

    channel_mgr.set_natural_language_handler(handle_natural_language)

    await channel_mgr.start_listening()

    await channel_mgr.broadcast(Message(MessageType.STATUS, f"Goal 文件: {goal_file}"))
    await channel_mgr.broadcast(Message(MessageType.STATUS, f"文档目录: {workspace_path}"))
    await channel_mgr.broadcast(Message(MessageType.STATUS, f"代码目录: {target_dir}"))
    if args.deny_git:
        await channel_mgr.broadcast(Message(MessageType.STATUS, "Git 操作已禁用"))

    # 检查是否需要重新分析需求
    docs_dir = workspace_path / "_docs" / "design"
    # 使用 goal 文件的父目录名作为快照文件名，避免冲突
    goal_parent_name = goal_file.parent.name
    docs_goal_file = docs_dir / f"goal_{goal_parent_name}.md"
    progress_file = docs_dir / "progress.md"
    tech_file = docs_dir / "tech.md"

    need_analyze = True
    if docs_goal_file.exists():
        # 比对 goal 文件内容
        current_goal = goal_file.read_text(encoding='utf-8')
        saved_goal = docs_goal_file.read_text(encoding='utf-8')

        if current_goal == saved_goal:
            # Goal 文件未变化
            if progress_file.exists() and tech_file.exists():
                print(f"[初始化] Goal 文件未变化，继续执行现有项目")
                need_analyze = False
            else:
                print(f"[初始化] Goal 文件未变化，但缺少文档，重新分析")
        else:
            # Goal 文件已变化，清理 workspace
            print(f"[初始化] Goal 文件已变化，清理 workspace 并重新开始")
            import shutil
            for item in workspace_path.iterdir():
                if item.name not in [goal_file.name, ".git", ".gitignore"]:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            print(f"[初始化] 已清理 workspace（保留 {goal_file.name}）")

    # 项目根目录
    project_root = Path(__file__).parent

    # 加载配置文件
    config = Config(str(project_root / "config.yaml"))

    # 如果命令行指定了 --deny-git，覆盖配置
    if args.deny_git:
        config.set_deny_git(True)

    # 创建 AgentOptions 管理器
    tools_config = load_tools_from_config(config, workspace_path)
    pre_tool_hook = create_pre_tool_use_hook(config)

    options_mgr = AgentOptionsManager(tools_config, pre_tool_hook, workspace_path, target_dir)
    options_mgr.print_info()

    client_mgr = options_mgr.get_client_manager()

    # 根据需要执行需求分析或使用现有文档
    if need_analyze:
        # 分析需求并生成文档（使用主Agent）
        tech_path, progress_path, task_type = await analyze_goal_and_generate_docs(
            goal_file, workspace_path, client_mgr, config
        )

        # 保存 goal 文件副本到 _docs 目录
        docs_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(goal_file, docs_goal_file)
        print(f"[初始化] 已保存 goal 文件副本到 _docs 目录\n")
    else:
        # 使用现有文档
        tech_path = str(tech_file)
        progress_path = str(progress_file)
        # 从文件读取任务类型
        task_type_file = docs_dir / ".task_type"
        if task_type_file.exists():
            task_type = task_type_file.read_text(encoding='utf-8').strip()
        else:
            # 如果文件不存在，默认为 coding
            task_type = 'coding'
        print(f"[初始化] 任务类型: {task_type}")
        print(f"[初始化] 使用现有文档继续执行\n")

    # 创建 PhaseRunner
    print("="*60)
    print("[主Agent] 创建 PhaseRunner")
    print(f"  进度文档: {progress_path}")
    print(f"  设计文档: {tech_path}")
    print("="*60 + "\n")

    runner = PhaseRunner(
        progress_path=progress_path,
        design_doc_path=tech_path,
        config=config,
        task_type=task_type,
        client_mgr=client_mgr,
        channel_mgr=channel_mgr
    )

    # 执行所有 phase（最多10个，避免无限循环）
    max_phases = 10
    for i in range(max_phases):
        # 检查停止
        if stopped:
            await channel_mgr.broadcast(Message(MessageType.STATUS, "已停止"))
            break

        # 检查暂停
        while paused and not stopped:
            await asyncio.sleep(0.5)

        await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"\n{'='*60}"))
        await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"开始执行第 {i+1} 轮"))
        await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"{'='*60}"))

        runner_config = config.get_runner_config()
        max_retries = runner_config['max_retries']
        retry_delay = runner_config['retry_delay']

        for retry in range(max_retries):
            try:
                result = await runner.run_next_phase()

                if result is None:
                    # 任务已完成
                    await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"\n{'='*60}"))
                    await channel_mgr.broadcast(Message(MessageType.STATUS, "✓ 所有任务已完成"))
                    await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"{'='*60}"))
                    break

                await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"\n✓ 本轮完成"))
                break  # 成功则跳出重试循环

            except TimeoutError as e:
                if retry < max_retries - 1:
                    await channel_mgr.broadcast(Message(MessageType.OUTPUT, f"\n⚠ 超时，重试 {retry + 1}/{max_retries - 1}..."))
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    await channel_mgr.broadcast(Message(MessageType.ERROR, f"执行失败（已重试{max_retries}次）: {e}"))
                    import traceback
                    traceback.print_exc()
                    break

            except Exception as e:
                await channel_mgr.broadcast(Message(MessageType.ERROR, f"执行失败: {e}"))
                import traceback
                traceback.print_exc()
                break

        else:
            # for-else: 如果重试循环正常结束（没有break），说明所有重试都失败
            continue


if __name__ == "__main__":
    asyncio.run(main())
