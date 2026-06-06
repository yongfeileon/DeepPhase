"""数据类型定义"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PhaseReport:
    """Phase 执行汇报"""
    phase_name: str
    status: str  # "completed" | "failed" | "partial"
    completed_tasks: List[str]
    files_changed: List[str]
    tests_passed: bool
    next_phase_suggestion: Optional[str]
    handoff_notes: str
    execution_time_seconds: float
