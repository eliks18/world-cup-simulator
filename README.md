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
