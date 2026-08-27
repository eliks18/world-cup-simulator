"""Simulation Results module."""

import uuid

from pydantic import BaseModel, Field

from app.src.domain.constants import TournamentStage, WinMethod
from app.src.domain.models.match_result import MatchResult
from app.src.domain.models.simulated_match import SimulatedMatch
from app.src.domain.models.simulation_statistics import SimulationStatistics
from app.src.domain.models.team import Team
from app.src.domain.models.team_result import TeamResult
from app.src.domain.models.tournament_standings import TournamentStandings


class SimulationResult(BaseModel):
    """Simulation Result model."""
    simulation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    champion: TeamResult | None = None
    standings: TournamentStandings | None = None

    team_results: dict[str, TeamResult] = Field(default_factory=dict)

    matches: list[SimulatedMatch] = Field(default_factory=list)

    statistics: SimulationStatistics | None = Field(
        default_factory=SimulationStatistics
    )

    def from_teams(self, teams: list[Team]) -> None:
        self.team_results = {
            team.name: TeamResult(team=team)
            for team in teams
        }

        self.matches = []


    def record_match(self, match: MatchResult, stage: TournamentStage,):
        simulated_match = SimulatedMatch(
            stage=stage,
            team_a=match.team_a,
            team_b=match.team_b,
            goals_a=match.goals_a,
            goals_b=match.goals_b,
            winner=match.winner,
            win_method=match.win_method,
        )

        self.matches.append(simulated_match)

        self._update_team_result(match.team_a, simulated_match)
        self._update_team_result(match.team_b, simulated_match)

        self._update_statistics(simulated_match)

    def eliminate(self, team: Team, stage: TournamentStage, eliminated_by: Team | None = None):
        team_result = self.team_results[team.name]
        team_result.stage = stage
        team_result.eliminated_by = eliminated_by.name if eliminated_by else None

    def _update_team_result(self, team: Team, match: SimulatedMatch):
        result = self.team_results[team.name]

        if team == match.team_a:
            goals_for = match.goals_a
            goals_against = match.goals_b
        else:
            goals_for = match.goals_b
            goals_against = match.goals_a

        if match.winner is None:
            result.draws += 1
        elif match.winner == team:
            result.wins += 1
        else:
            result.losses += 1

        result.matches_played += 1
        result.goals_for += goals_for
        result.goals_against += goals_against


    def _update_statistics(self, match: SimulatedMatch):
        self.statistics.total_matches += 1

        self.statistics.total_goals += (
                match.goals_a +
                match.goals_b
        )

        if match.win_method == WinMethod.EXTRA_TIME:
            self.statistics.extra_time_matches += 1

            self.statistics.draws_after_90 += 1

        elif match.win_method == WinMethod.PENALTIES:
            self.statistics.penalty_shootouts += 1

            self.statistics.draws_after_90 += 1

    def finish(self, team: Team):
        self.champion = self.team_results[team.name]

        self.champion.champion = True
        self.champion.stage = TournamentStage.FINAL

    @property
    def matches_by_stage(self) -> dict[TournamentStage, list[SimulatedMatch]]:
        result = {}
        for stage in TournamentStage:
            result.setdefault(stage, [])
            for match in self.matches:
                if match.stage == stage:
                    result[stage].append(self.matches)
        return result

    @property
    def uuid_as_str(self) -> str:
        return str(self.simulation_id)