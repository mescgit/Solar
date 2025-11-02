"""Structure definitions for the Solar simulation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Structure:
    """Immutable description of a placeable structure."""

    name: str
    base_production: float = 0.0
    upkeep: float = 0.0
    storage_capacity: float = 0.0
    adjacency_bonus: float = 0.0

    def production(self, sunlight: float, neighbors: int = 0) -> float:
        """Return the raw energy produced this turn.

        The ``neighbors`` argument is the count of directly adjacent tiles with the same
        structure. The adjacency bonus is applied linearly per neighbor. Production is never
        negative, even if sunlight dips below zero in extreme scripted scenarios.
        """

        bonus = self.adjacency_bonus * neighbors
        raw = (self.base_production + bonus) * sunlight
        return max(0.0, raw)


SOLAR_PANEL = Structure(
    name="Solar Panel",
    base_production=4.0,
    upkeep=0.25,
    adjacency_bonus=0.4,
)

BATTERY_BANK = Structure(
    name="Battery Bank",
    storage_capacity=12.0,
    upkeep=0.05,
)

HABITAT_DOME = Structure(
    name="Habitat Dome",
    upkeep=1.6,
)
