#!/usr/bin/env python3
"""
WardPulse Integration Story Verification Script (P6).

Drives the running API via /sim/control and /tasks to verify the three demo stories:
  1. Story 1: Bed 3 (COPD) has no card; Bed 7 (post-op) has active card at 07:00:00.
  2. Story 2: Bed 4 has repeat_bp and NOT page_doctor at 09:00:00.
  3. Story 3: Bed 12 in emergency while active still holds 2 cards; naive mode has more alerts_shown.

Exit non-zero on failure.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from typing import Any, Dict

try:
    import httpx
except ImportError:
    import urllib.request
    import json

    class SimpleClient:
        def __init__(self, base_url: str):
            self.base_url = base_url.rstrip("/")

        def get(self, path: str):
            req = urllib.request.Request(f"{self.base_url}{path}")
            try:
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode())
                    return type("Resp", (), {"status_code": resp.status, "json": lambda: data})()
            except urllib.error.HTTPError as e:
                return type("Resp", (), {"status_code": e.code, "json": lambda: json.loads(e.read().decode())})()

        def post(self, path: str, json: dict = None, **kwargs):
            payload = json if json is not None else kwargs.get("json_data", {})
            req = urllib.request.Request(
                f"{self.base_url}{path}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode())
                    return type("Resp", (), {"status_code": resp.status, "json": lambda: data})()
            except urllib.error.HTTPError as e:
                return type("Resp", (), {"status_code": e.code, "json": lambda: json.loads(e.read().decode())})()

    httpx = None


def create_client(base_url: str):
    if httpx:
        return httpx.Client(base_url=base_url, timeout=10.0)
    return SimpleClient(base_url=base_url)


def run_checks(base_url: str) -> None:
    print(f"Connecting to WardPulse API at {base_url}...")
    client = create_client(base_url)

    # 1. Health check
    retries = 10
    healthy = False
    for i in range(retries):
        try:
            res = client.get("/health")
            if res.status_code == 200:
                healthy = True
                break
        except Exception:
            time.sleep(0.5)

    if not healthy:
        print("[FAIL] Could not connect to /health. Is the backend server running?")
        sys.exit(1)
    print("  [OK] Backend is healthy.")

    # 2. Reset simulation to SIM_START (06:00:00)
    print("  Resetting simulation clock to 06:00:00...")
    res = client.post("/sim/control", json={"action": "reset"})
    assert res.status_code == 200, f"Reset failed: {res.json()}"
    state = res.json()
    print(f"  Current sim_time: {state['sim_time']}")

    # Helper: advance simulation to target time
    def advance_to(target_iso: str, speed: float = 120.0):
        target_dt = datetime.fromisoformat(target_iso)
        # Set speed
        client.post("/sim/control", json={"action": "set_speed", "speed_minutes_per_second": speed})
        # Start running
        client.post("/sim/control", json={"action": "play"})

        start_wait = time.time()
        while time.time() - start_wait < 15.0:
            res = client.get("/sim/state")
            current_state = res.json()
            curr_dt = datetime.fromisoformat(current_state["sim_time"])
            if curr_dt >= target_dt:
                # Pause
                client.post("/sim/control", json={"action": "pause"})
                return current_state
            time.sleep(0.1)

        client.post("/sim/control", json={"action": "pause"})
        raise TimeoutError(f"Simulation did not reach {target_iso} within 15 seconds")

    # -------------------------------------------------------------------------
    # STORY 1: 07:00:00 (+1h)
    # -------------------------------------------------------------------------
    print("\n--- Verifying Story 1: Same number, different patients (07:00:00) ---")
    advance_to("2026-10-20T07:00:00", speed=120.0)

    res_tasks = client.get("/tasks?mode=wardpulse")
    assert res_tasks.status_code == 200, f"GET /tasks failed: {res_tasks.json()}"
    tasks_data = res_tasks.json()

    active_beds = [t["bed"] for t in tasks_data["active"]]
    emergency_beds = [t["bed"] for t in tasks_data["emergency"]]
    all_alert_beds = active_beds + emergency_beds

    print(f"  Active beds at 07:00:00: {active_beds}")
    print(f"  Emergency beds at 07:00:00: {emergency_beds}")

    # Bed 3 (COPD) must NOT have a card
    if 3 in all_alert_beds:
        print("[FAIL] Story 1: Bed 3 (COPD baseline RR 22) raised a card unexpectedly!")
        sys.exit(1)

    # Bed 7 (Post-op) MUST have an active card
    if 7 not in active_beds:
        print("[FAIL] Story 1: Bed 7 (Post-op acute RR 22) did not receive an active card!")
        sys.exit(1)

    print("  [PASS] Story 1 Verified: Bed 3 (COPD) is calm; Bed 7 (Post-op) has active card.")

    # -------------------------------------------------------------------------
    # STORY 2: 09:00:00 (+3h)
    # -------------------------------------------------------------------------
    print("\n--- Verifying Story 2: Stale BP vs False Alarm (09:00:00) ---")
    advance_to("2026-10-20T09:00:00", speed=120.0)

    res_tasks = client.get("/tasks?mode=wardpulse")
    assert res_tasks.status_code == 200
    tasks_data = res_tasks.json()

    all_tasks = tasks_data["emergency"] + tasks_data["active"] + tasks_data["queue"]
    bed4_tasks = [t for t in all_tasks if t["bed"] == 4]

    print(f"  Bed 4 tasks at 09:00:00: {[(t['type'], t['status']) for t in bed4_tasks]}")

    # Must get repeat_bp, and NOT page_doctor
    has_repeat_bp = any(t["type"] == "repeat_bp" for t in bed4_tasks)
    has_page_doctor = any(t["type"] == "page_doctor" for t in bed4_tasks)

    if not has_repeat_bp:
        print("[FAIL] Story 2: Bed 4 did not receive a 'repeat_bp' card for stale BP!")
        sys.exit(1)

    if has_page_doctor:
        print("[FAIL] Story 2: Bed 4 erroneously triggered 'page_doctor' on stale data alone!")
        sys.exit(1)

    print("  [PASS] Story 2 Verified: Bed 4 gets repeat_bp and NOT page_doctor.")

    # -------------------------------------------------------------------------
    # STORY 3: 11:00:00 (+5h)
    # -------------------------------------------------------------------------
    print("\n--- Verifying Story 3: Crash Bypass (11:00:00) ---")
    advance_to("2026-10-20T11:00:00", speed=120.0)

    res_wp = client.get("/tasks?mode=wardpulse")
    assert res_wp.status_code == 200
    wp_data = res_wp.json()

    emergency_beds = [t["bed"] for t in wp_data["emergency"]]
    active_beds = [t["bed"] for t in wp_data["active"]]
    wp_alerts = wp_data["alerts_shown"]

    print(f"  Emergency beds at 11:00:00: {emergency_beds}")
    print(f"  Active beds at 11:00:00 (budget={wp_data.get('budget_k')}): {active_beds}")
    print(f"  WardPulse alerts_shown: {wp_alerts}")

    # Bed 12 must appear in emergency
    if 12 not in emergency_beds:
        print("[FAIL] Story 3: Bed 12 (crash vitals) did not appear in emergency bypass!")
        sys.exit(1)

    # Active cards must still hold 2 (attention budget)
    if len(active_beds) != 2:
        print(f"[FAIL] Story 3: Expected active cards count == 2, got {len(active_beds)}")
        sys.exit(1)

    # Query Naive mode for comparison
    res_naive = client.get("/tasks?mode=news2")
    assert res_naive.status_code == 200
    naive_data = res_naive.json()
    naive_alerts = naive_data["alerts_shown"]

    print(f"  Naive NEWS2 alerts_shown: {naive_alerts}")

    if naive_alerts <= wp_alerts:
        print(f"[FAIL] Naive mode alerts ({naive_alerts}) should be significantly higher than WardPulse ({wp_alerts})!")
        sys.exit(1)

    print(f"  [PASS] Story 3 Verified: Bed 12 in emergency; active holds 2 cards; naive mode shows {naive_alerts} alerts vs WardPulse {wp_alerts}.")

    # -------------------------------------------------------------------------
    # STORY 4: Live Typed-In COPD Deterioration (Bed 5 vs Control Bed 6)
    # -------------------------------------------------------------------------
    print("\n--- Verifying Story 4: Live Typed-In COPD Deterioration (Bed 5 vs Bed 6) ---")
    # Reset simulation to clean baseline before Story 4
    res_reset = client.post("/sim/control", json={"action": "reset"})
    assert res_reset.status_code == 200

    # Retrieve patient IDs for Bed 5 (COPD) and Bed 6 (non-COPD control)
    res_ward = client.get("/ward")
    assert res_ward.status_code == 200
    ward_beds = res_ward.json()["beds"]
    bed5_patient_id = next(b["patient_id"] for b in ward_beds if b["bed"] == 5)
    bed6_patient_id = next(b["patient_id"] for b in ward_beds if b["bed"] == 6)

    # 1. POST vitals for Bed 5 (COPD): SpO2 falling to 88% while RR stays at normal 22
    vitals_bed5 = {
        "patient_id": bed5_patient_id,
        "hr": 80.0,
        "sbp": 124.0,
        "dbp": 78.0,
        "rr": 22.0,
        "spo2": 88.0,
        "on_oxygen": True,
        "source": "manual",
    }
    res_post_5 = client.post("/vitals", json=vitals_bed5)
    assert res_post_5.status_code == 200, f"Failed to post vitals for Bed 5: {res_post_5.json()}"

    res_tasks_5 = client.get("/tasks?mode=wardpulse")
    assert res_tasks_5.status_code == 200
    tasks_5 = res_tasks_5.json()
    b5_active = [t for t in tasks_5["active"] if t["bed"] == 5]
    print(f"  Bed 5 active cards: {[(t['type'], t['reason']) for t in b5_active]}")

    has_b5_copd_reason = any("Critical hypoxia for COPD" in t["reason"] or "COPD" in t["reason"] for t in b5_active)
    if not has_b5_copd_reason:
        print("[FAIL] Story 4: Bed 5 did not receive an active card with COPD focus reason!")
        sys.exit(1)

    # 2. Reset and POST the exact same vitals for Bed 6 (Control, non-COPD)
    res_reset = client.post("/sim/control", json={"action": "reset"})
    assert res_reset.status_code == 200

    vitals_bed6 = {
        "patient_id": bed6_patient_id,
        "hr": 80.0,
        "sbp": 124.0,
        "dbp": 78.0,
        "rr": 22.0,
        "spo2": 88.0,
        "on_oxygen": True,
        "source": "manual",
    }
    res_post_6 = client.post("/vitals", json=vitals_bed6)
    assert res_post_6.status_code == 200

    res_tasks_6 = client.get("/tasks?mode=wardpulse")
    assert res_tasks_6.status_code == 200
    tasks_6 = res_tasks_6.json()
    b6_active = [t for t in tasks_6["active"] if t["bed"] == 6]
    print(f"  Bed 6 active cards: {[(t['type'], t['reason']) for t in b6_active]}")

    has_b6_copd_reason = any("COPD" in t["reason"] for t in b6_active)
    if has_b6_copd_reason:
        print("[FAIL] Story 4: Bed 6 erroneously received a COPD-boosted reason!")
        sys.exit(1)

    print("  [PASS] Story 4 Verified: Bed 5 gets active card with COPD focus reason; non-COPD control Bed 6 does not.")

    # Reset simulation back to clean baseline so other test suites or runs are unaffected
    res_final_reset = client.post("/sim/control", json={"action": "reset"})
    assert res_final_reset.status_code == 200

    print("\n===================================================================")
    print("ALL 4 CLINICAL STORIES & TOGGLE REDUCTION VERIFIED OK!")
    print("===================================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check WardPulse demo stories against live API")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL")
    args = parser.parse_args()
    try:
        run_checks(args.base_url)
    except Exception as e:
        print(f"\n[ERROR] Integration check failed: {e}")
        sys.exit(1)
