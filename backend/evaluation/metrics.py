"""
WardPulse comparative evaluation metrics module (P7).

Calculates clinical early-warning performance metrics:
  - Sensitivity (Event detection rate)
  - Median Lead Time (hours before documented event)
  - Alerts per Nurse-Hour (workload on 20-bed ward)
  - Measurement Tasks per Nurse-Hour (recheck cards generated)
  - False Alert Ratio (unactionable alert proportion)
Strictly avoids look-ahead: engine only sees vitals up to current reading.
"""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import List, Optional

from engine.config import DEFAULT_CONFIG
from engine.news2 import evaluate_ward_news2
from engine.pipeline import evaluate_ward
from evaluation.replay import ReplayCase
from shared.schemas import EngineConfig, Mode, SystemMetrics, Task, TaskType


def compute_metrics(
    cases: List[ReplayCase],
    mode: Mode,
    config: Optional[EngineConfig] = None,
) -> SystemMetrics:
    """Walk cases chronologically, evaluate without lookahead, and compute SystemMetrics."""
    cfg = config or DEFAULT_CONFIG

    events_total = 0
    events_detected = 0
    lead_times: List[float] = []

    total_alerts = 0
    false_alerts = 0
    total_measure_tasks = 0
    total_observation_hours = 0.0

    for case in cases:
        if not case.readings:
            continue

        readings_sorted = sorted(case.readings, key=lambda r: r.timestamp)
        first_time = readings_sorted[0].timestamp
        last_time = readings_sorted[-1].timestamp
        obs_hours = max(1.0, (last_time - first_time).total_seconds() / 3600.0)
        total_observation_hours += obs_hours

        has_event = case.event_time is not None
        if has_event:
            events_total += 1

        detected_for_case = False
        first_detection_time: Optional[datetime] = None
        previous_tasks: List[Task] = []

        # Step through time reading by reading (no look-ahead)
        for idx in range(1, len(readings_sorted) + 1):
            vitals_so_far = readings_sorted[:idx]
            now = vitals_so_far[-1].timestamp

            if mode == Mode.WARDPULSE:
                res = evaluate_ward(
                    patients=[case.patient],
                    vitals={case.patient.id: vitals_so_far},
                    now=now,
                    config=cfg,
                    previous_tasks=previous_tasks,
                )
                # Keep active & queued tasks as previous_tasks for aging
                previous_tasks = list(res.tasks.active) + list(res.tasks.queue)

                # High-priority alerts: page_doctor or emergency crash bypass
                raised_alerts = [
                    t for t in res.tasks.emergency + res.tasks.active
                    if t.type == TaskType.PAGE_DOCTOR or t.emergency
                ]
                measure_tasks = [
                    t for t in res.tasks.active + res.tasks.queue
                    if t.type in (
                        TaskType.REPEAT_BP,
                        TaskType.REPEAT_RESP_RATE,
                        TaskType.REPEAT_SPO2,
                        TaskType.REPEAT_HEART_RATE,
                        TaskType.REPEAT_TEMP,
                        TaskType.FULL_VITALS_RECHECK,
                    )
                ]
                total_measure_tasks += len(measure_tasks)

            else:
                # Naive NEWS2 comparator
                res = evaluate_ward_news2(
                    patients=[case.patient],
                    vitals={case.patient.id: vitals_so_far},
                    now=now,
                    config=cfg,
                    previous_tasks=None,
                )
                raised_alerts = list(res.tasks.active) + list(res.tasks.emergency)

            if raised_alerts:
                total_alerts += len(raised_alerts)

                if has_event and case.event_time is not None:
                    # Check if detection occurred prior to or at the event
                    if now <= case.event_time:
                        if not detected_for_case:
                            detected_for_case = True
                            first_detection_time = now
                    else:
                        # Alert after event already occurred
                        false_alerts += len(raised_alerts)
                else:
                    # Alert on a stable case with no documented deterioration event
                    false_alerts += len(raised_alerts)

        # Calculate lead time for detected case
        if detected_for_case and first_detection_time and case.event_time:
            lead_h = (case.event_time - first_detection_time).total_seconds() / 3600.0
            if lead_h >= 0:
                events_detected += 1
                lead_times.append(lead_h)

    # Derived metrics
    sensitivity = (events_detected / events_total) if events_total > 0 else None
    median_lead_time = statistics.median(lead_times) if lead_times else None

    # Workload scaled to 20-bed hospital ward
    ward_factor = 20.0
    alerts_per_nurse_hour = (
        (total_alerts / total_observation_hours) * ward_factor
        if total_observation_hours > 0
        else None
    )
    measure_tasks_per_nurse_hour = (
        (total_measure_tasks / total_observation_hours) * ward_factor
        if mode == Mode.WARDPULSE and total_observation_hours > 0
        else None
    )
    false_alert_ratio = (
        (false_alerts / total_alerts) if total_alerts > 0 else 0.0
    )

    return SystemMetrics(
        system=mode,
        events_total=events_total,
        events_detected=events_detected,
        sensitivity=round(sensitivity, 3) if sensitivity is not None else None,
        median_lead_time_hours=round(median_lead_time, 2) if median_lead_time is not None else None,
        alerts_per_nurse_hour=round(alerts_per_nurse_hour, 2) if alerts_per_nurse_hour is not None else None,
        measure_tasks_per_nurse_hour=round(measure_tasks_per_nurse_hour, 2) if measure_tasks_per_nurse_hour is not None else None,
        false_alert_ratio=round(false_alert_ratio, 3) if false_alert_ratio is not None else None,
    )
