# WardPulse Frontend — Nurse Console

The WardPulse nurse console is an AI early warning interface designed specifically for overloaded hospital ward nurses. Instead of flooding screens with dozens of alarms, it highlights the top 2 prioritized clinical actions for the next 15 minutes.

## Features

- **Personal Baseline Awareness**: Recognizes chronic conditions (e.g. COPD baseline RR 22 in Bed 3 is not an acute emergency; post-op RR 22 in Bed 7 is).
- **Top 2 Focus Cards**: Budgeted priority actions preventing nurse alarm fatigue.
- **Standby Queue**: Ranked by urgency and waiting time aging.
- **Unequivocal Crash Bypass**: Immediate top-of-screen emergency alert for crash vitals (Bed 12).
- **20-Bed Interactive Strip**: Color-coded ward status with stale data and open task indicators.
- **Patient Detail Drawer**: Vital trends with inline SVG sparklines, personal baseline conditions, and plain-language clinical reasons.
- **Quick Vitals Entry**: Fast tablet input for HR, BP, RR, SpO2, Temp, and ACVPU consciousness scale.
- **Mode Toggle Comparison**: Live side-by-side comparison between Naive AI (NEWS2) and WardPulse.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables

Create a `.env` file in `frontend/` if needed:

```bash
# Set to 'false' when connecting to the real FastAPI backend
VITE_USE_MOCK=true

# FastAPI backend base URL
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173).

### 4. Production Build

```bash
npm run build
npm run preview
```
