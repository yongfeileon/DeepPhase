"""进度追踪器 - 检测 progress.md 文件变化"""

import difflib
from pathlib import Path
from typing import Optional


class ProgressTracker:
    """进度追踪器 - 基于文件变化检测任务完成"""

    def __init__(self, progress_path: str):
        self.progress_path = Path(progress_path)
        self._snapshot: Optional[str] = None

    def save_snapshot(self):
        """保存当前进度文档快照"""
        if self.progress_path.exists():
            self._snapshot = self.progress_path.read_text(encoding='utf-8')
        else:
            self._snapshot = ""

    def get_diff(self) -> Optional[str]:
        """获取与快照的差异，返回 None 表示无变化"""
        if self._snapshot is None:
            return None

        current = self.progress_path.read_text(encoding='utf-8') if self.progress_path.exists() else ""

        if current == self._snapshot:
            return None

        # 生成统一格式的 diff
        diff = difflib.unified_diff(
            self._snapshot.splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile='before',
            tofile='after',
            lineterm=''
        )
        return ''.join(diff)
