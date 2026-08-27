from pydantic import BaseModel

from app.src.domain.constants import WinMethod, TournamentStage
from app.src.domain.models.team import Team


class SimulatedMatch(BaseModel):
    stage: TournamentStage
    team_a: Team
    team_b: Team
    goals_a: int
    goals_b: int
    winner: Team | None = None
    win_method: WinMethod

