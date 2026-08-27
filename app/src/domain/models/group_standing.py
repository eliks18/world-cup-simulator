from pydantic import BaseModel

from app.src.domain.models.team import Team


class GroupStanding(BaseModel):
    team: Team

    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    points: int = 0

    goals_for: int = 0
    goals_against: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against
