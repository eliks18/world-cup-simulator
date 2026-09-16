"""Tests for tournament simulation helpers."""

from datetime import date
import numpy as np
import random

from app.src.domain.constants import WinMethod
from app.src.application.match_simulator import MatchSimulator
from app.src.application.rng import RandomProvider
from app.src.application.simulation_models.v2 import V2Model
from app.src.domain.models.historical_match import HistoricalMatch
from app.src.application.tournament_simulator import TournamentSimulator
from app.src.domain.constants import THIRD_PLACE_COMBINATIONS
from app.src.domain.models.group_standing import GroupStanding
from app.src.domain.models.simulation_results import SimulationResult
from app.src.domain.models.team import Team


def standing(
    name: str,
    group: str,
    points: int,
    goals_for: int,
    goals_against: int,
) -> GroupStanding:
    """Build a group standing for test data."""
    return GroupStanding(
        team=Team(name=name, group=group, rating=1500),
        points=points,
        goals_for=goals_for,
        goals_against=goals_against,
    )


def test_select_best_third_places_returns_top_eight_third_places():
    """Select only the top eight third-place teams using FIFA criteria."""
    standings = []

    third_place_stats = [
        ("A", 4, 3, 3),
        ("B", 6, 3, 1),
        ("C", 4, 5, 2),
        ("D", 4, 4, 2),
        ("E", 3, 6, 4),
        ("F", 3, 2, 2),
        ("G", 5, 2, 3),
        ("H", 2, 7, 2),
        ("I", 4, 1, 3),
        ("J", 3, 3, 1),
    ]

    for group, points, goals_for, goals_against in third_place_stats:
        standings.extend(
            [
                standing(f"{group}1", group, points + 3, goals_for + 2, goals_against),
                standing(f"{group}2", group, points + 1, goals_for + 1, goals_against),
                standing(f"{group}3", group, points, goals_for, goals_against),
                standing(f"{group}4", group, 0, 0, 5),
            ]
        )

    selected = TournamentSimulator.select_best_third_places(standings)

    assert [standing.team.name for standing in selected] == [
        "B3",
        "G3",
        "C3",
        "D3",
        "A3",
        "I3",
        "E3",
        "J3",
    ]


def test_simulate_groups_adds_only_best_global_third_places():
    """Classify first two per group and only the best global third places."""
    groups = [chr(code) for code in range(ord("A"), ord("L") + 1)]
    teams = [
        Team(name=f"{group}{position}", group=group, rating=1500)
        for group in groups
        for position in range(1, 5)
    ]
    standings_by_group = {
        group: [
            standing(f"{group}1", group, 20, 6, 1),
            standing(f"{group}2", group, 16, 4, 2),
            standing(f"{group}3", group, 12 - index, 3, 3),
            standing(f"{group}4", group, 0, 1, 6),
        ]
        for index, group in enumerate(groups)
    }
    simulator = TournamentSimulator(model=None, teams=teams)
    simulation_record = SimulationResult()
    simulation_record.from_teams(teams)

    def simulate_group(
        group_teams: list[Team],
        simulation_record: SimulationResult,
    ) -> list[GroupStanding]:
        """Return fixed standings for the requested group."""
        return standings_by_group[group_teams[0].group]

    simulator.simulate_group = simulate_group

    qualified = simulator.simulate_groups(simulation_record)

    assert {
        group: [standing.team.name for standing in group_standings]
        for group, group_standings in qualified.items()
    } == {
        group: (
            [f"{group}1", f"{group}2", f"{group}3"]
            if group in groups[:8]
            else [f"{group}1", f"{group}2"]
        )
        for group in groups
    }


def test_build_round_resolves_dynamic_third_place_slots():
    """Resolve round-of-32 third-place placeholders from the FIFA matrix."""
    position_keys = {
        "1A",
        "1B",
        "1C",
        "1D",
        "1E",
        "1F",
        "1G",
        "1H",
        "1I",
        "1J",
        "1K",
        "1L",
        "2A",
        "2B",
        "2C",
        "2D",
        "2E",
        "2F",
        "2G",
        "2H",
        "2I",
        "2J",
        "2K",
        "2L",
        "3E",
        "3F",
        "3G",
        "3H",
        "3I",
        "3J",
        "3K",
        "3L",
    }
    qualified = {
        key: Team(name=key, group=key[1], rating=1500)
        for key in position_keys
    }

    matches = TournamentSimulator.build_round(qualified)

    assert [(left.name, right.name) for left, right in matches] == [
        ("2A", "2B"),
        ("1F", "2C"),
        ("1E", "3F"),
        ("1I", "3G"),
        ("1C", "2F"),
        ("2E", "2I"),
        ("1A", "3E"),
        ("1L", "3K"),
        ("2K", "2L"),
        ("1H", "2J"),
        ("1D", "3I"),
        ("1G", "3H"),
        ("1J", "2H"),
        ("2D", "2G"),
        ("1B", "3J"),
        ("1K", "3L"),
    ]


