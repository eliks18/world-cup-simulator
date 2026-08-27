from pydantic import BaseModel, Field

from app.src.domain.constants import MAX_ELO, NORMALIZED_GOAL_AVG
from app.src.domain.models.historical_match import HistoricalMatch


class Team(BaseModel):
    name: str
    group: str
    rating: int

    history: list[HistoricalMatch] = Field(default_factory=list)

    @property
    def form(self) -> float:
        score_map = {
            "W": 3,
            "D": 1,
            "L": 0,
        }

        points = sum(score_map[result] for result in self.matches)
        max_points = len(self.matches) * 3

        return points / max_points

    @property
    def goals_per_match(self) -> float:
        return self.GF / len(self.matches)

    @property
    def goals_against_per_match(self) -> float:
        return self.GA / len(self.matches)

    @property
    def overall_strength(self) -> float:
        return self.offensive_strength * 0.5 + self.defensive_strength * 0.5

    @property
    def offensive_strength(self) -> float:
        normalized_rating = self.rating / MAX_ELO

        attack = self.goals_per_match / NORMALIZED_GOAL_AVG

        return normalized_rating * 0.4 + self.form * 0.2 + attack * 0.4

    @property
    def defensive_strength(self) -> float:
        defense = 1 - min(
            self.goals_against_per_match / NORMALIZED_GOAL_AVG,
            1,
        )

        return self.form * 0.3 + defense * 0.7
