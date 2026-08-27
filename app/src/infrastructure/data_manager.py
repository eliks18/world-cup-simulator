"""CSVDataManager module."""
import polars as pl


class CSVDataManager:
    """Class to manage CSV data provided from different source files."""
    def __init__(self, teams_csv: str, ratings_csv: str, matches_csv: str):
        """DataManager constructor."""
        self._teams_df = pl.read_csv(teams_csv)
        self._ratings_df = pl.read_csv(ratings_csv)
        self._matches_df = (
            pl.read_csv(
                matches_csv,
                try_parse_dates=True,
            )
            .fill_null("")
        )

        self._ratings_map = dict(
            zip(
                self._ratings_df["Team"],
                self._ratings_df["Rating"],
            )
        )
        self._average_global_rating = self._ratings_df["Rating"].mean()
        self._average_goals = self._get_avg_goals()
        self._average_tournament_rating = self._get_avg_tournament_rating()

    @property
    def teams(self) -> pl.DataFrame:
        """Return a DataFrame containing information of the teams in the tournament."""
        return self._teams_df

    @property
    def matches(self) -> pl.DataFrame:
        """Return a DataFrame containing the last matches of each team of the tournament."""
        return self._matches_df

    @property
    def average_global_rating(self) -> float:
        """Return the average global rating."""
        return self._average_global_rating

    @property
    def average_tournament_rating(self) -> float:
        """Return the average tournament rating."""
        return self._average_tournament_rating

    @property
    def average_goals(self) -> float:
        """Return the average goals per match in the tournament."""
        return self._average_goals

    @staticmethod
    def deduplicate(origin_file: str, destiny_file: str) -> None:
        """Remove duplicate matches rows from a CSV file."""
        origin_df = pl.read_csv(origin_file)
        keys = [
            "DATE",
            "HOME_TEAM",
            "AWAY_TEAM",
            "HOME_GOALS",
            "AWAY_GOALS",
        ]

        duplicates = (
            origin_df
            .join(
                origin_df
                .group_by(keys)
                .len()
                .filter(pl.col("len") > 1),
                on=keys,
                how="inner",
            )
            .drop("len")
        )

        print(duplicates)

        keys = [
            "DATE",
            "HOME_TEAM",
            "AWAY_TEAM",
            "HOME_GOALS",
            "AWAY_GOALS",
        ]

        num_duplicates = (
            origin_df
            .group_by(keys)
            .len()
            .select(
                (pl.col("len") - 1)
                .clip(lower_bound=0)
                .sum()
            )
            .item()
        )

        print(f"Duplicados encontrados: {num_duplicates}")

        keys = [
            "DATE",
            "HOME_TEAM",
            "AWAY_TEAM",
            "HOME_GOALS",
            "AWAY_GOALS",
        ]

        destiny_df = origin_df.unique(
            subset=keys,
            keep="first",
        )

        destiny_df.write_csv(destiny_file)

    def get_team_rating(self, team_name: str) -> int:
        """Get the rating of a team."""
        if team_name not in self._ratings_map:
            raise ValueError(f"Team {team_name} not found in Ratings")
        return self._ratings_map[team_name]

    def _get_avg_goals(self) -> float:
        """Get the average goals per match in the tournament."""
        total_goals = (
            self._matches_df["HOME_GOALS"].sum() + self._matches_df["AWAY_GOALS"].sum()
        )

        total_matches = len(self._matches_df)

        return total_goals / total_matches

    def get_team_matches(
        self,
        team_name: str,
        limit: int = 10,
    ) -> pl.DataFrame:
        """Retrieve the matches for a given team."""
        matches = self.matches.filter(
            (pl.col("HOME_TEAM") == team_name)
            | (pl.col("AWAY_TEAM") == team_name)
        )

        total_matches = (
            matches
            .sort("DATE", descending=True)
            .head(limit)
        )

        if len(total_matches) < limit:
            raise ValueError(
                f"{team_name} has only {len(total_matches)} matches, {limit} required"
            )

        return total_matches

    def _get_avg_tournament_rating(self):
        """Retrieve the average rating for the teams in the tournament."""
        ratings = [self.get_team_rating(team) for team in self._teams_df["Team"]]

        return sum(ratings) / len(ratings)
