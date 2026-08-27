"""Parquet Simulator Exporter module."""

from pathlib import Path
from typing import Any

import polars as pl

from app.src.domain.models.simulation_results import SimulationResult


class ParquetSimulationResultExporter:
    """Parquet Simulation Result Exporter class."""

    def __init__(self, output_dir: Path, buffer_size: int = 20000):
        """ParquetSimulationResultExporter constructor."""
        self._output_dir = output_dir
        self._simulations_dir = output_dir / "simulations"
        self._matches_dir = output_dir / "matches"
        self._statistics_dir = output_dir / "statistics"
        self._buffer_size = buffer_size
        self._simulation_rows: list[dict] = []
        self._match_rows: list[dict] = []
        self._statistics_rows: list[dict] = []
        self._part_number = 0

    @staticmethod
    def _build_simulation_row(simulation_result: SimulationResult) -> dict[str, Any]:
        """Build simulation row."""
        return {
            "simulation_id": simulation_result.uuid_as_str,
            "champion": simulation_result.champion.team.name,
        }

    @staticmethod
    def _build_match_rows(simulation_result: SimulationResult) -> list[dict[str, Any]]:
        """Build match row."""
        rows = []

        for match in simulation_result.matches:
            rows.append(
                {
                    "simulation_id": simulation_result.uuid_as_str,
                    "stage": match.stage,
                    "home": match.team_a.name,
                    "away": match.team_b.name,
                    "home_goals": match.goals_a,
                    "away_goals": match.goals_b,
                    "winner": match.winner.name if match.winner else None,
                    "win_method": match.win_method,
                }
            )

        return rows

    @staticmethod
    def _build_statistics_rows(simulation_result: SimulationResult) -> list[dict[str, Any]]:
        """Build statistics row."""
        rows = []
        for team_result in simulation_result.team_results.values():
            row = {
                "simulation_id": simulation_result.uuid_as_str,
                "team": team_result.team.name,
                "stage": team_result.stage,
                "wins": team_result.wins,
                "draws": team_result.draws,
                "losses": team_result.losses,
                "matches_played": team_result.matches_played,
                "goals_for": team_result.goals_for,
                "goals_against": team_result.goals_against,
                "goal_difference": team_result.goal_difference,
                "champion": team_result.champion,
                "eliminated_by": team_result.eliminated_by,
                "win_rate": team_result.win_rate,
            }
            rows.append(row)
        return rows

    def _write_simulations(self) -> None:
        """Write simulation rows."""
        if not self._simulation_rows:
            return

        df = pl.DataFrame(self._simulation_rows)

        df.write_parquet(
            self._simulations_dir / f"part_{self._part_number:04d}.parquet"
        )

    def _write_matches(self) -> None:
        """Write match rows."""
        if not self._match_rows:
            return

        df = pl.DataFrame(self._match_rows)

        df.write_parquet(self._matches_dir / f"part_{self._part_number:04d}.parquet")

    def _write_statistics(self) -> None:
        """Write statistics rows."""
        if not self._statistics_rows:
            return

        df = pl.DataFrame(self._statistics_rows)
        df.write_parquet(
            self._statistics_dir / f"part_{self._part_number:04d}.parquet"
        )

    def _clear_buffers(self) -> None:
        """Clear Simulation and Match buffers."""
        self._simulation_rows.clear()
        self._match_rows.clear()
        self._statistics_rows.clear()

    def append(self, simulation_result: SimulationResult) -> None:
        """Append simulation and match rows into buffers."""
        self._simulation_rows.append(self._build_simulation_row(simulation_result))

        self._match_rows.extend(self._build_match_rows(simulation_result))

        self._statistics_rows.extend(self._build_statistics_rows(simulation_result))

        if len(self._simulation_rows) >= self._buffer_size:
            self.flush()

    def flush(self):
        """Check file part, write buffers into files and flush buffers."""
        self._part_number += 1
        self._write_simulations()
        self._write_matches()
        self._write_statistics()
        self._clear_buffers()
