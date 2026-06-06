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

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
from deep_phase import PhaseRunner
from deep_phase.hooks import create_pre_tool_use_hook
from deep_phase.config import Config
from deep_phase.tool_loader import load_tools_from_config
from deep_phase.analyzer import analyze_goal_and_generate_docs

import shutil


async def main():
    """主函数"""
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='DeepGoal Phase Runner')
    parser.add_argument('workspace_path', help='Workspace 路径')
    parser.add_argument('--deny-git', action='store_true', help='禁止 git 操作')
    args = parser.parse_args()

    workspace_path = Path(args.workspace_path)
    if not workspace_path.exists():
        print(f"错误: workspace 路径不存在: {workspace_path}")
        return

    print(f"\n[初始化] 使用 workspace: {workspace_path}")
    if args.deny_git:
        print(f"[初始化] Git 操作已禁用 (--deny-git)")

    # 查找 goal 文件
    goal_file = None
    for name in ["goal.md", "goal.txt"]:
        candidate = workspace_path / name
        if candidate.exists():
            goal_file = candidate
            break

    if not goal_file:
        print("错误: 未找到 goal.md 或 goal.txt 文件")
        return

    print(f"[初始化] 找到需求文件: {goal_file.name}")

    # 检查是否需要重新分析需求
    docs_dir = workspace_path / "_docs" / "design"
    docs_goal_file = docs_dir / goal_file.name
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

    # 从环境变量读取模型名称
    model = os.getenv("ANTHROPIC_MODEL", "glm-5")
    print(f"使用模型: {model}")

    # 从配置文件加载工具
    tools_config = load_tools_from_config(config, workspace_path)

    # 创建带有 config 的 hook
    pre_tool_hook = create_pre_tool_use_hook(config)

    # 配置选项
    options = ClaudeAgentOptions(
        model=model,
        permission_mode="bypassPermissions",
        cwd=str(workspace_path),
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="*", hooks=[pre_tool_hook], timeout=30.0)
            ]
        },
        **tools_config.to_agent_options()
    )

    # 根据需要执行需求分析或使用现有文档
    if need_analyze:
        # 分析需求并生成文档
        tech_path, progress_path, task_type = await analyze_goal_and_generate_docs(
            goal_file, workspace_path, options, config
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
        options=options,
        progress_path=progress_path,
        design_doc_path=tech_path,
        config=config,
        task_type=task_type
    )

    # 执行所有 phase（最多10个，避免无限循环）
    max_phases = 10
    for i in range(max_phases):
        print(f"\n{'='*60}")
        print(f"开始执行第 {i+1} 轮")
        print(f"{'='*60}")

        try:
            result = await runner.run_next_phase()

            if result is None:
                # 任务已完成
                print(f"\n{'='*60}")
                print("✓ 所有任务已完成")
                print(f"{'='*60}")
                break

            print(f"\n✓ 本轮完成")

        except Exception as e:
            print(f"\n✗ 执行失败: {e}")
            import traceback
            traceback.print_exc()
            break


if __name__ == "__main__":
    asyncio.run(main())
