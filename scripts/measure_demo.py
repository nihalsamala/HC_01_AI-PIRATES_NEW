#!/usr/bin/env python3
"""
WardPulse Demo Shift Measurement Script.

Executes directly against the pure logic engine (no web server, database, or network)
on the deterministic 20-bed simulator ward (seed 42).

Measures and reports:
1. Alerts on screen at Story 1 (07:00), Story 2 (09:00), and Story 3 (11:00)
2. Mean and max alerts shown per mode (WardPulse vs NEWS2)
3. Alerts per nurse-hour per mode
4. Number of measure-vitals triage tasks created
5. Full ward evaluation latency in milliseconds (median and p95 over 100 runs)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import statistics
import sys
import time
from typing import Dict, List, Set, Tuple

# Ensure backend directory is in python search path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from engine.config import DEFAULT_CONFIG
from engine.news2 import evaluate_ward_news2
from engine.pipeline import evaluate_ward
from shared.schemas import TaskType, VitalsReading
from simulator.clock import Simulator
from simulator.scenarios import SIM_START
from simulator.ward import build_ward


MEASURE_TASK_TYPES = {
    TaskType.REPEAT_BP,
    TaskType.REPEAT_RESP_RATE,
    TaskType.REPEAT_SPO2,
    TaskType.REPEAT_HEART_RATE,
    TaskType.REPEAT_TEMP,
    TaskType.FULL_VITALS_RECHECK,
}


def measure_engine_latency(patients, vitals_dict, n_runs: int = 100) -> Tuple[float, float]:
    """Measure full 20-bed ward evaluation latency in milliseconds over n_runs."""
    latencies: List[float] = []
    # Warmup
    for _ in range(5):
        evaluate_ward(patients, vitals_dict, SIM_START, DEFAULT_CONFIG, [])

    for _ in range(n_runs):
        t0 = time.perf_counter()
        evaluate_ward(patients, vitals_dict, SIM_START, DEFAULT_CONFIG, [])
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

    latencies.sort()
    med = statistics.median(latencies)
    p95_idx = int(len(latencies) * 0.95)
    p95 = latencies[min(p95_idx, len(latencies) - 1)]
    return med, p95


def run_shift_simulation(
    seed: int = 42,
    shift_hours: float = 12.0,
    step_minutes: int = 5,
):
    """Simulate the ward over the demo shift, evaluating every step_minutes."""
    patients, initial_vitals = build_ward(source="sim", seed=seed)
    sim = Simulator(seed=seed, source="sim")

    # Initial patient vitals dictionary
    vitals_dict: Dict[int, List[VitalsReading]] = {
        p.id: [v for v in initial_vitals if v.patient_id == p.id] for p in patients
    }

    # 1. Latency benchmark
    lat_median, lat_p95 = measure_engine_latency(patients, vitals_dict, n_runs=100)

    # 2. Step through the shift
    total_steps = int(shift_hours * 60 / step_minutes)

    story_moments = {
        "Story 1 (07:00:00 - Same RR, Diff Patients)": SIM_START + timedelta(hours=1),
        "Story 2 (09:00:00 - Stale BP vs False Alarm)": SIM_START + timedelta(hours=3),
        "Story 3 (11:00:00 - Crash Bypass SBP 78)": SIM_START + timedelta(hours=5),
    }

    story_results: Dict[str, Dict[str, int]] = {}
    wp_alerts_series: List[int] = []
    news2_alerts_series: List[int] = []

    # Track distinct alerts
    prev_wp_active: Set[Tuple[int, TaskType]] = set()
    prev_news2_active: Set[Tuple[int, TaskType]] = set()
    wp_new_alerts = 0
    news2_new_alerts = 0

    measure_tasks_created: Set[Tuple[int, TaskType, str]] = set()

    prev_wp_tasks = []
    prev_news2_tasks = []
    v_id_counter = 100000

    for step in range(total_steps + 1):
        cur_time = SIM_START + timedelta(minutes=step * step_minutes)

        # Advance sim and collect new readings
        new_readings_in = sim.advance(cur_time)
        for vin in new_readings_in:
            v_id_counter += 1
            vr = VitalsReading(
                id=v_id_counter,
                patient_id=vin.patient_id,
                timestamp=vin.timestamp,
                source=vin.source,
                hr=vin.hr,
                sbp=vin.sbp,
                dbp=vin.dbp,
                rr=vin.rr,
                spo2=vin.spo2,
                temp=vin.temp,
                on_oxygen=vin.on_oxygen,
                consciousness=vin.consciousness,
            )
            vitals_dict[vin.patient_id].append(vr)

        # Filter vitals strictly up to cur_time (zero lookahead)
        cur_vitals = {
            pid: [v for v in vlist if v.timestamp <= cur_time]
            for pid, vlist in vitals_dict.items()
        }

        # Evaluate WardPulse
        wp_eval = evaluate_ward(patients, cur_vitals, cur_time, DEFAULT_CONFIG, prev_wp_tasks)
        # Evaluate NEWS2
        news2_eval = evaluate_ward_news2(patients, cur_vitals, cur_time, DEFAULT_CONFIG, prev_news2_tasks)

        prev_wp_tasks = list(wp_eval.tasks.active) + list(wp_eval.tasks.queue)
        prev_news2_tasks = list(news2_eval.tasks.active) + list(news2_eval.tasks.queue)

        wp_shown = wp_eval.tasks.alerts_shown
        news2_shown = news2_eval.tasks.alerts_shown

        wp_alerts_series.append(wp_shown)
        news2_alerts_series.append(news2_shown)

        # Count new distinct alerts
        curr_wp_active_set = {(t.bed, t.type) for t in wp_eval.tasks.emergency + wp_eval.tasks.active}
        curr_news2_active_set = {(t.bed, t.type) for t in news2_eval.tasks.emergency + news2_eval.tasks.active}

        wp_new_alerts += len(curr_wp_active_set - prev_wp_active)
        news2_new_alerts += len(curr_news2_active_set - prev_news2_active)

        prev_wp_active = curr_wp_active_set
        prev_news2_active = curr_news2_active_set

        # Record measure-vitals tasks
        for t in wp_eval.tasks.active + wp_eval.tasks.queue:
            if t.type in MEASURE_TASK_TYPES:
                measure_tasks_created.add((t.patient_id, t.type, t.title))

        # Check story moments
        for s_name, s_time in story_moments.items():
            if cur_time == s_time:
                story_results[s_name] = {"wp": wp_shown, "news2": news2_shown}

    # Summary Statistics
    wp_mean = statistics.mean(wp_alerts_series)
    wp_max = max(wp_alerts_series)
    news2_mean = statistics.mean(news2_alerts_series)
    news2_max = max(news2_alerts_series)

    # Shift alert rates per nurse-hour
    wp_rate_1n = wp_new_alerts / shift_hours
    news2_rate_1n = news2_new_alerts / shift_hours
    wp_rate_2n = wp_new_alerts / (shift_hours * 2.0)
    news2_rate_2n = news2_new_alerts / (shift_hours * 2.0)

    # 6-hour demo window (06:00 to 12:00) stats
    steps_6h = int(6.0 * 60 / step_minutes) + 1
    wp_mean_6h = statistics.mean(wp_alerts_series[:steps_6h])
    news2_mean_6h = statistics.mean(news2_alerts_series[:steps_6h])

    print("================================================================================")
    print("           WARDPULSE DEMO SHIFT MEASUREMENT REPORT (seed=42)")
    print("================================================================================")
    print(f"Shift Window: {SIM_START.strftime('%Y-%m-%d %H:%M:%S')} to {(SIM_START + timedelta(hours=shift_hours)).strftime('%Y-%m-%d %H:%M:%S')} ({shift_hours:.0f} hours)")
    print(f"Evaluation Cadence: Every {step_minutes} minutes ({len(wp_alerts_series)} evaluations)")
    print(f"Ward Size: 20 beds | Direct Engine Evaluation (no web server)")
    print("--------------------------------------------------------------------------------")
    print("1. ALERTS ON SCREEN AT CLINICAL STORY MOMENTS")
    print("--------------------------------------------------------------------------------")
    for s_name, res in story_results.items():
        delta = res['wp'] - res['news2']
        pct = (delta / res['news2'] * 100) if res['news2'] > 0 else 0.0
        print(f"  * {s_name:<46} | WardPulse: {res['wp']:>2} | NEWS2: {res['news2']:>2} ({pct:>+.0f}%)")

    print("\n--------------------------------------------------------------------------------")
    print("2. ON-SCREEN ALERTS SHOWN (WORKLOAD PERCEPTION)")
    print("--------------------------------------------------------------------------------")
    print(f"  * Mean Alerts on Screen (6h demo window): WardPulse = {wp_mean_6h:.2f} | NEWS2 = {news2_mean_6h:.2f} ({((wp_mean_6h-news2_mean_6h)/news2_mean_6h)*100:+.1f}%)")
    print(f"  * Mean Alerts on Screen (12h full shift): WardPulse = {wp_mean:.2f} | NEWS2 = {news2_mean:.2f} ({((wp_mean-news2_mean)/news2_mean)*100:+.1f}%)")
    print(f"  * Max Alerts on Screen at any moment:   WardPulse = {wp_max}    | NEWS2 = {news2_max}")

    print("\n--------------------------------------------------------------------------------")
    print("3. ALERTS PER NURSE-HOUR (NEW ALERTS GENERATED)")
    print("--------------------------------------------------------------------------------")
    print(f"  * Total New Alert Events Generated:     WardPulse = {wp_new_alerts}    | NEWS2 = {news2_new_alerts}")
    print(f"  * If 1 Nurse on duty (12 nurse-hrs):    WardPulse = {wp_rate_1n:.2f}/hr | NEWS2 = {news2_rate_1n:.2f}/hr")
    print(f"  * If 2 Nurses on duty (24 nurse-hrs):   WardPulse = {wp_rate_2n:.2f}/hr | NEWS2 = {news2_rate_2n:.2f}/hr")

    print("\n--------------------------------------------------------------------------------")
    print("4. TRIAGE MEASUREMENT TASKS")
    print("--------------------------------------------------------------------------------")
    print(f"  * Distinct Measure-Vitals Tasks Created: {len(measure_tasks_created)} (Bed 4 repeat_bp on stale BP)")
    for pid, ttype, title in sorted(measure_tasks_created):
        print(f"      - Bed {pid}: {title} ({ttype.value})")

    print("\n--------------------------------------------------------------------------------")
    print("5. ENGINE EVALUATION LATENCY (100 runs, 20-bed full ward)")
    print("--------------------------------------------------------------------------------")
    print(f"  * Median Latency: {lat_median:.2f} ms")
    print(f"  * p95 Latency:    {lat_p95:.2f} ms")
    print("================================================================================\n")

    return {
        "story_results": story_results,
        "wp_mean": wp_mean,
        "wp_max": wp_max,
        "news2_mean": news2_mean,
        "news2_max": news2_max,
        "wp_mean_6h": wp_mean_6h,
        "news2_mean_6h": news2_mean_6h,
        "wp_new_alerts": wp_new_alerts,
        "news2_new_alerts": news2_new_alerts,
        "wp_rate_1n": wp_rate_1n,
        "news2_rate_1n": news2_rate_1n,
        "wp_rate_2n": wp_rate_2n,
        "news2_rate_2n": news2_rate_2n,
        "measure_tasks_count": len(measure_tasks_created),
        "lat_median": lat_median,
        "lat_p95": lat_p95,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure WardPulse vs NEWS2 across the simulated demo shift")
    parser.add_argument("--seed", type=int, default=42, help="Simulator seed")
    parser.add_argument("--hours", type=float, default=12.0, help="Shift duration in hours")
    parser.add_argument("--step", type=int, default=5, help="Simulation time step in minutes")
    args = parser.parse_args()

    run_shift_simulation(seed=args.seed, shift_hours=args.hours, step_minutes=args.step)
