"""
NEWS2 evaluation pipeline (naive AI comparator).
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


def evaluate_ward_news2(
    patients: List[Patient],
    vitals: Dict[int, List[VitalsReading]],
    now: datetime,
    config: EngineConfig,
    previous_tasks: Optional[List[Task]] = None,
) -> WardEvaluation:
    """Evaluate ward patients using standard NEWS2 scoring (naive comparator)."""
    return WardEvaluation(
        assessments=[],
        tasks=TasksResponse(
            mode=Mode.NEWS2,
            now=now,
            budget_k=None,
            emergency=[],
            active=[],
            queue=[],
        ),
        ward=WardOverview(now=now, beds=[]),
    )
