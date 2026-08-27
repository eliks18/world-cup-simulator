from pydantic import BaseModel


class SimulationStatistics(BaseModel):
    total_matches: int = 0
    total_goals: int = 0
    penalty_shootouts: int = 0
    extra_time_matches: int = 0
    draws_after_90: int = 0

    @property
    def average_goals(self) -> float:
        if self.total_matches == 0:
            return 0.0

        return self.total_goals / self.total_matches