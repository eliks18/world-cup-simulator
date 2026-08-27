from pydantic import BaseModel

from app.src.domain.constants import TournamentStage
from app.src.domain.models.team import Team


class TeamResult(BaseModel):
    team: Team
    stage: TournamentStage | None = None
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    champion: bool = False
    eliminated_by: str | None = None

    @property
    def average_goals(self) -> float:
        if self.matches_played == 0:
            return 0.0

        return self.goals_for / self.matches_played

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def win_rate(self) -> float:
        return (self.wins / self.matches_played) * 100