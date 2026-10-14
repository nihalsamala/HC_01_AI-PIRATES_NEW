"""
WardPulse attention allocation pipeline.
"""

from datetime import datetime
from typing import Dict, List, Optional

from shared.schemas import (
    EngineConfig,
    Mode,
    Patient,
    Task,
    TasksResponse,
    VitalsReading,
    WardEvaluation,
    WardOverview,
)


def evaluate_ward(
    patients: List[Patient],
    vitals: Dict[int, List[VitalsReading]],
    now: datetime,
    config: EngineConfig,
    previous_tasks: Optional[List[Task]] = None,
) -> WardEvaluation:
    """Evaluate ward patients and allocate nurse attention (WardPulse mode)."""
    return WardEvaluation(
        assessments=[],
        tasks=TasksResponse(
            mode=Mode.WARDPULSE,
            now=now,
            budget_k=config.k_budget,
            emergency=[],
            active=[],
            queue=[],
        ),
        ward=WardOverview(now=now, beds=[]),
    )
