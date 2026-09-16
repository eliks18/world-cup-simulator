"""Match simulator module."""

import random

import numpy as np

from app.src.application.rng import RandomProvider
from app.src.domain.constants import WinMethod, TournamentStage
from app.src.domain.models.match_result import MatchResult
from app.src.domain.models.team import Team
from app.src.domain.simulation_model import SimulationModel


class MatchSimulator:
    """Match simulator class."""

    def __init__(self, model: SimulationModel, rng: RandomProvider | None = None):
        """Match simulator constructor."""
        self.model = model
        if rng is None:
            rng = RandomProvider(np.random.default_rng(), random.Random())
        self.rng = rng

    def _resolve_knockout(
        self, stage:TournamentStage, team_a: Team, team_b: Team, goals_a: int, goals_b: int
    ) -> MatchResult:
        went_to_extra_time = False
        went_to_penalties = False
        win_method = WinMethod.FULL_TIME

        # Went to extra time
        if goals_a == goals_b:
            went_to_extra_time = True
            win_method = WinMethod.EXTRA_TIME
            goals_a, goals_b = self._play_extra_time(goals_a, goals_b)

            if goals_a == goals_b:
                went_to_penalties = True
                win_method = WinMethod.PENALTIES
                winner = self._simulate_penalties(team_a, team_b)
            elif goals_a > goals_b:
                winner = team_a
            else:
                winner = team_b

        elif goals_a > goals_b:
            winner = team_a
        else:
            winner = team_b

        return MatchResult(
            stage=stage,
            team_a=team_a,
            team_b=team_b,
            goals_a=goals_a,
            goals_b=goals_b,
            winner=winner,
            went_to_extra_time=went_to_extra_time,
            went_to_penalties=went_to_penalties,
            win_method=win_method,
        )

    def _generate_score(
        self,
        lambda_a: float,
        lambda_b: float,
    ) -> tuple[int, int]:
        return (
            self.rng.poisson(lambda_a),
            self.rng.poisson(lambda_b),
        )

    def _simulate_penalties(self, team_a: Team, team_b: Team) -> Team:
        probability = team_a.rating / (team_a.rating + team_b.rating)

        return team_a if self.rng.uniform() < probability else team_b

    def _play_extra_time(self, goals_a: int, goals_b: int) -> tuple[int, int]:
        goals_a += self.rng.poisson(0.15)
        goals_b += self.rng.poisson(0.15)
        return goals_a, goals_b

    def simulate_match(
        self, team_a: Team, team_b: Team, is_knockout: bool = True, stage=TournamentStage.GROUP_STAGE
    ) -> MatchResult:
        """Simulate a match between two teams."""
        winner = None
        lambda_a, lambda_b = self.model.expected_goals(
            team_a,
            team_b,
        )

        # Generar goles
        goals_a, goals_b = self._generate_score(
            lambda_a,
            lambda_b,
        )
        if goals_a > goals_b:
            winner = team_a
        elif goals_b > goals_a:
            winner = team_b

        # Eliminación directa
        if is_knockout:
            knockout_match_result = self._resolve_knockout(
                stage,
                team_a,
                team_b,
                goals_a,
                goals_b,
            )
            return knockout_match_result

        return MatchResult(
            stage=stage,
            team_a=team_a,
            team_b=team_b,
            goals_a=goals_a,
            goals_b=goals_b,
            winner=winner,
            win_method=WinMethod.FULL_TIME,
        )
