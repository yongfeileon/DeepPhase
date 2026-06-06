"""Playwright 浏览器自动化工具配置

使用官方 @playwright/mcp 包提供浏览器自动化能力。
"""

from __future__ import annotations

from typing import Optional

from .config import ToolsConfig


def add_playwright_tool(
    config: ToolsConfig,
    output_dir: Optional[str] = None,
) -> None:
    """添加 Playwright 浏览器自动化工具

    Args:
        config: 工具配置对象
        output_dir: 截图等输出文件目录（可选）
    """
    args = ["-y", "@playwright/mcp@latest"]
    if output_dir:
        args.extend(["--output-dir", output_dir])
    config.add_stdio_server("playwright", "npx", args)
