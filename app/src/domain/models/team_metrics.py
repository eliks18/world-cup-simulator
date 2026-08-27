from pydantic import BaseModel


class TeamMetrics(BaseModel):
    offensive_rating: float
    defensive_rating: float
    weighted_form: float
    performance_score: float
