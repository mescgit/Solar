"""Core simulation primitives for the Solar prototype."""

from .structures import Structure, SOLAR_PANEL, BATTERY_BANK, HABITAT_DOME
from .state import GameState, EnergyReport, PlacementError

__all__ = [
    "Structure",
    "SOLAR_PANEL",
    "BATTERY_BANK",
    "HABITAT_DOME",
    "GameState",
    "EnergyReport",
    "PlacementError",
]
