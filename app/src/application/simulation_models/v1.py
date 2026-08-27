"""Version 1 module."""

from app.src.domain.models.team import Team
from app.src.domain.models.team_metrics import TeamMetrics
from app.src.domain.simulation_model import BaseSimulationModel


class V1Model(BaseSimulationModel):
    """Version 1 model for world cup simulation."""

    def __init__(self, teams: list[Team]):
        """Model constructor."""
        self._teams = teams
        self._team_metrics = self._set_teams_metrics()

    def _set_teams_metrics(self) -> dict[str, TeamMetrics]:
        return {
            team.name: TeamMetrics(
                offensive_rating=0.0,
                defensive_rating=0.0,
                weighted_form=0.0,
                performance_score=0.0,
            )
            for team in self._teams
        }

    def expected_goals(self, team_a: Team, team_b: Team) -> tuple[float, float]:
        """Calculates the expected goals between two teams for a match."""
        # Promedios ofensivos y defensivos
        atk_a = team_a.goals_per_match
        def_a = team_a.goals_against_per_match

        atk_b = team_b.goals_per_match
        def_b = team_b.goals_against_per_match

        # Goles esperados base
        lambda_a = (atk_a + def_b) / 2
        lambda_b = (atk_b + def_a) / 2

        # Ajuste por Elo
        rating_diff = team_a.rating - team_b.rating
        elo_factor = rating_diff / 1000

        lambda_a *= 1 + elo_factor
        lambda_b *= 1 - elo_factor

        # Ajuste por forma reciente
        form_diff = team_a.form - team_b.form
        form_factor = form_diff * 0.20

        lambda_a *= 1 + form_factor
        lambda_b *= 1 - form_factor

        # Evitar valores extremos
        lambda_a = max(0.2, lambda_a)
        lambda_b = max(0.2, lambda_b)

        return lambda_a, lambda_b
