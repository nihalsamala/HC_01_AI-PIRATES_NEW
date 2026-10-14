"""
SQLAlchemy 2 ORM models for WardPulse (SQLite backend).

Tables follow contracts.md section 9 exactly.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PatientRow(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bed: Mapped[int] = mapped_column(Integer, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    conditions: Mapped[str] = mapped_column(JSON, default="[]")  # JSON list of strings
    admitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class VitalsRow(Base):
    __tablename__ = "vitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sbp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dbp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spo2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    on_oxygen: Mapped[bool] = mapped_column(Boolean, default=False)
    consciousness: Mapped[str] = mapped_column(String(1), default="A")
    source: Mapped[str] = mapped_column(String(20), default="sim")


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    bed: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_vital: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuditLogRow(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    patient_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(JSON, default="{}")  # JSON dict


class FeedbackRow(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # "done" or "not_useful"
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
