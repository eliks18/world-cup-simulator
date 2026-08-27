from pydantic import BaseModel

from app.src.domain.constants import WinMethod, TournamentStage
from app.src.domain.models.team import Team


class MatchResult(BaseModel):
    stage: TournamentStage

    team_a: Team
    team_b: Team

    goals_a: int
    goals_b: int

    winner: Team | None = None

    went_to_extra_time: bool = False
    went_to_penalties: bool = False

    win_method: WinMethod

    @property
    def is_draw(self) -> bool:
        return self.goals_a == self.goals_b

    @property
    def has_winner(self) -> bool:
        return self.winner is not None
