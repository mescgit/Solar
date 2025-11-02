"""Game state management for the Solar simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from .structures import Structure, BATTERY_BANK


class PlacementError(ValueError):
    """Raised when attempting to place an invalid structure."""


@dataclass(slots=True)
class EnergyReport:
    """Summary of a single turn of the simulation."""

    production: float
    consumption: float
    stored: float
    discharged: float
    unmet_demand: float
    overflow: float

    @property
    def net(self) -> float:
        """Net energy change before storage considerations."""

        return self.production - self.consumption


class GameState:
    """Mutable state container that tracks structures and energy balance."""

    width: int
    height: int
    _tiles: List[Optional[Structure]]
    energy_storage: float
    max_storage: float
    unmet_demand: float

    def __init__(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Board dimensions must be positive")

        self.width = width
        self.height = height
        self._tiles = [None for _ in range(width * height)]
        self.energy_storage = 0.0
        self.max_storage = 0.0
        self.unmet_demand = 0.0

    # ------------------------------------------------------------------
    # Board helpers
    # ------------------------------------------------------------------
    def _index(self, x: int, y: int) -> int:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise PlacementError(f"Tile ({x}, {y}) is outside the board")
        return y * self.width + x

    def _neighbors(self, index: int) -> Iterable[int]:
        x, y = index % self.width, index // self.width
        if x > 0:
            yield index - 1
        if x < self.width - 1:
            yield index + 1
        if y > 0:
            yield index - self.width
        if y < self.height - 1:
            yield index + self.width

    def _adjacent_same_type(self, index: int) -> int:
        structure = self._tiles[index]
        if structure is None:
            return 0
        return sum(
            1
            for neighbor in self._neighbors(index)
            if self._tiles[neighbor] is not None
            and self._tiles[neighbor].name == structure.name
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def place_structure(self, x: int, y: int, structure: Structure) -> None:
        """Place ``structure`` on the given tile.

        Raises ``PlacementError`` if the tile is already occupied or invalid.
        """

        index = self._index(x, y)
        if self._tiles[index] is not None:
            raise PlacementError(f"Tile ({x}, {y}) is already occupied")

        self._tiles[index] = structure
        if structure.storage_capacity:
            self.max_storage += structure.storage_capacity

    def remove_structure(self, x: int, y: int) -> None:
        index = self._index(x, y)
        structure = self._tiles[index]
        if structure is None:
            raise PlacementError(f"Tile ({x}, {y}) is empty")

        self._tiles[index] = None
        if structure.storage_capacity:
            self.max_storage = max(0.0, self.max_storage - structure.storage_capacity)
            self.energy_storage = min(self.energy_storage, self.max_storage)

    def structures(self) -> Tuple[Optional[Structure], ...]:
        """Return an immutable snapshot of the grid contents."""

        return tuple(self._tiles)

    def advance_turn(self, sunlight: float, demand: float) -> EnergyReport:
        """Resolve a single game turn.

        ``sunlight`` modulates production: ``1.0`` represents a clear day, while ``0`` is a blackout.
        ``demand`` is the colony consumption outside of upkeep (e.g., research, growth).
        """

        if sunlight < 0:
            raise ValueError("Sunlight cannot be negative")
        if demand < 0:
            raise ValueError("Demand cannot be negative")

        production = 0.0
        upkeep = 0.0
        storage_capacity = 0.0

        for idx, structure in enumerate(self._tiles):
            if structure is None:
                continue

            upkeep += structure.upkeep
            if structure.storage_capacity:
                storage_capacity += structure.storage_capacity

            neighbors = self._adjacent_same_type(idx)
            production += structure.production(sunlight, neighbors)

        # Update storage cap in case structures were removed or added before turn.
        self.max_storage = storage_capacity
        self.energy_storage = min(self.energy_storage, self.max_storage)

        net = production - upkeep - demand
        stored = 0.0
        discharged = 0.0
        overflow = 0.0

        if net >= 0:
            available_capacity = self.max_storage - self.energy_storage
            stored = min(net, available_capacity)
            self.energy_storage += stored
            overflow = net - stored
            unmet = 0.0
        else:
            requirement = -net
            discharged = min(self.energy_storage, requirement)
            self.energy_storage -= discharged
            unmet = requirement - discharged
            self.unmet_demand += unmet

        # Batteries consume upkeep but do not produce energy; prevent negative storage when no batteries.
        if self.max_storage == 0 and self.energy_storage != 0:
            self.energy_storage = 0.0

        report = EnergyReport(
            production=production,
            consumption=upkeep + demand,
            stored=stored,
            discharged=discharged,
            unmet_demand=unmet,
            overflow=overflow,
        )
        return report

    # Convenience constructors ------------------------------------------------
    @classmethod
    def with_defaults(cls) -> "GameState":
        """Return a 3x3 grid pre-populated with a small starter layout."""

        state = cls(3, 3)
        state.place_structure(1, 0, BATTERY_BANK)
        state.place_structure(0, 1, BATTERY_BANK)
        return state
