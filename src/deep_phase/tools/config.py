"""工具配置管理器"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from claude_agent_sdk.types import McpStdioServerConfig


class ToolsConfig:
    """工具配置管理器"""

    def __init__(self):
        self.mcp_servers: Dict[str, Any] = {}
        self.disabled_tools: List[str] = []

    def add_stdio_server(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """添加 stdio MCP server 配置

        Args:
            name: 服务名称
            command: 启动命令
            args: 命令参数
            env: 环境变量
        """
        config: McpStdioServerConfig = {"command": command}
        if args:
            config["args"] = args
        if env:
            config["env"] = env
        self.mcp_servers[name] = config

    def add_sdk_server(
        self,
        name: str,
        server_config: Any,
    ) -> None:
        """添加 SDK MCP server 配置

        Args:
            name: 服务名称
            server_config: SDK MCP server 配置对象
        """
        self.mcp_servers[name] = server_config

    def disable_tool(self, tool_name: str) -> None:
        """禁用指定工具

        Args:
            tool_name: 工具名称（如 "WebSearch", "WebFetch"）
        """
        if tool_name not in self.disabled_tools:
            self.disabled_tools.append(tool_name)

    def to_agent_options(self) -> Dict[str, Any]:
        """转换为 ClaudeAgentOptions 的参数

        Returns:
            包含 mcp_servers 和 disallowed_tools 的字典
        """
        result: Dict[str, Any] = {}
        if self.mcp_servers:
            result["mcp_servers"] = self.mcp_servers
        if self.disabled_tools:
            result["disallowed_tools"] = self.disabled_tools
        return result
