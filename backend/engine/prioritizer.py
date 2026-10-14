"""
Attention prioritizer, task aging, and crash bypass engine for WardPulse.

Implements the K-budget nurse attention allocation, priority aging over time,
escalation of unattended cards, and crash bypass to emergency banners.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from shared.schemas import (
    EngineConfig,
    Mode,
    Task,
    TasksResponse,
    TaskStatus,
    TaskType,
)


def prioritize_tasks(
    candidate_tasks: List[Task],
    previous_tasks: Optional[List[Task]],
    now: datetime,
    config: EngineConfig,
) -> TasksResponse:
    """Prioritize candidate tasks with aging, escalation, and K-budget allocation.
    
    Rules:
    - Task identity is (patient_id, type). Persistent tasks retain id and created_at.
    - Tasks whose condition cleared are dropped naturally.
    - Priority = base_urgency + (aging_per_hour x hours_waiting) + escalation_boost.
    - Crash tasks bypass the budget into `emergency`.
    - At most `k_budget` tasks receive `active` status; remainder are `queued`.
    """
    # Index active/queued tasks from previous evaluation to preserve identity and created_at
    prev_map: Dict[Tuple[int, TaskType], Task] = {}
    max_id = 0
    if previous_tasks:
        for t in previous_tasks:
            if t.id > max_id:
                max_id = t.id
            if t.status in (TaskStatus.ACTIVE, TaskStatus.QUEUED):
                prev_map[(t.patient_id, t.type)] = t

    processed_tasks: List[Task] = []

    for task in candidate_tasks:
        key = (task.patient_id, task.type)

        if key in prev_map:
            prev = prev_map[key]
            task_id = prev.id
            created_at = prev.created_at
        else:
            max_id += 1
            task_id = max_id
            created_at = now

        waiting_minutes = max(0.0, (now - created_at).total_seconds() / 60.0)
        waiting_hours = waiting_minutes / 60.0

        # Aging boost
        aging_boost = config.aging_per_hour * waiting_hours

        # Escalation boost past threshold
        is_escalated = waiting_minutes >= config.escalation_after_minutes
        escalation_boost = 1.0 if is_escalated else 0.0

        final_priority = round(task.priority + aging_boost + escalation_boost, 3)

        updated_task = Task(
            id=task_id,
            patient_id=task.patient_id,
            bed=task.bed,
            type=task.type,
            target_vital=task.target_vital,
            title=task.title,
            reason=task.reason,
            priority=final_priority,
            status=task.status,
            emergency=task.emergency,
            escalated=is_escalated,
            created_at=created_at,
            waiting_minutes=round(waiting_minutes, 1),
            resolved_at=None,
        )
        processed_tasks.append(updated_task)

    # Separate crash emergency cards from budget cards
    emergency_tasks: List[Task] = []
    normal_tasks: List[Task] = []

    for t in processed_tasks:
        if t.emergency:
            t.status = TaskStatus.ACTIVE
            emergency_tasks.append(t)
        else:
            normal_tasks.append(t)

    # Sort emergency cards by priority descending
    emergency_tasks.sort(key=lambda t: t.priority, reverse=True)

    # Sort normal cards by priority descending
    normal_tasks.sort(key=lambda t: t.priority, reverse=True)

    # Allocate K-budget slots
    k = config.k_budget
    active_tasks: List[Task] = []
    queued_tasks: List[Task] = []

    for idx, t in enumerate(normal_tasks):
        if idx < k:
            t.status = TaskStatus.ACTIVE
            active_tasks.append(t)
        else:
            t.status = TaskStatus.QUEUED
            queued_tasks.append(t)

    return TasksResponse(
        mode=Mode.WARDPULSE,
        now=now,
        budget_k=k,
        emergency=emergency_tasks,
        active=active_tasks,
        queue=queued_tasks,
    )
