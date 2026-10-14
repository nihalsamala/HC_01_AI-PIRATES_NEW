"""
Ward simulator and patient builder.
"""

from datetime import datetime
from typing import List, Tuple

from shared.schemas import Patient, VitalsIn, VitalsReading


def build_ward(seed: int = 42) -> Tuple[List[Patient], List[VitalsReading]]:
    """Build simulated ward patients and prior vitals history."""
    return ([], [])


class Simulator:
    """Ward simulation clock and vitals generator."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def advance(self, to: datetime) -> List[VitalsIn]:
        return []

    def reset(self) -> None:
        pass
