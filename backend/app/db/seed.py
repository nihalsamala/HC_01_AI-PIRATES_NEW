"""
Database seed script for WardPulse.

Resets the DB and loads patients and history from build_ward(seed).
If build_ward returns empty (stub), seeds 3 tiny placeholder patients.

Usage:
    cd backend && python -m app.db.seed
"""

from datetime import datetime

from app.db.models import AuditLogRow, PatientRow, VitalsRow
from app.db.session import reset_db, SessionLocal

from shared.schemas import Consciousness, Source


def seed_db(seed: int = 42) -> None:
    """Reset DB and load ward data."""
    reset_db()

    # Try loading from the simulator
    try:
        from simulator.ward import build_ward
        patients, readings = build_ward(seed)
    except Exception:
        patients, readings = [], []

    db = SessionLocal()
    try:
        if patients:
            # Real data from simulator
            for p in patients:
                db.add(PatientRow(
                    id=p.id,
                    bed=p.bed,
                    age=p.age,
                    conditions=[c.value for c in p.conditions],
                    admitted_at=p.admitted_at,
                    display_name=p.display_name,
                ))

            for r in readings:
                db.add(VitalsRow(
                    patient_id=r.patient_id,
                    timestamp=r.timestamp,
                    hr=r.hr,
                    sbp=r.sbp,
                    dbp=r.dbp,
                    rr=r.rr,
                    spo2=r.spo2,
                    temp=r.temp,
                    on_oxygen=r.on_oxygen,
                    consciousness=r.consciousness.value if r.consciousness else "A",
                    source=r.source.value if r.source else "sim",
                ))
        else:
            # Placeholder patients so the API still works
            now = datetime(2026, 10, 20, 6, 0)
            for bed in range(1, 4):
                db.add(PatientRow(
                    id=bed,
                    bed=bed,
                    age=55 + bed * 5,
                    conditions=[],
                    admitted_at=now,
                    display_name=f"Bed {bed}",
                ))
                # One placeholder vital per patient
                db.add(VitalsRow(
                    patient_id=bed,
                    timestamp=now,
                    hr=72.0,
                    sbp=120.0,
                    dbp=80.0,
                    rr=16.0,
                    spo2=98.0,
                    temp=36.6,
                    on_oxygen=False,
                    consciousness="A",
                    source="sim",
                ))

        # Initial audit log entry
        db.add(AuditLogRow(
            timestamp=datetime.utcnow() if not patients else patients[0].admitted_at,
            event_type="db_seeded",
            details={"patient_count": len(patients) if patients else 3,
                     "reading_count": len(readings) if readings else 3},
        ))

        db.commit()
        patient_count = len(patients) if patients else 3
        reading_count = len(readings) if readings else 3
        print(f"[OK] Database seeded: {patient_count} patients, {reading_count} vitals readings")

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
