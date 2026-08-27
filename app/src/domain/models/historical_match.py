from datetime import date

from pydantic import BaseModel


class HistoricalMatch(BaseModel):
    date: date
    opponent_team: str
    opponent_rating: int

    goals_for: int
    goals_against: int

    competition: str
    stage: str | None = None
    instance: str | None = None
    winner: str | None
