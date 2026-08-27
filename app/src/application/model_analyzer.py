"""Model analyzer module."""

from app.src.application.match_simulator import MatchSimulator
from app.src.application.simulation_models.v1 import V1Model
from app.src.application.simulation_models.v2 import V2Model
from app.src.application.simulation_models.v3 import V3Model
from app.src.domain.constants import ModelMetrics, AnalyzerMetric, WinMethod
from app.src.domain.models.metrics_config import MetricsConfig
from app.src.domain.models.team import Team
from app.src.domain.simulation_model import BaseSimulationModel
from app.src.infrastructure.data_manager import CSVDataManager


class ModelAnalyzer:
    """Model analyzer class."""

    def __init__(
        self,
        teams: list[Team],
        data_manager: CSVDataManager,
    ):
        """Model analyzer constructor."""
        self.teams: list[Team] = teams
        self.data_manager: CSVDataManager = data_manager
        self.models: dict[str, BaseSimulationModel] = self._build_model_mapping()
        self.metric_mappings = self._set_metric_mappings()

    def _build_model_mapping(self):
        v1_model = V1Model(teams=self.teams)
        v2_model = V2Model(
            teams=self.teams,
            average_goals=self.data_manager.average_goals,
            average_global_rating=self.data_manager.average_global_rating,
            average_tournament_rating=self.data_manager.average_tournament_rating,
        )
        v3_model = V3Model(
            teams=self.teams,
            average_goals=self.data_manager.average_goals,
            average_global_rating=self.data_manager.average_global_rating,
            average_tournament_rating=self.data_manager.average_tournament_rating,
        )

        return {
            "V1": v1_model,
            "V2": v2_model,
            "V3": v3_model,
        }

    def _set_metric_mappings(self):
        return {
            AnalyzerMetric.top_attack.value: MetricsConfig(
                metric_getter=self.attack,
                metric_name=ModelMetrics.offensive_rating,
                reverse=True,
            ),
            AnalyzerMetric.worst_attack.value: MetricsConfig(
                metric_getter=self.attack,
                metric_name=ModelMetrics.offensive_rating,
                reverse=False,
            ),
            AnalyzerMetric.top_defense.value: MetricsConfig(
                metric_getter=self.defense,
                metric_name=ModelMetrics.defensive_rating,
                reverse=False,
            ),
            AnalyzerMetric.worst_defense.value: MetricsConfig(
                metric_getter=self.defense,
                metric_name=ModelMetrics.defensive_rating,
                reverse=True,
            ),
            AnalyzerMetric.top_form.value: MetricsConfig(
                metric_getter=self.form,
                metric_name=ModelMetrics.weighted_form,
                reverse=True,
            ),
            AnalyzerMetric.worst_form.value: MetricsConfig(
                metric_getter=self.form,
                metric_name=ModelMetrics.weighted_form,
                reverse=False,
            ),
            AnalyzerMetric.top_performance.value: MetricsConfig(
                metric_getter=self.performance,
                metric_name=ModelMetrics.performance_score,
                reverse=True,
            ),
            AnalyzerMetric.worst_performance.value: MetricsConfig(
                metric_getter=self.performance,
                metric_name=ModelMetrics.performance_score,
                reverse=False,
            ),
        }

    def compare_metric(
        self,
        metric_name: AnalyzerMetric,
        limit: int = 10,
    ):
        """Compare specific metric beween models."""
        model_metrics = []

        for model_name, model in self.models.items():
            metric = self.metric_mappings[metric_name.value].metric_getter(
                self.teams,
                model,
                self.metric_mappings[metric_name.value].reverse,
                limit,
            )

            model_metrics.append((model_name, metric))

        print(f"{'#':<4}{'V1':<30}{'V2':<30}{'V3':<30}")
        for i in range(limit):
            v1_team = model_metrics[0][1][i]
            v2_team = model_metrics[1][1][i]
            v3_team = model_metrics[2][1][i]

            v1_metric = getattr(
                self.models["V1"].get_team_metrics(v1_team),
                self.metric_mappings[metric_name.value].metric_name,
                self.metric_mappings[metric_name.value].reverse,
            )
            v2_metric = getattr(
                self.models["V2"].get_team_metrics(v2_team),
                self.metric_mappings[metric_name.value].metric_name,
                self.metric_mappings[metric_name.value].reverse,
            )
            v3_metric = getattr(
                self.models["V3"].get_team_metrics(v3_team),
                self.metric_mappings[metric_name.value].metric_name,
                self.metric_mappings[metric_name.value].reverse,
            )

            print(
                f"{i + 1:<3}"
                f"{v1_team.name[:15]:<18}"
                f"{v1_metric:<12.3f}"
                f"{v2_team.name[:15]:<18}"
                f"{v2_metric:<12.3f}"
                f"{v3_team.name[:15]:<18}"
                f"{v3_metric:<12.3f}"
            )

    def compare_team(
        self,
        team_name: str,
    ) -> None:
        """Compare a team metrics between models."""
        team = next(t for t in self.teams if t.name == team_name)

        print()
        print(team.name)
        print("-" * 60)

        header = f"{'Metric':<15}"

        for model_name in self.models:
            header += f"{model_name:<12}"

        print(header)

        metrics = [
            ("Attack", "offensive_rating"),
            ("Defense", "defensive_rating"),
            ("Form", "weighted_form"),
            ("Performance", "performance_score"),
        ]

        for label, attribute in metrics:
            row = f"{label:<15}"

            for model in self.models.values():
                value = getattr(
                    model.get_team_metrics(team),
                    attribute,
                )

                row += f"{value:<12.3f}"

            print(row)

    def run_match(self, team_a: str, team_b: str, model_name: str):
        """Run match between teams."""
        team_a = next(t for t in self.teams if t.name == team_a)
        team_b = next(t for t in self.teams if t.name == team_b)
        model = self.models[model_name]
        match_simulator = MatchSimulator(model=model)
        match_result = match_simulator.simulate_match(team_a, team_b)

        print(
            f"{match_result.team_a.name} {match_result.goals_a} - {match_result.goals_b} {match_result.team_b.name}"
        )
        instance = (
            WinMethod.PENALTIES.value
            if match_result.went_to_penalties
            else WinMethod.EXTRA_TIME.value
            if match_result.went_to_extra_time
            else WinMethod.FULL_TIME.value
        )
        print(f"Winner team: {match_result.winner.name} in {instance}")

    def run_expected_goals(self, team_a: str, team_b: str, model_name: str):
        """Run the expected goals between two teams."""
        team_a = next(t for t in self.teams if t.name == team_a)
        team_b = next(t for t in self.teams if t.name == team_b)
        model = self.models[model_name]
        xg_a, xg_b = model.expected_goals(team_a, team_b)
        print(f"{model_name}: {team_a.name} {xg_a} - {xg_b} {team_b.name}")
        self.compare_team(team_a.name)
        self.compare_team(team_b.name)

    @staticmethod
    def performance(
        teams: list[Team],
        model: BaseSimulationModel,
        reverse: bool = False,
        limit: int = 10,
    ):
        """Return the top performance teams for a given model."""
        ranked = sorted(
            teams,
            key=lambda t: model.get_team_metrics(t).performance_score,
            reverse=reverse,
        )

        return ranked[:limit]

    @staticmethod
    def attack(
        teams: list[Team],
        model: BaseSimulationModel,
        reverse: bool = False,
        limit: int = 10,
    ):
        """Return the top attack teams for a given model."""
        ranked = sorted(
            teams,
            key=lambda t: model.get_team_metrics(t).offensive_rating,
            reverse=reverse,
        )

        return ranked[:limit]

    @staticmethod
    def defense(
        teams: list[Team],
        model: BaseSimulationModel,
        reverse: bool = False,
        limit: int = 10,
    ):
        """Return the top defense teams for a given model."""
        ranked = sorted(
            teams,
            key=lambda t: model.get_team_metrics(t).defensive_rating,
            reverse=reverse,
        )

        return ranked[:limit]

    @staticmethod
    def form(
        teams: list[Team],
        model: BaseSimulationModel,
        reverse: bool = False,
        limit: int = 10,
    ):
        """Return the top form teams for a given model."""
        ranked = sorted(
            teams,
            key=lambda t: model.get_team_metrics(t).weighted_form,
            reverse=reverse,
        )

        return ranked[:limit]
