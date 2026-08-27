from abc import ABC, abstractmethod

from app.src.domain.models.team import Team
from app.src.domain.models.team_metrics import TeamMetrics


class SimulationModel(ABC):

    @abstractmethod
    def expected_goals(self, team_a: Team, team_b: Team) -> tuple[float, float]:
        raise NotImplementedError


class BaseSimulationModel(SimulationModel):
    _team_metrics: dict[str, TeamMetrics]

    def get_team_metrics(
            self,
            team: Team,
    ) -> TeamMetrics:
        """Returns the metrics for a given team."""
        return self._team_metrics[team.name]
