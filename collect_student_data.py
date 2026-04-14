#!/usr/bin/env python3
"""
Student Data Collection Script for AOA Project Round 2

Usage:
    python3 collect_student_data.py --student "Your Name" --config-id 1

This script runs experiments with predefined parameter configurations and generates
the required student_name_data.csv and analysis materials.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df, plot_results


# Predefined parameter configurations for different group members
PARAMETER_CONFIGS = {
    1: {
        "name": "Fast Exploration (High Mutation)",
        "max_generations": 8,
        "population_size": 6,
        "top_k": 2,
        "mutation_rate": 0.6,
        "description": "High mutation rate for aggressive exploration with smaller population"
    },
    2: {
        "name": "Balanced Standard",
        "max_generations": 10,
        "population_size": 8,
        "top_k": 3,
        "mutation_rate": 0.35,
        "description": "Default balanced configuration for steady evolution"
    },
    3: {
        "name": "Conservative (Low Mutation)",
        "max_generations": 12,
        "population_size": 10,
        "top_k": 4,
        "mutation_rate": 0.2,
        "description": "Low mutation rate with larger population for careful refinement"
    },
    4: {
        "name": "Elite-Focused",
        "max_generations": 10,
        "population_size": 12,
        "top_k": 6,
        "mutation_rate": 0.3,
        "description": "Large elite selection to preserve good solutions"
    },
    5: {
        "name": "Rapid Evolution (Few Generations)",
        "max_generations": 5,
        "population_size": 10,
        "top_k": 3,
        "mutation_rate": 0.5,
        "description": "Quick evolution with moderate parameters"
    },
    6: {
        "name": "Deep Search (Many Generations)",
        "max_generations": 15,
        "population_size": 8,
        "top_k": 3,
        "mutation_rate": 0.4,
        "description": "Extended evolution over many generations"
    },
    7: {
        "name": "Small Population Intensive",
        "max_generations": 10,
        "population_size": 5,
        "top_k": 2,
        "mutation_rate": 0.45,
        "description": "Minimal population with moderate mutation"
    },
    8: {
        "name": "Large Population Diverse",
        "max_generations": 8,
        "population_size": 15,
        "top_k": 5,
        "mutation_rate": 0.35,
        "description": "Large diverse population for broad exploration"
    }
}


def run_student_experiment(student_name: str, config_id: int, problem: str = "both"):
    """Run experiment with specific configuration and collect all required data."""

    print(f"\n{'='*80}")
    print(f"Student Data Collection for: {student_name}")
    print(f"Configuration ID: {config_id} - {PARAMETER_CONFIGS[config_id]['name']}")
    print(f"{'='*80}\n")

    # Load base config and update with student parameters
    cfg = Config.load("./config.yaml")
    params = PARAMETER_CONFIGS[config_id]

    cfg.raw["project"]["max_generations"] = params["max_generations"]
    cfg.raw["project"]["population_size"] = params["population_size"]
    cfg.raw["project"]["top_k"] = params["top_k"]
    cfg.raw["project"]["mutation_rate"] = params["mutation_rate"]

    # Create output directory
    output_dir = Path(f"./student_data/{student_name.replace(' ', '_')}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save configuration
    config_path = output_dir / "configuration.json"
    with open(config_path, 'w') as f:
        json.dump({
            "student_name": student_name,
            "config_id": config_id,
            "config_name": params["name"],
            "description": params["description"],
            "parameters": {k: v for k, v in params.items() if k not in ["name", "description"]},
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)

    print(f" Configuration saved to {config_path}")

    # Run experiments for each problem
    problems = ["pacman", "matrix"] if problem == "both" else [problem]
    all_results = {}

    for prob in problems:
        print(f"\n{'─'*80}")
        print(f"Running {prob.upper()} experiment...")
        print(f"{'─'*80}")

        start_time = time.time()

        try:
            results = run_experiment(cfg, problem=prob)
            runtime = time.time() - start_time

            # Convert to DataFrame
            df = history_to_df(results)

            # Add metadata columns
            df['student_name'] = student_name
            df['config_id'] = config_id
            df['config_name'] = params["name"]
            df['runtime_seconds'] = runtime
            df['timestamp'] = datetime.now().isoformat()

            # Save CSV
            csv_path = output_dir / f"{student_name.replace(' ', '_')}_{prob}_data.csv"
            df.to_csv(csv_path, index=False)
            print(f" Data saved to {csv_path}")

            # Generate fitness plot
            plot_path = output_dir / f"{prob}_fitness_comparison.png"
            plot_results(df, str(plot_path))
            print(f" Plot saved to {plot_path}")

            # Generate detailed analysis plots
            generate_detailed_plots(df, prob, output_dir, params)

            all_results[prob] = {
                "results": results,
                "dataframe": df,
                "runtime": runtime,
                "csv_path": csv_path,
                "plot_path": plot_path
            }

            print(f" {prob.upper()} experiment completed in {runtime:.2f} seconds")

        except Exception as e:
            print(f" Error running {prob} experiment: {e}")
            continue

    # Generate summary report
    generate_summary_report(student_name, params, all_results, output_dir)

    print(f"\n{'='*80}")
    print(f" All data collection completed for {student_name}")
    print(f" Output directory: {output_dir}")
    print(f"{'='*80}\n")

    return all_results


def generate_detailed_plots(df: pd.DataFrame, problem: str, output_dir: Path, params: dict):
    """Generate comprehensive analysis plots."""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{problem.upper()} Evolution Analysis - {params["name"]}', fontsize=14, fontweight='bold')

    # Plot 1: Fitness over generations
    ax1 = axes[0, 0]
    for mode in df['mode'].unique():
        subset = df[df['mode'] == mode]
        ax1.plot(subset['generation'], subset['fitness'], marker='o', label=mode, linewidth=2)
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('Fitness Score')
    ax1.set_title('Fitness Evolution by Mode')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Best fitness per mode (bar chart)
    ax2 = axes[0, 1]
    best_fitness = df.groupby('mode')['fitness'].max()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    ax2.bar(best_fitness.index, best_fitness.values, color=colors[:len(best_fitness)])
    ax2.set_ylabel('Best Fitness')
    ax2.set_title('Best Fitness by Evolution Mode')
    ax2.set_xticklabels(best_fitness.index, rotation=15, ha='right')
    for i, v in enumerate(best_fitness.values):
        ax2.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')

    # Plot 3: Metric-specific analysis
    ax3 = axes[1, 0]
    metric_cols = [col for col in df.columns if col.startswith('metric_')]
    if metric_cols:
        for mode in df['mode'].unique():
            subset = df[df['mode'] == mode]
            # Plot first metric as example
            ax3.plot(subset['generation'], subset[metric_cols[0]], marker='s', label=mode, alpha=0.7)
        ax3.set_xlabel('Generation')
        ax3.set_ylabel(metric_cols[0].replace('metric_', '').title())
        ax3.set_title(f'{metric_cols[0].replace("metric_", "").title()} Over Generations')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

    # Plot 4: Generation-by-generation improvement
    ax4 = axes[1, 1]
    for mode in df['mode'].unique():
        subset = df[df['mode'] == mode].sort_values('generation')
        if len(subset) > 1:
            improvements = subset['fitness'].diff().fillna(0)
            ax4.plot(subset['generation'], improvements.cumsum(), marker='d', label=mode)
    ax4.set_xlabel('Generation')
    ax4.set_ylabel('Cumulative Fitness Improvement')
    ax4.set_title('Cumulative Fitness Improvement')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plot_path = output_dir / f"{problem}_detailed_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f" Detailed analysis plot saved to {plot_path}")


def generate_summary_report(student_name: str, params: dict, results: dict, output_dir: Path):
    """Generate a text summary report with analysis."""

    report_path = output_dir / f"{student_name.replace(' ', '_')}_analysis_summary.txt"

    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"STUDENT DATA ANALYSIS REPORT\n")
        f.write(f"Student: {student_name}\n")
        f.write(f"Configuration: {params['name']}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

        f.write("PARAMETER CONFIGURATION\n")
        f.write("-"*80 + "\n")
        f.write(f"Description: {params['description']}\n")
        f.write(f"  • Max Generations: {params['max_generations']}\n")
        f.write(f"  • Population Size: {params['population_size']}\n")
        f.write(f"  • Top-K Selection: {params['top_k']}\n")
        f.write(f"  • Mutation Rate: {params['mutation_rate']}\n\n")

        for problem, data in results.items():
            f.write(f"\n{problem.upper()} EXPERIMENT RESULTS\n")
            f.write("-"*80 + "\n")

            df = data['dataframe']
            f.write(f"Runtime: {data['runtime']:.2f} seconds\n")
            f.write(f"Total Generations: {df['generation'].max() + 1}\n")
            f.write(f"Total Evaluations: {len(df)}\n\n")

            f.write("BEST FITNESS BY MODE:\n")
            for mode in df['mode'].unique():
                mode_data = df[df['mode'] == mode]
                best_fitness = mode_data['fitness'].max()
                best_gen = mode_data[mode_data['fitness'] == best_fitness]['generation'].iloc[0]
                f.write(f"  • {mode:20s}: {best_fitness:.4f} (achieved at generation {best_gen})\n")

            f.write("\nIMPROVEMENT ANALYSIS:\n")
            for mode in df['mode'].unique():
                mode_data = df[df['mode'] == mode].sort_values('generation')
                if len(mode_data) > 1:
                    initial = mode_data['fitness'].iloc[0]
                    final = mode_data['fitness'].iloc[-1]
                    improvement = final - initial
                    improvement_pct = (improvement / initial * 100) if initial > 0 else 0
                    f.write(f"  • {mode:20s}: {improvement:+.4f} ({improvement_pct:+.2f}%)\n")

            f.write("\nSTEPS PER GENERATION:\n")
            mode_counts = df.groupby('mode')['generation'].nunique()
            for mode, count in mode_counts.items():
                avg_time = data['runtime'] / count if count > 0 else 0
                f.write(f"  • {mode:20s}: {count} generations, ~{avg_time:.2f}s per generation\n")

            f.write("\n" + "="*80 + "\n")

    print(f" Summary report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Collect student experiment data for AOA Project Round 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Configuration IDs:
  1: Fast Exploration (High Mutation) - gens=8, pop=6, k=2, mut=0.6
  2: Balanced Standard - gens=10, pop=8, k=3, mut=0.35
  3: Conservative (Low Mutation) - gens=12, pop=10, k=4, mut=0.2
  4: Elite-Focused - gens=10, pop=12, k=6, mut=0.3
  5: Rapid Evolution - gens=5, pop=10, k=3, mut=0.5
  6: Deep Search - gens=15, pop=8, k=3, mut=0.4
  7: Small Population Intensive - gens=10, pop=5, k=2, mut=0.45
  8: Large Population Diverse - gens=8, pop=15, k=5, mut=0.35

Example:
  python3 collect_student_data.py --student "John Doe" --config-id 1
        """
    )

    parser.add_argument('--student', '-s', required=True,
                       help='Student name (e.g., "John Doe")')
    parser.add_argument('--config-id', '-c', type=int, required=True, choices=range(1, 9),
                       help='Configuration ID (1-8)')
    parser.add_argument('--problem', '-p', choices=['pacman', 'matrix', 'both'], default='both',
                       help='Which problem to run (default: both)')

    args = parser.parse_args()

    if args.config_id not in PARAMETER_CONFIGS:
        print(f"Error: Invalid config ID {args.config_id}")
        return 1

    try:
        run_student_experiment(args.student, args.config_id, args.problem)
        return 0
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
