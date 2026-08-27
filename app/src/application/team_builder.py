"""Team Builder module."""
from typing import Any

from app.src.domain.models.historical_match import HistoricalMatch
from app.src.domain.models.team import Team
from app.src.infrastructure.data_manager import CSVDataManager


class TeamBuilder:
    """Team Builder class."""

    def __init__(self, csv_data_manager: CSVDataManager):
        """Team Builder constructor."""
        self.csv_data_manager = csv_data_manager

    def build_teams(self) -> list[Team]:
        """Build teams from csv teams file."""
        teams = []

        for row in self.csv_data_manager.teams.to_dicts():
            teams.append(self.build_team(row))

        return teams

    def build_team(
        self,
        row: dict[str, Any],
    ) -> Team:
        """Build team row."""
        team_name = row["Team"]
        team = Team(
            name=team_name,
            group=row["Group"],
            rating=self.csv_data_manager.get_team_rating(team_name),
            history=self.build_history(team_name),
        )
        return team

    def build_history(
        self,
        team_name: str,
        limit: int = 10,
    ) -> list[HistoricalMatch]:
        """Build team match history from csv matches file."""
        team_matches = self.csv_data_manager.get_team_matches(team_name, limit)

        history = []

        for match in team_matches.iter_rows(named=True):
            is_home = match["HOME_TEAM"] == team_name
            opponent = match["AWAY_TEAM"] if is_home else match["HOME_TEAM"]

            history_match = HistoricalMatch(
                date=match["DATE"],
                opponent_team=opponent,
                opponent_rating=self.csv_data_manager.get_team_rating(opponent),
                goals_for=match["HOME_GOALS"] if is_home else match["AWAY_GOALS"],
                goals_against=match["AWAY_GOALS"] if is_home else match["HOME_GOALS"],
                competition=match["COMPETITION"],
                stage=match["STAGE"] or None,
                instance=match["INSTANCE"] or None,
                winner=match["WINNER"] or None,
            )
            history.append(history_match)
        return history
