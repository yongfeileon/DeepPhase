"""智谱 AI 网络搜索和网页阅读工具配置"""

from __future__ import annotations

from typing import Optional, Dict, Any

from .config import ToolsConfig


def add_zhipu_web_tools(
    config: ToolsConfig,
    mcp_server_config: Optional[Dict[str, Any]] = None,
    replace_builtin: bool = True,
) -> None:
    """添加智谱 AI 网络搜索和网页阅读工具

    Args:
        config: 工具配置对象
        mcp_server_config: SDK MCP server 配置（可选）
            如果提供，将添加到 mcp_servers 中
            如果不提供，假设已在环境中配置（如 .claude/settings.json）
        replace_builtin: 是否替代内置的 WebSearch/WebFetch（默认 True）

    Example:
        # 方式1：假设智谱工具已在环境中配置
        add_zhipu_web_tools(config, replace_builtin=True)

        # 方式2：提供 SDK MCP server 配置
        from claude_agent_sdk import create_sdk_mcp_server
        server = create_sdk_mcp_server(...)
        add_zhipu_web_tools(config, mcp_server_config=server, replace_builtin=True)
    """
    # 禁用内置工具
    if replace_builtin:
        config.disable_tool("WebSearch")
        config.disable_tool("WebFetch")

    # 如果提供了 MCP server 配置，添加到配置中
    if mcp_server_config:
        config.add_sdk_server('zhipu-web', mcp_server_config)

