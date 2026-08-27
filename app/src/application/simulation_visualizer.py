import polars as pl
import matplotlib.pyplot as plt
from pathlib import Path


class SimulationVisualizer:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def stage_heatmap(
            self,
            df: pl.DataFrame,
    ):
        teams = df["team"].to_list()

        stages = [
            column
            for column in df.columns
            if column != "team"
        ]

        matrix = (
            df
            .select(stages)
            .to_numpy()
        )

        matrix = matrix * 100 / matrix.sum(axis=1, keepdims=True)

        fig, ax = plt.subplots(figsize=(6, 10))

        # Plot the heatmap
        im = ax.imshow(matrix, aspect="auto", cmap="RdBu")

        # Create colorbar
        cbar_kw = {}

        cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
        cbar.ax.set_ylabel("Simulations", rotation=-90, va="bottom")

        # Show all ticks and label them with the respective list entries.
        ax.set_xticks(range(len(stages)))
        ax.set_xticklabels(stages, rotation=45, ha="right")
        ax.tick_params(
            axis="x",
            pad=10,
        )

        ax.set_yticks(range(len(teams)))
        ax.set_yticklabels(teams)


        ax.set_title(
            "Tournament Stage Distribution"
        )
        plt.tight_layout()
        plt.savefig(Path.joinpath(self._output_dir, "heatmap"), dpi=300)
        plt.close(fig)

    def group_vs_championship_probability(self, df: pl.DataFrame):
        fig, ax = plt.subplots(figsize=(6, 10))

        x = df["group_stage_pct"]
        y = df["champion_pct"]

        ax.scatter(x, y)

        for row in df.iter_rows(named=True):
            ax.text(
                row["group_stage_pct"],
                row["champion_pct"],
                row["team"],
                fontsize=8,
            )

        ax.axvline(
            df["group_stage_pct"].mean(),
            linestyle="--",
            alpha=0.5,
        )

        ax.axhline(
            df["champion_pct"].mean(),
            linestyle="--",
            alpha=0.5,
        )


        plt.tight_layout()
        plt.savefig(Path.joinpath(self._output_dir, "scatter"), dpi=300)
        plt.close(fig)

    def group_vs_championship_rating(self, df: pl.DataFrame):
        ratings = df["rating"]

        normalized = (
                (ratings - ratings.min())
                / (ratings.max() - ratings.min())
        )
        sizes = 20 + normalized * 1500

        fig, ax = plt.subplots(figsize=(6, 10))

        x = df["group_stage_pct"]
        y = df["champion_pct"]
        s = sizes
        ax.scatter(x=x, y=y, s=s, alpha=0.6)
        for row, size in zip(df.iter_rows(named=True), sizes):
            offset = size ** 0.5 / 2

            ax.annotate(
                row["team"],
                (row["group_stage_pct"], row["champion_pct"]),
                xytext=(offset, offset),
                textcoords="offset points",
                fontsize=8,
            )

        plt.tight_layout()
        plt.savefig(Path.joinpath(self._output_dir, "bubble"), dpi=300)
        plt.close(fig)