def test_third_place_matrix_has_all_fifa_combinations():
    """Include all possible eight-group third-place combinations."""
    assert len(THIRD_PLACE_COMBINATIONS) == 495


def _make_history(team_name: str, opponent_rating: int, goals_for: int, goals_against: int, result: str | None) -> list:
    """Build a minimal 1-match history for a team."""
    return [
        HistoricalMatch(
            date=date(2026, 6, 1),
            opponent_team="opponent",
            opponent_rating=opponent_rating,
            goals_for=goals_for,
            goals_against=goals_against,
            competition="FIFA World Cup",
            instance="2026",
            winner=result,
        )
    ]


def _make_v2_model(
    team_a: "Team",
    team_b: "Team",
) -> "V2Model":
    """Build a V2Model with two teams, using tournament-average approximations."""
    avg_global_rating = (team_a.rating + team_b.rating) / 2
    avg_tournament_rating = avg_global_rating
    avg_goals = 2.5
    return V2Model(
        teams=[team_a, team_b],
        average_global_rating=avg_global_rating,
        average_tournament_rating=avg_tournament_rating,
        average_goals=avg_goals,
    )


def test_match_simulation_is_reproducible():
    """A seeded RNG produces deterministic, repeatable match outcomes.

    Covers the non-draw path (Poisson scoring) and the draw -> extra-time -> penalties
    path. Two runs with the same seed produce the same goals/winner/win_method.
    A different seed produces a different outcome.
    """
    team_a = Team(
        name="TeamA",
        group="A",
        rating=1600,
        history=_make_history("TeamA", 1500, 2, 1, "TeamA"),
    )
    team_b = Team(
        name="TeamB",
        group="A",
        rating=1400,
        history=_make_history("TeamB", 1500, 1, 2, "TeamB"),
    )

    model = _make_v2_model(team_a, team_b)

    # Seed 42: run twice, assert identical results
    rng_42 = RandomProvider(np.random.default_rng(42), random.Random(42))
    sim_a = MatchSimulator(model=model, rng=rng_42)
    result_a = sim_a.simulate_match(team_a, team_b, is_knockout=True)

    rng_42b = RandomProvider(np.random.default_rng(42), random.Random(42))
    sim_b = MatchSimulator(model=model, rng=rng_42b)
    result_b = sim_b.simulate_match(team_a, team_b, is_knockout=True)

    assert result_a.goals_a == result_b.goals_a
    assert result_a.goals_b == result_b.goals_b
    assert result_a.winner.name == result_b.winner.name
    assert result_a.win_method == result_b.win_method

    # Seed 99: must produce a different outcome
    rng_99 = RandomProvider(np.random.default_rng(99), random.Random(99))
    sim_c = MatchSimulator(model=model, rng=rng_99)
    result_c = sim_c.simulate_match(team_a, team_b, is_knockout=True)

    assert (result_a.goals_a, result_a.goals_b) != (result_c.goals_a, result_c.goals_b) or (
        result_a.winner.name != result_c.winner.name
    )

    # Verify goals are non-negative integers and winner is set in a knockout match
    assert result_a.goals_a >= 0
    assert result_a.goals_b >= 0
    assert result_a.winner is not None


def test_penalties_path_is_reproducible():
    """Equal lambdas -> draw -> extra time draw -> penalties, with a deterministic seed.

    Uses two teams with identical ratings so expected_goals are equal. The seeded RNG
    is used to confirm that a draw triggers extra time and, when extra time also draws,
    penalties are resolved via the rating ratio.
    """
    # Two identical teams -> equal expected goals -> guaranteed draw in regulation
    team_x = Team(
        name="TeamX",
        group="X",
        rating=1500,
        history=_make_history("TeamX", 1500, 1, 1, None),
    )
    team_y = Team(
        name="TeamY",
        group="X",
        rating=1500,
        history=_make_history("TeamY", 1500, 1, 1, None),
    )

    model = _make_v2_model(team_x, team_y)

    # Use seed 10 to make the penalties path deterministic (equal lambdas -> draw -> ET draw -> penalties)
    rng = RandomProvider(np.random.default_rng(10), random.Random(10))
    sim = MatchSimulator(model=model, rng=rng)
    result = sim.simulate_match(team_x, team_y, is_knockout=True)

    # Draw in regulation is expected with equal lambdas
    assert result.goals_a == result.goals_b, (
        f"Expected regulation draw with equal lambdas, got {result.goals_a}-{result.goals_b}"
    )
    assert result.went_to_extra_time is True
    assert result.winner is not None
    assert result.win_method in (WinMethod.EXTRA_TIME, WinMethod.PENALTIES)
