from pathlib import Path

from app.src.application.parquet_analyzer import ParquetAnalyzer
from app.src.application.simulation_models.v3 import V3Model
from app.src.application.simulation_visualizer import SimulationVisualizer
from app.src.application.simulator_exporter import ParquetSimulationResultExporter
from app.src.application.team_builder import TeamBuilder
from app.src.application.tournament_simulator import TournamentSimulator
from app.src.infrastructure.data_manager import CSVDataManager


def run_n_simulations():
    data_manager = CSVDataManager(
        teams_csv="teams.csv", ratings_csv="ratings.csv", matches_csv="matches.csv"
    )
    team_builder = TeamBuilder(csv_data_manager=data_manager)
    teams = team_builder.build_teams()

    model_v3 = V3Model(
        teams=teams,
        average_goals=data_manager.average_goals,
        average_global_rating=data_manager.average_global_rating,
        average_tournament_rating=data_manager.average_tournament_rating,
    )

    tournament_simulator = TournamentSimulator(model=model_v3, teams=teams)
    exporter = ParquetSimulationResultExporter(Path("results/"))

    for simulation_result in tournament_simulator.run(100000):
        exporter.append(simulation_result)

    exporter.flush()


def main():
#    run_n_simulations()

    parquet_analyzer = ParquetAnalyzer(
        simulations_dir=Path("results/simulations"),
        matches_dir=Path("results/matches"),
        stats_dir=Path("results/statistics"),
        ratings_file=Path("ratings.csv"),
    )
    finals, semifinals = parquet_analyzer.find_champion_roadmap()
    breakpoint()
    exit()
    simulation_visualizer = SimulationVisualizer(Path("results/graphs"))
    df_stage_distribution_matrix = parquet_analyzer.stage_distribution_matrix()
    df_group_vs_championship = parquet_analyzer.group_vs_championship_probability()
    df_group_vs_championship_rating = parquet_analyzer.group_vs_championship_rating()

    simulation_visualizer.stage_heatmap(df_stage_distribution_matrix)
    simulation_visualizer.group_vs_championship_probability(df_group_vs_championship)
    simulation_visualizer.group_vs_championship_rating(df_group_vs_championship_rating)


if __name__ == "__main__":
    main()
