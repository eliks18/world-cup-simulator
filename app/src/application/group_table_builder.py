import polars as pl

from app.src.domain.models.group_standing import GroupStanding


class GroupTableBuilder:
    def __init__(self, teams_df):
        self._teams_df = teams_df

    def build(
            self,
            matches: pl.DataFrame,
            group: str | None = None,
    ) -> pl.DataFrame:
        df = self._normalize_matches(matches)
        df = self._aggregate_team_stats(df)
        df = self._calculate_points(df)
        df = self._calculate_goal_difference(df)
        df = self._aggregate_standings(df)
        df = self._join_with_group(df, group)
        return df

    def _normalize_matches(self, matches: pl.DataFrame) -> pl.DataFrame:
        home = matches.select(
            pl.col("home").alias("team"),
            pl.col("away").alias("opponent"),
            pl.col("home_goals").alias("goals_for"),
            pl.col("away_goals").alias("goals_against"),
        )

        away = matches.select(
            pl.col("away").alias("team"),
            pl.col("home").alias("opponent"),
            pl.col("away_goals").alias("goals_for"),
            pl.col("home_goals").alias("goals_against"),
        )

        normalized = pl.concat([home, away])
        return normalized

    def _aggregate_team_stats(self, normalized_matches: pl.DataFrame):
        normalized_with_stats = normalized_matches.with_columns(
            played=pl.lit(1),
            wins=(pl.col("goals_for") > pl.col("goals_against")).cast(pl.Int8),
            draws=(pl.col("goals_for") == pl.col("goals_against")).cast(pl.Int8),
            losses=(pl.col("goals_for") < pl.col("goals_against")).cast(pl.Int8),
        )
        return normalized_with_stats

    def _calculate_points(self, normalized_matches: pl.DataFrame):
        normalized_with_points = normalized_matches.with_columns(
            points=
                pl.col("wins") * 3 +
                pl.col("draws")
        )
        return normalized_with_points

    def _aggregate_standings(self, normalized_matches: pl.DataFrame):
        standings = (
            normalized_matches
            .group_by("team")
            .agg(
                pl.sum("played"),
                pl.sum("wins"),
                pl.sum("draws"),
                pl.sum("losses"),
                pl.sum("goals_for"),
                pl.sum("goals_against"),
                pl.sum("goal_difference"),
                pl.sum("points"),
            )
        )
        return standings

    def _join_with_group(self, normalized_matches: pl.DataFrame, group: str | None = None) -> pl.DataFrame:
        joined_matches = normalized_matches.join(
            self._teams_df.select(["Team", "Group"]),
            left_on="team",
            right_on="Team",
        )
        if group:
              joined_matches = joined_matches.filter(pl.col("Group") == group)
        joined_matches = joined_matches.sort(
            by=["Group", "points", "goal_difference", "goals_for"],
            descending=True,
        )
        return joined_matches

    def _calculate_goal_difference(
            self,
            normalized_match: pl.DataFrame,
    ) -> pl.DataFrame:
        return normalized_match.with_columns(
            (
                    pl.col("goals_for") - pl.col("goals_against")
            ).alias("goal_difference")
        )
