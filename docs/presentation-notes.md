# WardPulse Presentation Notes & Judge Defense

This guide prepares the presentation team for the final hackathon pitch, slide deck delivery, and tough questions from clinical judges, medical informaticians, and technical jurors.

---

## 1. Slide-by-Slide Pitch Outline (5–7 Minute Presentation)

### Slide 1: Title & Hook
- **Slide Title:** **WardPulse: An AI Nurse Attention Allocator for Understaffed Hospital Wards**
- **Speaker Script:**
  > *"Imagine you are a nurse on night shift. You are responsible for twenty acute medical patients. Your ward monitor is blaring alarms every four minutes. Half of them are for a COPD patient whose oxygen saturation is always 90%. After three hours, you tune them out. Then, a post-operative patient quietly deteriorates—and nobody notices until she goes into cardiac arrest.
  > This is not a failure of nursing. This is a failure of system design. Today, we are presenting WardPulse: an AI Attention Allocator that protects patient safety while curing alarm fatigue."*

---

### Slide 2: The Hidden Crisis on Hospital Wards
- **Key Points:**
  - Standard nurse-to-patient ratios on general wards: **1:10 to 1:15**.
  - Conventional systems (like UK NEWS2) rely on **rigid population thresholds**.
  - A single abnormal vital sign triggers a panic alarm regardless of individual baseline.
  - Result: Over **10 alarms simultaneously** in a 20-bed ward; **85%+ false alarm rate**.
- **Speaker Script:**
  > *"Hospital wards are not ICUs. We don't have one nurse per patient, and patients aren't connected to twenty continuous monitors. When early warning scores treat every patient identically, nurses drown in alerts. If everything is an emergency, nothing is."*

---

### Slide 3: The Core Clinical Insights
- **Key Points:**
  1. **Personal Baselines:** Compare vitals to the patient's individual running median and MAD, conditioned on chronic illness priors.
  2. **Freshness vs. Risk:** A missing observation is a triage measurement task, not a panicked call to a physician.
  3. **Attention Budgeting ($K=2$):** Direct the nurse's immediate attention to the **top 2 actions for the next 15 minutes**.
  4. **Safety Floor:** Unequivocal collapse immediately bypasses all queuing into an emergency banner.

---

### Slide 4: System Architecture & Safety Guarantees
- **Visual:** Architectural flow diagram (Data $\to$ Baseline Engine $\to$ Safety Floor $\to$ Task Prioritizer $\to$ React Console).
- **Speaker Script:**
  > *"WardPulse is built on a pure-logic clinical engine. Time is deterministic, observations have zero lookahead, and every output comes from a clinically validated closed set of actions. We never allow generative LLMs to hallucinate drug dosages or diagnostic advice. Patient safety is hard-coded into the architecture."*

---

