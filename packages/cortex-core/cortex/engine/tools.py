"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Tool System                                ║
║  Extensible tool registry for AI capabilities               ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional, List

from cortex.exceptions import ToolNotFoundError, ToolExecutionError


@dataclass
class ToolInfo:
    """Metadata about a registered tool."""
    name: str
    description: str
    parameters: Dict[str, str]


@dataclass
class ToolResult:
    """Result from executing a tool."""
    success: bool
    output: Any
    error: str = ""
    duration_ms: float = 0.0


class ToolRegistry:
    """Extensible tool registry.

    Register any Python function as a tool the AI can use.
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._info: Dict[str, ToolInfo] = {}

    def register(
        self,
        name: str,
        fn: Callable,
        description: str = "",
        parameters: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a tool."""
        self._tools[name] = fn
        self._info[name] = ToolInfo(
            name=name,
            description=description or fn.__doc__ or "",
            parameters=parameters or {},
        )

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a registered tool."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")

        import time
        start = time.time()
        try:
            output = self._tools[name](**kwargs)
            return ToolResult(
                success=True,
                output=output,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def list_tools(self) -> List[ToolInfo]:
        """List all registered tools."""
        return list(self._info.values())

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    @property
    def tool_count(self) -> int:
        return len(self._tools)
