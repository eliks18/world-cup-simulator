"""Version 3 module."""

from app.src.application.simulation_models.v2 import V2Model
from app.src.domain.constants import (
    COMPETITION_WEIGHTS,
    INSTANCE_WEIGHTS,
    STAGE_WEIGHTS,
)
from app.src.domain.models.historical_match import HistoricalMatch
from app.src.domain.models.team import Team


class V3Model(V2Model):
    """Version 3 model for world cup simulation."""

    def _get_avg_offensive_rating(self) -> float:
        offensive_values = [
            self.offensive_rating(
                team,
                self._average_global_rating,
            )
            for team in self._teams
        ]
        return sum(offensive_values) / len(offensive_values)

    @staticmethod
    def _recency_weight(
        position: int,
    ) -> float:
        return max(0.5, 1.0 - (position * 0.03))

    def expected_goals(self, team_a: Team, team_b: Team) -> tuple[float, float]:
        """Calculates the expected goals between two teams for a match."""
        metrics_a = self.get_team_metrics(team_a)
        metrics_b = self.get_team_metrics(team_b)

        attack_a = metrics_a.offensive_rating / self._average_offensive_rating
        attack_b = metrics_b.offensive_rating / self._average_offensive_rating

        attack_factor_a = attack_a**0.8
        attack_factor_b = attack_b**0.8

        defense_a = self._average_defensive_rating / metrics_a.defensive_rating
        defense_b = self._average_defensive_rating / metrics_b.defensive_rating

        defense_factor_a = defense_a**0.5
        defense_factor_b = defense_b**0.5

        elo_a = team_a.rating / self._average_tournament_rating
        elo_b = team_b.rating / self._average_tournament_rating

        elo_factor_a = elo_a**2.0
        elo_factor_b = elo_b**2.0

        form_a = 0.9 + (0.2 * metrics_a.weighted_form)
        form_b = 0.9 + (0.2 * metrics_b.weighted_form)

        base_goals_per_team = self._average_goals / 2

        performance_factor_a = 1 + (metrics_a.performance_score * 0.05)
        performance_factor_b = 1 + (metrics_b.performance_score * 0.05)

        lambda_a = (
            base_goals_per_team
            * attack_factor_a
            * (1 / defense_factor_b)
            * elo_factor_a
            * form_a
            * performance_factor_a
        )
        lambda_b = (
            base_goals_per_team
            * attack_factor_b
            * (1 / defense_factor_a)
            * elo_factor_b
            * form_b
            * performance_factor_b
        )

        return lambda_a, lambda_b

    def get_match_weight(
        self,
        match: HistoricalMatch,
        position: int,
    ) -> float:
        """Returns the weight of a match based on different parameters."""
        competition_weight = COMPETITION_WEIGHTS.get(
            match.competition,
            1.0,
        )

        stage_weight = STAGE_WEIGHTS.get(
            match.stage,
            1.0,
        )

        instance_weight = INSTANCE_WEIGHTS.get(
            match.instance,
            1.0,
        )

        recency_weight = self._recency_weight(position)

        return competition_weight * stage_weight * instance_weight * recency_weight

    def offensive_rating(self, team: Team, avg_tournament_rating: float) -> float:
        """Calculates the offensive rating of a team."""
        total = 0.0
        total_weight = 0.0

        for position, match in enumerate(team.history):
            opponent_factor = match.opponent_rating / avg_tournament_rating
            weight = self.get_match_weight(match, position)

            total += match.goals_for * opponent_factor * weight

            total_weight += weight

        return total / total_weight

    def defensive_rating(self, team: Team, avg_tournament_rating: float) -> float:
        """Calculates the defensive rating of a team."""
        total = 0.0
        total_weight = 0.0

        for position, match in enumerate(team.history):
            opponent_factor = avg_tournament_rating / match.opponent_rating
            weight = self.get_match_weight(match, position)

            total += match.goals_against * opponent_factor * weight

            total_weight += weight

        return total / total_weight

    def weighted_form(
        self,
        team: Team,
        avg_tournament_rating: float,
    ) -> float:
        """Calculates the weighted form of a team."""
        total_score = 0.0
        max_score = 0.0

        for position, match in enumerate(team.history):
            if match.winner == team.name:
                points = 3
            elif match.winner is None:
                points = 1
            else:
                points = 0

            opponent_weight = match.opponent_rating / avg_tournament_rating

            match_weight = self.get_match_weight(match, position)

            total_score += points * opponent_weight * match_weight

            max_score += 3 * opponent_weight * match_weight

        return total_score / max_score

    def performance_score(
        self,
        team: Team,
        avg_tournament_rating: float,
    ) -> float:
        """Measures the recent form of a team."""
        total = 0.0
        total_weight = 0.0

        for position, match in enumerate(team.history):
            weight = self.get_match_weight(
                match,
                position,
            )

            expected_goal_diff = (team.rating - match.opponent_rating) / 200
            actual_goal_diff = match.goals_for - match.goals_against

            performance = actual_goal_diff - expected_goal_diff

            total += performance * weight
            total_weight += weight

        return total / total_weight
