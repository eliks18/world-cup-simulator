"""Parquet Analyzer module."""

from pathlib import Path
import polars as pl
from polars import DataFrame

from app.src.domain.constants import TournamentStage, WinMethod

stage_order = [
    "Group Stage",
    "Round of 32",
    "Round of 16",
    "Quarter-final",
    "Semi-final",
    "Final",
]


class ParquetAnalyzer:
    """Parquet Analyzer class."""

    def __init__(self, matches_dir: Path, simulations_dir: Path, stats_dir: Path, ratings_file: Path) -> None:
        """Parquet Analyzer constructor."""
        self._matches_dir = matches_dir
        self._simulations_dir = simulations_dir
        self._ratings_file = ratings_file
        self._stats_dir = stats_dir
        self._all_matches = self._load_dataset(self._matches_dir)
        self._simulations = self._load_dataset(self._simulations_dir)
        self._statistics = self._load_dataset(self._stats_dir)
        self._ratings = pl.read_csv(self._ratings_file)
        self._knockout_matches = self._knockout_matches()
        self._group_matches = self._group_matches()

    @property
    def knockout_matches(self) -> pl.DataFrame:
        """Return the corresponding matches to Knockout Stage."""
        return self._knockout_matches.collect()

    @property
    def group_matches(self) -> pl.DataFrame:
        """Return the corresponding matches to Group Stage."""
        return self._group_matches.collect()

    def _filter_matches(
        self,
        stage: TournamentStage = None,
        win_method: WinMethod = None,
        team: str = None,
        simulation_id: str = None,
    ) -> pl.LazyFrame:
        """Filter the matches LazyFrame using different filter types."""
        query = self._all_matches
        if stage:
            query = query.filter(pl.col("stage") == stage.value)
        if win_method:
            query = query.filter(pl.col("win_method") == win_method.value)
        if simulation_id:
            query = query.filter(pl.col("simulation_id") == simulation_id)
        if team:
            query = query.filter((pl.col("home") == team) | (pl.col("away") == team))

        return query

    @staticmethod
    def _load_dataset(directory:Path) -> pl.LazyFrame:
        """Load a LazyFrame from a given directory."""
        return pl.scan_parquet(directory / "*.parquet")

    def _knockout_matches(self) -> pl.LazyFrame:
        """Filter the matches LazyFrame by Knockout Stage."""
        return self._all_matches.filter(pl.col("stage") != "Group Stage")

    def _group_matches(self) -> pl.LazyFrame:
        """Filter the matches LazyFrame by Group Stage."""
        return self._all_matches.filter(pl.col("stage") == "Group Stage")

    def match_count_by_stage(self) -> pl.DataFrame:
        """Return a DataFrame of matches count by stage."""
        return (
            self._all_matches.group_by("stage")
            .len()
            .sort("len", descending=True)
            .collect()
        )

    def team_matches(
        self,
        team: str,
        stage: TournamentStage | None = None,
        simulation_id: str | None = None,
    ) -> pl.DataFrame:
        """Return a filtered DataFrame of matches for a team."""
        return self._filter_matches(
            team=team,
            stage=stage,
            simulation_id=simulation_id,
        ).collect()

    def simulation_group_matches(self, simulation_id: str) -> pl.DataFrame:
        """Return a DataFrame of group matches for a simulation id."""
        return self._filter_matches(
            simulation_id=simulation_id,
            stage=TournamentStage.FINAL
        ).collect()

    def champion_distribution(self) -> pl.DataFrame:
        """Return a DataFrame of champion teams distribution."""
        return (
            self._simulations.group_by("champion")
            .len()
            .sort("len", descending=True)
            .collect()
        )

    def team_stats(self, team_name: str) -> pl.DataFrame:
        """Return a DataFrame of team stats for a team."""
        return (
            self._statistics
            .filter(pl.col("team") == team_name)
#            .filter(pl.col("champion"))
            .collect()
        )

    def team_stage_distribution(self, team_name: str) -> pl.DataFrame:
        return (
            self._statistics
            .filter(pl.col("team") == team_name)
            .group_by(pl.col("stage"))
            .len()
            .sort("len", descending=True)
            .collect()
        )

    def team_eliminated_by_distribution(self, team_name: str) -> pl.DataFrame:
        return (
            self._statistics
            .filter(pl.col("team") == team_name)
            .group_by(pl.col("eliminated_by"))
            .len()
            .sort("len", descending=True)
            .collect()
        )

    def championship_probability(self, team_name: str) -> pl.DataFrame:
        return (
            self._statistics
            .filter(pl.col("team") == team_name)
            .group_by(pl.col("champion"))
            .len()
            .sort("len", descending=True)
            .collect()
            .with_columns(
                (pl.col("len") / pl.col("len").sum() * 100)
                .round(2)
                .alias("pct")
            )
        )

    def stage_distribution_matrix(self) -> pl.DataFrame:
        df = (
            self._statistics
            .group_by(["team", "stage"])
            .len()
            .sort("team")
            .collect()
        )
        df = df.pivot(
            on="stage",
            index="team",
            values="len",
            aggregate_function="sum",
        )
        df = df.select(
            "team",
            *stage_order,
        )
        return df

    def group_vs_championship_probability(self) -> pl.DataFrame:
        return (
            self._statistics
            .group_by("team")
            .agg(
                (
                    (pl.col("stage") == TournamentStage.GROUP_STAGE.value)
                    .mean()
                    * 100
                ).alias("group_stage_pct"),

                (
                    pl.col("champion")
                    .mean()
                    * 100
                ).alias("champion_pct"),
            )
            .collect()
        )

    def group_vs_championship_rating(self) -> tuple[pl.DataFrame]:
        probabilities = (
            self._statistics
            .group_by("team")
            .agg(
                (
                        (pl.col("stage") == TournamentStage.GROUP_STAGE.value)
                        .mean() * 100
                ).alias("group_stage_pct"),

                (
                        pl.col("champion")
                        .mean() * 100
                ).alias("champion_pct"),
            )
        )
        ratings = self._ratings.rename({"Team": "team", "Rating": "rating"})

        return (
            probabilities
            .join(ratings.lazy(), on="team")
            .collect()
        )

    def find_champion_roadmap(self) -> tuple[DataFrame, DataFrame]:
        matches_filter = self._all_matches.with_columns(
            pl.concat_list("home", "away").alias("teams")
        )

        matches = matches_filter.filter(
            pl.col("teams").list.contains("Spain")
            & pl.col("teams").list.contains("Argentina")
        ).drop("teams").collect()

        finals = matches.filter(pl.col("stage") == "Final")

        simulation_ids = finals.get_column("simulation_id").unique()

        semifinals = (
            matches_filter.filter(
                pl.col("simulation_id").is_in(simulation_ids)
                & (pl.col("stage") == "Semi-final")
                & (
                    (
                        pl.col("teams").list.contains("Spain")
                        & pl.col("teams").list.contains("France")
                    )
                    | (
                        pl.col("teams").list.contains("Argentina")
                        & pl.col("teams").list.contains("England")
                    )
                )
            )
            .drop("teams")
            .collect()
        )

        return (
            finals.group_by("winner", "win_method").len(),
            semifinals.group_by("winner", "win_method").len()
        )