### Slide 5: The Live Demonstration
- **Action:** Open [http://localhost:5173](http://localhost:5173), launch **Guided Demo Mode**, and step through the 3 stories:
  - **Story 1 (07:00):** Same RR (22) $\to$ Bed 3 (COPD) calm, Bed 7 (Post-op) prioritized. Toggle to Naive AI to reveal the 11-alarm flood!
  - **Story 2 (09:00):** 7h old blood pressure on Bed 4 $\to$ focused `"Repeat manual BP"` task rather than false alarm.
  - **Story 3 (11:00):** Septic crash on Bed 12 $\to$ instant **Emergency Banner** bypass while active budget holds steady.

---

### Slide 6: Rigorous Quantitative Evaluation
- **Visual:** The Comparative Benchmark Table (from `docs/evaluation.md`).
- **Real Numbers to Cite (PhysioNet CinC 2019, n=1,999 cases):**
  - **Full Clinical Sensitivity Parity:** **74.5%** (137/184 events detected; 95% Wilson CI: [67.7%, 80.2%]), matching NEWS2 (73.9%, 136/184; [67.1%, 79.7%]).
  - **Bedside Intervention Lead Time:** **32.0 hours median lead time** before documented sepsis event (95% bootstrap CI: [26.0h, 43.0h]).
  - **Proactive Triage:** **2.84 measurement tasks/nurse-hour** scheduled to resolve ambiguous vital trajectories.
  - **Cognitive Load Reduction (SIMULATED):** Drops active shift demands from an average of **3.18 alarms down to 1.68 budgeted cards (-47.0% load reduction)**.

---

### Slide 7: Ethical AI, Clinical Disclosures & Limitations
- **Key Points:**
  - **Decision support only:** Augments nursing judgment, never diagnoses.
  - **Domain shift honesty:** Public datasets originate in ICUs; general ward cadence requires ~4h downsampling.
  - **Proof of concept:** Hackathon innovation prototype; not FDA/CE cleared.
- **Speaker Script:**
  > *"We don't claim autonomous medicine. WardPulse is an intelligent workflow assistant designed to keep nurses calm, organized, and focused on the bedside actions that save lives."*

---

### Slide 8: Roadmap & Next Steps
- **Next Milestones:**
  - Native HL7/FHIR observation streaming from wireless vitals carts.
  - Wearable patch integration (continuous SpO2/HR sensors).
  - Prospective clinical observational registry study on medical/surgical wards.

---

## 2. Likely Judge Questions & Battle-Tested Answers

### Q1: "Why not use a Large Language Model (LLM) or GPT-4 to generate the action cards?"
- **Honest Clinical Answer:**
  > *"In acute clinical deterioration, deterministic safety and traceability are paramount. An LLM can hallucinate medication dosages, formulate unauthorized differential diagnoses, or produce non-standard nursing instructions. WardPulse restricts all recommendations to a strictly typed, closed set of actionable nursing protocols (`page_doctor`, `repeat_reading`, `semi_fowlers_position`, `increase_monitoring_frequency`). The system is 100% auditable and reproducible."*

---

### Q2: "What if two patients are already in the top 2 slots, and a third patient deteriorates? Won't someone die waiting in the queue?"
- **Honest Clinical Answer:**
  > *"No, because of our **two-tier safety architecture**:
  > 1. **The Crash Bypass:** Any unequivocal physiological collapse (severe shock, respiratory failure, coma) immediately bypasses the attention budget and surfaces in an unmistakable top-level Emergency Banner.
  > 2. **Task Aging & Escalation:** In the standby queue, tasks accumulate priority dynamically with waiting time. If a patient's trend worsens, their priority score jumps ahead of existing tasks, ensuring high-velocity escalation."*

---

### Q3: "If you adjust for personal baselines in chronic COPD patients, couldn't you miss a genuine deterioration?"
- **Honest Clinical Answer:**
  > *"We addressed this with our **Hard Safety Floor Guarantee**. A personal baseline is only allowed to discount false positives when vitals are stable around that established baseline. If any vital crosses an absolute physiological red line (such as RR > 30, SBP < 85, or SpO2 < 85%), safety rules override the baseline completely and mandate immediate escalation. Personal baselines can never suppress a hard red-line breach."*

---

### Q4: "You trained an optional LightGBM model. Why is it turned off by default?"
- **Honest Engineering Answer:**
  > *"The LightGBM model and its 1.000 AUROC metric came strictly from our synthetic cohort—they are **synthetic cohort results, not evidence of real-world accuracy**. When we benchmarked on real clinical records, transparent rule-based features—baseline z-scores, trend slopes, and shock index—already achieved full sensitivity parity (74.5% vs 73.9%) and identical 32.0h lead time. Because an opaque tree model adds computational opacity without measurable lead time improvement, our ML hook is **disabled by default (`ENABLE_ML = False`)**. In clinical AI, explainability and transparency must win."*

---

### Q5: "How does the system handle missing or incomplete vitals?"
- **Honest Technical Answer:**
  > *"Missing vitals are treated as clinically significant information, never as fatal errors or normal zeroes. In our engine, every vital sign can be `None`. The system tracks observation age independently for each vital. When a reading becomes stale, WardPulse creates a triage task to measure that specific vital sign, closing information gaps before making escalation decisions."*

---

### Q6: "Is this certified as a medical device?"
- **Honest Regulatory Answer:**
  > *"WardPulse is an academic proof-of-concept developed for this hackathon. It is classified as Clinical Decision Support (CDS) software under FDA Section 520(o). Before clinical deployment, it would require prospective observational trials, institutional review board (IRB) approval, and formal regulatory clearance."*

---

## 3. Quick Reference Card for Presenters

| Fact / Metric | Exact Value | Context to Mention |
| :--- | :---: | :--- |
| **Sensitivity** | **74.5%** (137/184) | 95% Wilson CI: [67.7%, 80.2%]; PhysioNet CinC 2019, $n=1,999$ |
| **Median Lead Time** | **32.0 hours** | 95% bootstrap CI: [26.0h, 43.0h]; identical to NEWS2 |
| **Attention Budget** | **$K = 2$ cards** | Focuses nurse on top immediate demands for next 15 min |
| **On-Screen Load Drop** | **-47.0%** | SIMULATED: drops 6h demo shift mean from 3.18 to 1.68 cards |
| **Emergency Bypass** | **Instant** | Unequivocal collapse bypasses budget into Emergency Banner |
| **Model Status** | **Disabled** | Synthetic cohort only, not evidence of accuracy (`ENABLE_ML = False`) |
| **Backend Tests** | **65 / 65 passing** | Full pytest coverage across API, engine, simulator, eval, and ML |

---

## 4. Citation & Public Dataset Attribution

Public evaluation records derived from the PhysioNet Challenge 2019:
> **Citation:**
> Reyna, M. A., Josef, C., Jeter, R., Shashikumar, S. P., Westover, M. B., Nemati, S., Clifford, G. D., & Sharma, A. (2019). Early Detection of Sepsis from Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019. *Critical Care Medicine*, 48(2), e74–e81. https://doi.org/10.13026/v64v-d857.
> Distributed under Creative Commons Attribution 4.0 International (CC BY 4.0).

