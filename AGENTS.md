# World Cup Simulator - Project Documentation

## Project Description

A Monte Carlo simulation system for the FIFA World Cup that runs thousands of tournament simulations to generate statistical probabilities for team outcomes. The system models team performance using Elo ratings, historical match data, and a sophisticated expected goals (xG) model with multiple simulation model versions (v1, v2, v3).

**Key capabilities:**
- Simulates full tournaments from group stage through knockout rounds
- Runs 100,000+ simulations with buffered Parquet export
- Analyzes results with Polars for statistical distributions
- Visualizes outcomes (stage progression heatmaps, group vs championship probabilities)

## Architecture

The project follows a **layered architecture** (Clean Architecture inspired) with clear separation of concerns:

### Layers

```
app/
├── __main__.py                 # Entry point - orchestrates simulation + analysis
├── src/
│   ├── domain/                 # Core business logic (pure Python, no external deps)
│   │   ├── constants.py        # Tournament config, weights, enums
│   │   ├── simulation_model.py # Abstract base for simulation models
│   │   └── models/             # Pydantic domain models
│   ├── application/            # Use cases & business orchestration
│   │   ├── team_builder.py     # Builds Team aggregates from CSV data
│   │   ├── match_simulator.py  # Simulates individual matches (Poisson xG)
│   │   ├── tournament_simulator.py # Orchestrates full tournament flow
│   │   ├── simulator_exporter.py   # Buffered Parquet export
│   │   ├── parquet_analyzer.py     # Post-simulation statistical analysis
│   │   ├── simulation_visualizer.py # Matplotlib visualizations
│   │   └── simulation_models/      # Model implementations (v1, v2, v3)
│   └── infrastructure/         # External adapters
│       └── data_manager.py     # CSV/Polars data loading
```

### Data Flow

1. **CSVDataManager** loads teams, ratings, and historical matches from CSV
2. **TeamBuilder** constructs `Team` aggregates with 10-match history
3. **SimulationModel** (V3) computes team metrics (offensive/defensive ratings, form, performance)
4. **MatchSimulator** uses Poisson distribution on expected goals (xG)
5. **TournamentSimulator** runs group stage → round of 32 → knockout bracket
6. **ParquetSimulationResultExporter** buffers and writes results to partitioned Parquet
7. **ParquetAnalyzer** queries results with Polars LazyFrames for statistics
8. **SimulationVisualizer** generates charts

### Key Design Patterns

- **Strategy Pattern**: `SimulationModel` abstraction with V1/V2/V3 implementations
- **Builder Pattern**: `TeamBuilder` constructs complex `Team` aggregates
- **Repository Pattern**: `CSVDataManager` abstracts data access
- **Iterator Pattern**: `TournamentSimulator.run()` yields results lazily
- **Buffered Writer**: Exporter batches writes to avoid memory pressure

## Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| Language | Python | ≥3.12 |
| Data Processing | Polars | ≥1.41.2 |
| Numerical Computing | NumPy | ≥2.4.6 |
| Data Analysis | Pandas | ≥3.0.3 |
| Validation | Pydantic | ≥2.13.4 |
| Visualization | Matplotlib | ≥3.11.0 |
| Linting | Ruff | ≥0.15.16 |
| Package Manager | uv | (lock file) |

## Domain Models (Pydantic)

- **Team** - Core aggregate with rating, group, match history
- **HistoricalMatch** - Single match record with context (competition, stage, instance)
- **TeamMetrics** - Computed metrics (offensive/defensive rating, weighted form, performance score)
- **MatchResult** - Simulated match outcome with goals, winner, win method
- **SimulationResult** - Complete tournament record with all matches and team results
- **GroupStanding** - Group phase ranking (points, GD, GF)
- **TeamResult** - Per-team tournament statistics

## Simulation Model (V3)

The V3 model calculates expected goals (λ) using multiplicative factors:

```
λ = base_goals × attack_factor × (1/defense_factor) × elo_factor × form_factor × performance_factor
```

Where:
- **attack_factor** = (offensive_rating / avg_offensive)^0.8
- **defense_factor** = (avg_defensive / defensive_rating)^0.5
- **elo_factor** = (team_rating / avg_tournament_rating)^2.0
- **form_factor** = 0.9 + 0.2 × weighted_form
- **performance_factor** = 1 + 0.05 × performance_score

Match weights incorporate: competition importance, tournament stage, win method, and recency.

## Running the Project

```bash
# Run simulations (100k tournaments)
uv run python -m app

# The main() function runs analysis on existing results by default
# Uncomment run_n_simulations() in __main__.py to generate new data
```

## Output Structure

```
results/
├── simulations/   # Parquet: simulation_id, champion
├── matches/       # Parquet: all matches with stage, goals, winner
├── statistics/    # Parquet: per-team per-simulation stats
└── graphs/        # PNG visualizations
```

## Configuration Constants

Key tunables in `app/src/domain/constants.py`:
- `GROUPS_QUALIFIERS` - Teams advancing per group (2 or 3)
- `ROUND_OF_32` - Fixed bracket pairings
- `COMPETITION_WEIGHTS` - Match importance by competition type
- `STAGE_WEIGHTS` - Match importance by tournament stage
- `INSTANCE_WEIGHTS` - Win method weighting (full-time > ET > penalties)
- `MAX_ELO` - 2200 (normalization ceiling)
- `NORMALIZED_GOAL_AVG` - 3 goals/match baseline