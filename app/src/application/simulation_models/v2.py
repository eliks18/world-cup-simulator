"""Version 2 module."""

from app.src.domain.models.team import Team
from app.src.domain.models.team_metrics import TeamMetrics
from app.src.domain.simulation_model import BaseSimulationModel


class V2Model(BaseSimulationModel):
    """Version 2 model for world cup simulation."""

    def __init__(
        self,
        teams: list[Team],
        average_global_rating: float,
        average_tournament_rating: float,
        average_goals: float,
    ):
        """Model constructor."""
        self._teams = teams
        self._average_global_rating = average_global_rating
        self._average_tournament_rating = average_tournament_rating
        self._average_goals = average_goals
        self._average_offensive_rating = self._get_avg_offensive_rating()
        self._average_defensive_rating = self._get_avg_defensive_rating()
        self._team_metrics = self._set_teams_metrics()

    @property
    def average_offensive_rating(self):
        """Return the average offensive rating of the team."""
        return self._average_offensive_rating

    @property
    def average_defensive_rating(self):
        """Return the average defensive rating of the team."""
        return self._average_defensive_rating

    def _get_avg_offensive_rating(self) -> float:
        offensive_values = [
            self.offensive_rating(
                team,
                self._average_global_rating,
            )
            for team in self._teams
        ]
        return sum(offensive_values) / len(offensive_values)

    def _get_avg_defensive_rating(self) -> float:
        defensive_values = [
            self.defensive_rating(
                team,
                self._average_global_rating,
            )
            for team in self._teams
        ]
        return sum(defensive_values) / len(defensive_values)

    def _set_teams_metrics(self) -> dict[str, TeamMetrics]:
        return {
            team.name: TeamMetrics(
                offensive_rating=self.offensive_rating(
                    team,
                    self._average_tournament_rating,
                ),
                defensive_rating=self.defensive_rating(
                    team,
                    self._average_tournament_rating,
                ),
                weighted_form=self.weighted_form(
                    team,
                    self._average_tournament_rating,
                ),
                performance_score=self.performance_score(
                    team, self._average_tournament_rating
                ),
            )
            for team in self._teams
        }

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

        lambda_a = (
            base_goals_per_team
            * attack_factor_a
            * (1 / defense_factor_b)
            * elo_factor_a
            * form_a
        )
        lambda_b = (
            base_goals_per_team
            * attack_factor_b
            * (1 / defense_factor_a)
            * elo_factor_b
            * form_b
        )

        return lambda_a, lambda_b

    def get_team_metrics(
        self,
        team: Team,
    ) -> TeamMetrics:
        """Returns the metrics for a given team."""
        return self._team_metrics[team.name]

    @staticmethod
    def offensive_rating(team: Team, avg_tournament_rating: float) -> float:
        """Calculates the offensive rating of a team."""
        weighted_goals = []

        for match in team.history:
            weighted_goals.append(
                match.goals_for * (match.opponent_rating / avg_tournament_rating)
            )

        return sum(weighted_goals) / len(weighted_goals)

    @staticmethod
    def defensive_rating(team: Team, avg_tournament_rating: float) -> float:
        """Calculates the defensive rating of a team."""
        weighted_goals_against = []

        for match in team.history:
            weighted_goals_against.append(
                match.goals_against * (avg_tournament_rating / match.opponent_rating)
            )

        return sum(weighted_goals_against) / len(weighted_goals_against)

    @staticmethod
    def weighted_form(team: Team, avg_tournament_rating: float) -> float:
        """Calculates the weighted form of a team."""
        total_score = 0.0
        max_score = 0.0

        for match in team.history:
            if match.winner == team.name:
                points = 3
            elif match.winner is None:
                points = 1
            else:
                points = 0

            weight = match.opponent_rating / avg_tournament_rating

            total_score += points * weight
            max_score += 3 * weight

        return total_score / max_score

    @staticmethod
    def performance_score(
        team: Team,
        avg_tournament_rating: float,
    ) -> float:
        """Measures the recent form of a team."""
        return 0.0
