from __future__ import annotations

import math

import pytest

from solar import (
    BATTERY_BANK,
    GameState,
    HABITAT_DOME,
    PlacementError,
    SOLAR_PANEL,
)


def test_adjacency_bonus_increases_production_and_overflow():
    state = GameState(2, 1)
    state.place_structure(0, 0, SOLAR_PANEL)
    state.place_structure(1, 0, SOLAR_PANEL)

    report = state.advance_turn(sunlight=1.0, demand=0.0)

    assert math.isclose(report.production, 8.8, rel_tol=1e-6)
    assert math.isclose(report.consumption, 0.5, rel_tol=1e-6)
    assert math.isclose(report.overflow, 8.3, rel_tol=1e-6)
    assert report.stored == pytest.approx(0.0)
    assert report.discharged == pytest.approx(0.0)
    assert report.unmet_demand == pytest.approx(0.0)


def test_storage_clamps_and_deficits_are_tracked():
    state = GameState(2, 2)
    state.place_structure(0, 0, SOLAR_PANEL)
    state.place_structure(1, 0, BATTERY_BANK)

    first = state.advance_turn(sunlight=1.0, demand=2.0)
    assert first.overflow == pytest.approx(0.0)
    assert state.energy_storage == pytest.approx(1.7)

    second = state.advance_turn(sunlight=0.2, demand=3.0)
    assert second.stored == pytest.approx(0.0)
    assert second.discharged == pytest.approx(1.7)
    assert second.unmet_demand == pytest.approx(0.8)
    assert state.energy_storage == pytest.approx(0.0)
    assert state.unmet_demand == pytest.approx(0.8)


def test_cannot_place_on_invalid_tile():
    state = GameState(2, 2)
    with pytest.raises(PlacementError):
        state.place_structure(5, 5, SOLAR_PANEL)

    state.place_structure(0, 0, HABITAT_DOME)
    with pytest.raises(PlacementError):
        state.place_structure(0, 0, SOLAR_PANEL)


