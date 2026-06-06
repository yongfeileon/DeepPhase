"""工具调用日志 Hook 函数"""

from pathlib import Path


def create_pre_tool_use_hook(config):
    """创建工具使用前的 hook，带有 config 闭包"""

    async def pre_tool_use_hook(input_data, tool_use_id, context):
        """工具使用前的 hook"""
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})

        # 检查 git 操作拦截
        if config and config.is_git_denied():
            if tool_name == "Bash" and "command" in tool_input:
                command = tool_input["command"].strip()
                # 检查是否是 git 命令
                if command.startswith("git ") or command.startswith("git\t"):
                    print(f"\n[HOOK] ✗ 拦截 git 操作: {command[:100]}")
                    return {
                        "continue_": False,
                        "error": "Git 操作已被禁止（security.deny_git=true）"
                    }

        # 提取文件名（如果是文件操作工具）
        file_info = ""
        if "file_path" in tool_input:
            file_info = f" → {Path(tool_input['file_path']).name}"
        elif "path" in tool_input and tool_input["path"]:
            file_info = f" → {Path(tool_input['path']).name}"

        print(f"\n[TOOL] {tool_name}{file_info}")

        # 显示 Bash 命令（前100个字符）
        if tool_name == "Bash" and "command" in tool_input:
            command = tool_input["command"]
            display_cmd = command[:100] + "..." if len(command) > 100 else command
            print(f"  命令: {display_cmd}")

        # 显示 TodoWrite 的任务清单
        if tool_name == "TodoWrite" and "todos" in tool_input:
            todos = tool_input["todos"]
            print(f"  任务清单 ({len(todos)} 项):")
            for i, todo in enumerate(todos, 1):
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(todo.get("status", "pending"), "❓")
                print(f"    {i}. {status_icon} {todo.get('content', 'N/A')}")

        return {"continue_": True}

    return pre_tool_use_hook


async def post_tool_use_hook(input_data, tool_use_id, context):
    """工具使用后的 hook"""
    tool_name = input_data.get("tool_name", "unknown")
    print(f"[TOOL] {tool_name} 完成")
    return {"continue_": True}
