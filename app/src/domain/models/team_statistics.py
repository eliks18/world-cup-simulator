from pydantic import BaseModel

from app.src.domain.constants import TournamentStage


class TeamStatistics(BaseModel):
    team: str
    stage: TournamentStage
    eliminated_by: str | None = None
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0