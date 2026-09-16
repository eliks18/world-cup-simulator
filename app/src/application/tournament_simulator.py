"""Tournament Simulator module."""

from collections import defaultdict
from itertools import combinations
from collections.abc import Iterator

import numpy as np
import random

from app.src.application.match_simulator import MatchSimulator
from app.src.application.rng import RandomProvider
from app.src.domain.models.simulation_results import SimulationResult
from app.src.domain.constants import (
    N_SIMULATIONS,
    TournamentStage,
    NEXT_STAGE,
    ROUND_OF_32,
    THIRD_PLACE_ASSIGNMENT_ORDER,
    THIRD_PLACE_COMBINATIONS,
)
from app.src.domain.models.group_standing import GroupStanding
from app.src.domain.models.team import Team
from app.src.domain.simulation_model import SimulationModel


class TournamentSimulator:
    """Tournament Simulator class."""

    def __init__(self, model: SimulationModel, teams: list[Team]):
        """Tournament Simulator constructor."""
        self.match_simulator: MatchSimulator = MatchSimulator(model=model)
        self.teams: list[Team] = teams

    def run(self, n: int = N_SIMULATIONS, seed: int | None = None) -> Iterator[SimulationResult]:
        """Run the Tournament Simulation for n times."""
        if seed is None:
            rng = RandomProvider(np.random.default_rng(), random.Random())
        else:
            rng = RandomProvider(np.random.default_rng(seed), random.Random(seed))
        self.match_simulator.rng = rng

        for simulation_id in range(n):
            simulation_result = self.simulate_tournament()
            print(f"🏆 Champion: {simulation_result.champion.team.name}")
            yield simulation_result

    def simulate_tournament(self) -> SimulationResult:
        """Executes a tournamenr simulation from groups to knockout phases."""
        simulation_record = SimulationResult()
        simulation_record.from_teams(self.teams)

        qualified = self.simulate_groups(simulation_record)

        positions = self.build_qualified_positions(qualified)
        round_of_32 = self.build_round(positions)

        round_of_16_winners = self.play_knockout_round(
            round_of_32, simulation_record, TournamentStage.ROUND_OF_32
        )
        champion = self.simulate_knockout_stage(
            round_of_16_winners, simulation_record, TournamentStage.ROUND_OF_16
        )

        simulation_record.finish(champion)

        return simulation_record

    def simulate_group(
        self,
        teams: list[Team],
        simulation_record: SimulationResult,
    ):
        """Executes a simulation of matches for teams in a group."""
        standings = {team.name: GroupStanding(team=team) for team in teams}

        for team_a, team_b in combinations(
            teams,
            2,
        ):
            match = self.match_simulator.simulate_match(
                stage=TournamentStage.GROUP_STAGE,
                team_a=team_a,
                team_b=team_b,
                is_knockout=False,
            )
            simulation_record.record_match(match, TournamentStage.GROUP_STAGE)

            standing_a = standings[team_a.name]
            standing_b = standings[team_b.name]

            standing_a.goals_for += match.goals_a
            standing_a.goals_against += match.goals_b

            standing_b.goals_for += match.goals_b
            standing_b.goals_against += match.goals_a

            if match.goals_a > match.goals_b:
                standing_a.points += 3

            elif match.goals_b > match.goals_a:
                standing_b.points += 3

            else:
                standing_a.points += 1
                standing_b.points += 1

        return sorted(
            standings.values(),
            key=lambda s: (
                s.points,
                s.goal_difference,
                s.goals_for,
            ),
            reverse=True,
        )

    @staticmethod
    def select_best_third_places(
        standings: list[GroupStanding],
    ) -> list[GroupStanding]:
        """Select the 8 best third-place teams across all groups."""
        groups = defaultdict(list)

        for standing in standings:
            groups[standing.team.group].append(standing)

        third_places = []

        for group_standings in groups.values():
            sorted_standings = sorted(
                group_standings,
                key=lambda s: (
                    s.points,
                    s.goal_difference,
                    s.goals_for,
                ),
                reverse=True,
            )

            if len(sorted_standings) >= 3:
                third_places.append(sorted_standings[2])

        return sorted(
            third_places,
            key=lambda s: (
                s.points,
                s.goal_difference,
                s.goals_for,
            ),
            reverse=True,
        )[:8]

    def simulate_groups(
        self,
        simulation_record: SimulationResult,
    ) -> dict[str, list[GroupStanding]]:
        """Executes a simulation of matches for all groups."""
        groups = self.build_groups(self.teams)

        qualified = {}
        all_standings = []

        for group_name, group_teams in groups.items():
            standings = self.simulate_group(group_teams, simulation_record)
            all_standings.extend(standings)

            qualified[group_name] = standings[:2]

        for third_place in self.select_best_third_places(all_standings):
            qualified[third_place.team.group].append(third_place)

        self._eliminate_group_stage_teams(
            simulation_record,
            qualified,
        )

        return qualified

    def play_knockout_round(
        self,
        matches: list[tuple[Team, Team]],
        simulation_record: SimulationResult,
        stage: TournamentStage,
    ) -> list[Team]:
        """Play knockout round."""
        winners = []

        for team_a, team_b in matches:
            match = self.match_simulator.simulate_match(
                stage=stage,
                team_a=team_a,
                team_b=team_b,
            )

            simulation_record.record_match(match, stage=stage)

            winners.append(match.winner)

            loser = team_b if match.winner == team_a else team_a
            simulation_record.eliminate(loser, stage, match.winner)

        return winners

    @staticmethod
    def build_next_round(
        teams: list[Team],
    ) -> list[tuple[Team, Team]]:
        """Build next round team matches."""
        matches = []

        for i in range(
            0,
            len(teams),
            2,
        ):
            matches.append(
                (
                    teams[i],
                    teams[i + 1],
                )
            )

        return matches

    def simulate_knockout_stage(
        self,
        teams: list[Team],
        simulation_record: SimulationResult,
        stage: TournamentStage,
    ) -> Team:
        """Executes a simulation knockout stage."""
        current_round = teams

        while len(current_round) > 1:
            matches = self.build_next_round(current_round)

            current_round = self.play_knockout_round(matches, simulation_record, stage)

            if len(current_round) > 1:
                stage = NEXT_STAGE[stage]

        return current_round[0]

    @staticmethod
    def build_groups(
        teams: list[Team],
    ) -> dict[str, list[Team]]:
        """Build groups of teams."""
        groups = defaultdict(list)

        for team in teams:
            groups[team.group].append(team)

        return groups

    @staticmethod
    def build_qualified_positions(
        qualified: dict[str, list[GroupStanding]],
    ) -> dict[str, Team]:
        """Build team positions for each group."""
        positions = {}

        for group_name, standings in qualified.items():
            for position, standing in enumerate(
                standings,
                start=1,
            ):
                key = f"{position}{group_name}"

                positions[key] = standing.team

        return positions

    @staticmethod
    def build_round(qualified: dict[str, Team]) -> list[tuple[Team, Team]]:
        """Build round of matches."""
        matches = []
        third_place_opponents = TournamentSimulator.build_third_place_opponents(
            qualified,
        )

        for left, right in ROUND_OF_32:
            if right.startswith("3:"):
                right = third_place_opponents[right.removeprefix("3:")]

            matches.append(
                (
                    qualified[left],
                    qualified[right],
                )
            )

        return matches

    @staticmethod
    def build_third_place_opponents(qualified: dict[str, Team]) -> dict[str, str]:
        """Build third-place opponent slots from the FIFA 2026 matrix."""
        third_place_groups = sorted(
            position[1]
            for position in qualified
            if position.startswith("3")
        )
        combination_key = "".join(third_place_groups)

        if combination_key not in THIRD_PLACE_COMBINATIONS:
            raise ValueError(
                f"Invalid third-place combination: {combination_key}"
            )

        return dict(
            zip(
                THIRD_PLACE_ASSIGNMENT_ORDER,
                THIRD_PLACE_COMBINATIONS[combination_key],
                strict=True,
            )
        )

    def _eliminate_group_stage_teams(self, simulation_record: SimulationResult, qualified: dict):
        qualified_names = {
            team.team.name
            for teams in qualified.values()
            for team in teams
        }

        for team in self.teams:
            if team.name not in qualified_names:
                simulation_record.eliminate(
                    team,
                    TournamentStage.GROUP_STAGE,
                )
