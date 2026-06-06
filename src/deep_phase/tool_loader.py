"""从配置文件加载工具"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .tools import ToolsConfig, add_playwright_tool, add_zhipu_web_tools


def load_tools_from_config(config: Config, workspace_dir: Path) -> ToolsConfig:
    """从配置文件加载工具配置

    Args:
        config: 配置对象
        workspace_dir: 工作目录路径

    Returns:
        ToolsConfig 对象
    """
    tools_config = ToolsConfig()

    # 加载 Playwright 工具
    if config.is_tool_enabled('playwright'):
        playwright_cfg = config.get_tool_config('playwright')
        output_dir = playwright_cfg.get('output_dir')
        if output_dir:
            output_dir = str(workspace_dir / output_dir)
        add_playwright_tool(tools_config, output_dir=output_dir)
        print(f"[工具] 已启用 Playwright")

    # 加载智谱工具
    if config.is_tool_enabled('zhipu_web'):
        zhipu_cfg = config.get_tool_config('zhipu_web')
        replace_builtin = zhipu_cfg.get('replace_builtin', True)
        add_zhipu_web_tools(tools_config, replace_builtin=replace_builtin)
        print(f"[工具] 已启用智谱 Web 工具")

    return tools_config
