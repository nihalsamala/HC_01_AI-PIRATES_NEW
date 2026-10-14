# WardPulse Live Demonstration Script

This script is the definitive, click-by-click presentation guide for demonstrating WardPulse to hackathon judges, clinical evaluators, and hospital administrators.

---

## 1. Setup & Pre-Flight Checklist

Before taking the stage:
1. **Launch the Stack:**
   ```powershell
   # Start backend and frontend together:
   .\scripts\run_all.ps1
   ```
2. **Open the Console:** Navigate to [http://localhost:5173](http://localhost:5173) in your browser.
3. **Verify Health:** Look at the top header:
   - Green badge indicates `LIVE API` connected (or `MOCK DATA` if running standalone).
   - Sim clock displays `2026-10-20 06:00:00` (or running forward).
4. **Projector Ready:** If presenting on a large screen or projector, click **"Projector Text"** in the top header to enlarge fonts, card titles, and counter badges.

---

## 2. Quick 60-Second Elevator Pitch (What to Say)

> *"In an understaffed 20-bed hospital ward, two nurses are responsible for monitoring twenty acutely ill patients. Today's early warning systems, like NEWS2, use rigid population thresholds. If a COPD patient normally breathes at 22 breaths per minute, the alarm rings every single hour. When ten alarms go off at once, nurses experience severe alarm fatigue—and real deterioration gets lost in the noise.*
>
> *WardPulse transforms early warning from an alarm flood into an **AI Attention Allocator**. It evaluates each patient against their **personal baseline**, separates **clinical risk** from **data freshness**, and limits the screen to the **top 2 immediate actions** for the next 15 minutes. And if an unequivocal crash occurs, it **bypasses the queue** straight to an emergency banner. Let me show you how it works."*

---

## 3. The 3 Scripted Clinical Scenarios (Step-by-Step)

You can run this manually using the clock controls, or click the **"Guided Demo"** button in the header.

---

### Step 1: Launch Guided Demo Mode
- **Action:** Click the **"Guided Demo"** button (top right header).
- **What happens on screen:**
  - A dark teal story caption banner appears: **"Story 1: Personal Baselines (1/3)"**.
  - Simulation time jumps to `07:00:00`.
  - Bed 7 is automatically selected, opening her vital trend sparklines in the side panel.

---

### Step 2: Story 1 — Same Breathing Rate, Different Patients
- **Simulation Time:** `2026-10-20 07:00:00` (+1 hour into shift).
- **What to say:**
  > *"Look at Bed 3 and Bed 7. Both patients currently have the exact same respiratory rate: 22 breaths per minute. Under standard NEWS2, both trigger alerts.
  > But look at who they are: Bed 3 is a chronic COPD patient whose baseline respiratory rate has been 21 to 23 for days. WardPulse recognizes this is his personal normal and keeps the ward quiet.
  > Meanwhile, Bed 7 is a post-operative patient whose baseline breathing rate was 14. Climbing to 22 is an acute 57% baseline breach. WardPulse puts an active card on screen: 'Page on-duty doctor for Bed 7'."*
- **Click:** Click **"Naive AI (Standard NEWS2)"** on the mode toggle.
  - **What the audience sees:** The counter jumps from **1** to **6+ alerts**. Bed 3, Bed 5, Bed 9 all turn red.
- **Click:** Toggle back to **"WardPulse"**.
  - **What the audience sees:** The counter drops back to **1 actionable card**. The noise vanishes.

---

### Step 3: Story 2 — Stale Data is a Task, Not Panic
- **Action:** Click **"Next Story"** on the demo banner (or step to Story 2).
- **Simulation Time:** `2026-10-20 09:00:00` (+3 hours into shift).
- **What to say:**
  > *"At 09:00, Bed 4 had a low blood pressure earlier (112 mmHg), but the blood pressure cuff was skipped during the last round. Her BP reading is now over 7 hours old.
  > A naive ML model would predict high shock risk based on outdated numbers, panicking the team.
  > WardPulse disentangles risk from freshness. It does not page a doctor on stale numbers. Instead, it generates a focused triage task: 'Repeat manual BP on Bed 4'. It tells the nurse to verify reality before escalating."*
- **What the audience sees:**
  - Bed 4 tile on the ward strip shows a yellow "WATCH" status with a dotted stale-vitals indicator.
  - Active card 2 appears: **"Repeat manual BP: Bed 4"** with reason *"BP not taken for 7h; prior SBP 112"*.
  - Total active demands = **2**. Notice that the $K=2$ attention budget is perfectly filled.

---

### Step 4: Story 3 — Unequivocal Crash Bypasses the Budget
- **Action:** Click **"Next Story"** on the demo banner (or step to Story 3).
- **Simulation Time:** `2026-10-20 11:00:00` (+5 hours into shift).
- **What to say:**
  > *"Now an emergency happens. Bed 12, who was stable all morning, suddenly collapses into septic shock: blood pressure drops to 78, heart rate spikes to 135, oxygen drops to 86%, and consciousness shifts to confusion.
  > Our attention budget is already full with Beds 7 and 4. In a naive system, an emergency would wait in a backlog.
  > But WardPulse has a hard-coded clinical safety floor: Unequivocal physiological collapse bypasses all queuing and sounds an immediate, unmistakable Emergency Banner at the very top of the screen. Beds 7 and 4 stay in their slots. No patient is ever hidden when life is on the line."*
- **What the audience sees:**
  - A flashing red **"EMERGENCY BYPASS: BED 12 — CRITICAL PHYSIOLOGICAL COLLAPSE"** banner spans the top of the console.
  - The nurse can click **"Acknowledged / Done"** to log the emergency action into the audit trail.

---

## 4. Live Interactive Judge Test (Entering Real Vitals)

Invite a judge to test the system live:
1. Click **"Record New Vitals (Any Bed)"** floating at the bottom right.
2. Select **Bed 15** (currently green and stable).
3. Enter abnormal vitals:
   - Heart Rate: `130`
   - Systolic BP: `82`
   - Respiratory Rate: `28`
4. Click **"Submit Vitals"**.
5. **Show the judge:** Within 500ms, the ward strip re-evaluates, Bed 15 flashes red, and an immediate clinical card appears on the nurse console.

---

## 5. Live Mode Comparison Summary (The 5-Second Reveal)

Flip between **WardPulse** and **Naive NEWS2** one final time:

| What Judges Notice | Naive AI (NEWS2) | WardPulse |
| :--- | :---: | :---: |
| **Active Cards on Screen** | **11 simultaneous alarms** | **2 prioritized cards** |
| **Nurse Cognitive Load** | Alarm fatigue, chaotic scrolling | Calm, actionable 15-minute plan |
| **Chronic COPD (Bed 3)** | Constant false red alerts | Recognized personal baseline |
| **Stale Blood Pressure (Bed 4)** | Panicked false alarm | Actionable "Repeat BP" task |
| **Septic Collapse (Bed 12)** | Lost in the list of 11 alarms | Top-level Emergency Banner bypass |
| **False Alarm Reduction** | Baseline (High Fatigue) | **-73% reduction in active demands** |

---

## 6. Fallback Procedures (If Anything Fails)

- **If Wi-Fi drops or backend is unreachable:**
  - The frontend has zero external cloud dependencies.
  - Open `frontend/.env` and set `VITE_USE_MOCK=true`.
  - Restart frontend (`npm run dev`). The interactive console runs entirely in-memory with full simulation playback, sparklines, and story progressions.
- **If the simulation gets out of sync:**
  - Click the **"Reset"** button (circular arrow in the header clock).
  - Click **"Guided Demo"** $\to$ Story 1.
