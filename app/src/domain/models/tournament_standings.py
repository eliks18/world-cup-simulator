from pydantic import BaseModel

from app.src.domain.models.team import Team


class TournamentStandings(BaseModel):
    champion: Team
    runner_up: Team
    third_place: Team | None

    semi_finalists: list[Team]
    quarter_finalists: list[Team]
    round_of_16: list[Team]