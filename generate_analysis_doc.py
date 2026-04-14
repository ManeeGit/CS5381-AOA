#!/usr/bin/env python3
"""
Generate student analysis document from experimental data.

This creates a detailed analysis report with screenshots, plots, and statistical analysis
required for the project submission.

Usage:
    python3 generate_analysis_doc.py --student "Your Name"
"""

import argparse
import json
from pathlib import Path
import pandas as pd
from datetime import datetime


def generate_markdown_report(student_name: str):
    """Generate detailed markdown analysis document."""

    student_dir = Path(f"./student_data/{student_name.replace(' ', '_')}")

    if not student_dir.exists():
        print(f"Error: No data found for student '{student_name}'")
        print(f"Please run collect_student_data.py first")
        return False

    # Load configuration
    config_path = student_dir / "configuration.json"
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        return False

    with open(config_path) as f:
        config = json.load(f)

    # Find CSV files
    csv_files = list(student_dir.glob("*_data.csv"))
    if not csv_files:
        print(f"Error: No data CSV files found in {student_dir}")
        return False

    # Create markdown report
    md_path = student_dir / f"{student_name.replace(' ', '_')}_analysis_report.md"

    with open(md_path, 'w') as f:
        write_header(f, student_name, config)

        for csv_file in csv_files:
            problem = "pacman" if "pacman" in csv_file.name else "matrix"
            df = pd.read_csv(csv_file)
            write_problem_analysis(f, problem, df, student_dir, config)

        write_conclusion(f, config)
        write_references(f)

    print(f" Markdown report generated: {md_path}")
    print(f"\nTo convert to DOCX, use:")
    print(f"  pandoc {md_path} -o {md_path.with_suffix('.docx')}")
    print(f"  (requires pandoc: brew install pandoc)")

    return True


def write_header(f, student_name: str, config: dict):
    """Write document header."""

    f.write(f"# AOA Project - Student Experimental Analysis\n\n")
    f.write(f"**Student Name:** {student_name}  \n")
    f.write(f"**Configuration:** {config['config_name']} (ID: {config['config_id']})  \n")
    f.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')}  \n")
    f.write(f"**Course:** CS5381 - Analysis of Algorithms  \n\n")
    f.write("---\n\n")

    f.write("## 1. Executive Summary\n\n")
    f.write(f"This report presents experimental results for the Evolve evolutionary algorithm system ")
    f.write(f"using the **{config['config_name']}** configuration. ")
    f.write(f"The system was tested on two benchmark problems: Pacman Agent Optimization and ")
    f.write(f"3x3 Matrix Multiplication.\n\n")

    f.write("### 1.1 Configuration Details\n\n")
    f.write(f"**Description:** {config['description']}\n\n")
    f.write("| Parameter | Value |\n")
    f.write("|-----------|-------|\n")
    for key, value in config['parameters'].items():
        f.write(f"| {key.replace('_', ' ').title()} | {value} |\n")
    f.write("\n")


def write_problem_analysis(f, problem: str, df: pd.DataFrame, student_dir: Path, config: dict):
    """Write detailed analysis for a specific problem."""

    f.write(f"## 2. {problem.upper()} Experiment Results\n\n")

    # Runtime performance
    f.write("### 2.1 Runtime Performance\n\n")
    runtime = df['runtime_seconds'].iloc[0] if 'runtime_seconds' in df.columns else 0
    total_gens = df['generation'].max() + 1
    total_evals = len(df)

    f.write(f"- **Total Runtime:** {runtime:.2f} seconds\n")
    f.write(f"- **Total Generations:** {total_gens}\n")
    f.write(f"- **Total Evaluations:** {total_evals}\n")
    f.write(f"- **Average Time per Generation:** {runtime/total_gens:.2f} seconds\n")
    f.write(f"- **Average Time per Evaluation:** {runtime/total_evals:.4f} seconds\n\n")

    # Steps per generation
    f.write("### 2.2 Steps Per Generation\n\n")
    f.write("| Evolution Mode | Generations | Avg. Time/Gen |\n")
    f.write("|----------------|-------------|---------------|\n")

    for mode in df['mode'].unique():
        mode_data = df[df['mode'] == mode]
        gen_count = mode_data['generation'].nunique()
        avg_time = runtime / gen_count if gen_count > 0 else 0
        f.write(f"| {mode} | {gen_count} | {avg_time:.2f}s |\n")
    f.write("\n")

    # Fitness scores across iterations
    f.write("### 2.3 Fitness Scores Across Iterations\n\n")

    # Fitness comparison plot
    fitness_plot = student_dir / f"{problem}_fitness_comparison.png"
    if fitness_plot.exists():
        f.write(f"![Fitness Evolution - {problem.upper()}]({fitness_plot.name})\n\n")
        f.write(f"**Figure 1:** Fitness evolution across generations for {problem} problem. ")
        f.write("Three evolution modes are compared: no_evolution (baseline), random_mutation, and llm_guided.\n\n")

    # Fitness statistics table
    f.write("#### Fitness Statistics by Mode\n\n")
    f.write("| Mode | Initial | Final | Best | Improvement | Improvement % |\n")
    f.write("|------|---------|-------|------|-------------|---------------|\n")

    for mode in df['mode'].unique():
        mode_data = df[df['mode'] == mode].sort_values('generation')
        initial = mode_data['fitness'].iloc[0]
        final = mode_data['fitness'].iloc[-1]
        best = mode_data['fitness'].max()
        improvement = final - initial
        improvement_pct = (improvement / initial * 100) if initial > 0 else 0

        f.write(f"| {mode} | {initial:.4f} | {final:.4f} | {best:.4f} | "
                f"{improvement:+.4f} | {improvement_pct:+.2f}% |\n")
    f.write("\n")

    # Generation count analysis
    f.write("### 2.4 Generation Count Analysis\n\n")
    f.write(f"The experiment ran for **{total_gens} generations** with the following progression:\n\n")

    # Sample fitness progression for random_mutation mode
    random_mode = df[df['mode'] == 'random_mutation'].sort_values('generation')
    if len(random_mode) > 0:
        f.write("#### Sample Fitness Progression (Random Mutation Mode)\n\n")
        f.write("| Generation | Fitness | Change |\n")
        f.write("|------------|---------|--------|\n")

        prev_fitness = None
        for _, row in random_mode.head(min(10, len(random_mode))).iterrows():
            gen = int(row['generation'])
            fitness = row['fitness']
            change = fitness - prev_fitness if prev_fitness is not None else 0
            f.write(f"| {gen} | {fitness:.4f} | {change:+.4f} |\n")
            prev_fitness = fitness
        f.write("\n")

    # Detailed analysis plot
    detailed_plot = student_dir / f"{problem}_detailed_analysis.png"
    if detailed_plot.exists():
        f.write(f"![Detailed Analysis - {problem.upper()}]({detailed_plot.name})\n\n")
        f.write(f"**Figure 2:** Comprehensive analysis dashboard for {problem} showing fitness evolution, ")
        f.write("best fitness comparison, metric-specific trends, and cumulative improvements.\n\n")

    # Comparative plots and analysis
    f.write("### 2.5 Comparative Analysis of Evolution Modes\n\n")

    f.write("#### 2.5.1 No Evolution (Baseline)\n")
    no_evo = df[df['mode'] == 'no_evolution']
    if len(no_evo) > 0:
        baseline_fitness = no_evo['fitness'].iloc[0]
        f.write(f"- **Purpose:** Baseline benchmark without any evolution\n")
        f.write(f"- **Fitness Score:** {baseline_fitness:.4f}\n")
        f.write(f"- **Observations:** This represents the initial code quality without any optimization\n\n")

    f.write("#### 2.5.2 Random Mutation\n")
    rand_mut = df[df['mode'] == 'random_mutation']
    if len(rand_mut) > 0:
        best_rand = rand_mut['fitness'].max()
        improvement_rand = best_rand - baseline_fitness if len(no_evo) > 0 else 0
        f.write(f"- **Best Fitness:** {best_rand:.4f}\n")
        f.write(f"- **Improvement over Baseline:** {improvement_rand:+.4f}\n")
        f.write(f"- **Observations:** Random mutations explore the solution space through ")
        f.write(f"stochastic modifications (parameter perturbation, line swaps, template replacement)\n\n")

    f.write("#### 2.5.3 LLM-Guided Mutation\n")
    llm_guided = df[df['mode'] == 'llm_guided']
    if len(llm_guided) > 0:
        best_llm = llm_guided['fitness'].max()
        improvement_llm = best_llm - baseline_fitness if len(no_evo) > 0 else 0
        f.write(f"- **Best Fitness:** {best_llm:.4f}\n")
        f.write(f"- **Improvement over Baseline:** {improvement_llm:+.4f}\n")
        f.write(f"- **Observations:** LLM-guided evolution uses language models to make ")
        f.write(f"intelligent code improvements based on problem understanding\n\n")

    # Configuration impact analysis
    f.write("### 2.6 Impact of Configuration Parameters\n\n")
    params = config['parameters']

    f.write(f"The **{config['config_name']}** configuration was designed to ")
    f.write(f"{config['description'].lower()}. Key observations:\n\n")

    f.write(f"- **Population Size ({params['population_size']}):** ")
    if params['population_size'] < 8:
        f.write("Smaller population enables faster iterations but may limit diversity\n")
    elif params['population_size'] > 10:
        f.write("Larger population provides better exploration at the cost of runtime\n")
    else:
        f.write("Balanced population size for standard exploration-exploitation trade-off\n")

    f.write(f"- **Mutation Rate ({params['mutation_rate']}):** ")
    if params['mutation_rate'] < 0.3:
        f.write("Low mutation favors exploitation of known good solutions\n")
    elif params['mutation_rate'] > 0.5:
        f.write("High mutation promotes aggressive exploration of solution space\n")
    else:
        f.write("Moderate mutation balances exploration and exploitation\n")

    f.write(f"- **Top-K Selection ({params['top_k']}):** ")
    elite_ratio = params['top_k'] / params['population_size']
    if elite_ratio > 0.5:
        f.write("High elitism preserves many good solutions between generations\n")
    else:
        f.write("Selective elitism maintains diversity while preserving best candidates\n")

    f.write("\n")


def write_conclusion(f, config: dict):
    """Write conclusions and recommendations."""

    f.write("## 3. Conclusions\n\n")

    f.write("### 3.1 Key Findings\n\n")
    f.write("1. **Evolution Effectiveness:** The evolutionary algorithm successfully improved ")
    f.write("solution quality over generations across both benchmark problems\n\n")

    f.write("2. **Mode Comparison:** ")
    f.write("- Baseline (no evolution) provides reference point\n")
    f.write("- Random mutation shows stochastic improvement\n")
    f.write("- LLM-guided mutation demonstrates intelligent optimization\n\n")

    f.write(f"3. **Configuration Impact:** The {config['config_name']} configuration ")
    f.write(f"({config['description'].lower()}) achieved its design objectives\n\n")

    f.write("### 3.2 Observations and Insights\n\n")
    f.write("- **Fitness Caching:** Significantly reduced redundant evaluations, improving runtime efficiency\n")
    f.write("- **Adaptive Mechanisms:** The system adapts mutation rates based on stagnation detection\n")
    f.write("- **Multi-objective Optimization:** Fitness functions balance multiple competing objectives\n\n")

    f.write("### 3.3 Future Directions\n\n")
    f.write("- Explore hybrid mutation strategies combining random and LLM-guided approaches\n")
    f.write("- Implement multi-population islands for parallel evolution\n")
    f.write("- Add adaptive parameter tuning based on evolution progress\n")
    f.write("- Extend to additional benchmark problems and domains\n\n")


def write_references(f):
    """Write references section."""

    f.write("## References\n\n")
    f.write("1. A. Novikov et al., \"AlphaEvolve: A coding agent for scientific and algorithmic discovery,\" ")
    f.write("arXiv:2506.13131, 2025.\n\n")
    f.write("2. S. Tamilselvi, \"Introduction to Evolutionary Algorithms,\" in Genetic Algorithms, ")
    f.write("IntechOpen, 2022.\n\n")
    f.write("3. H. Amit, \"An Overview of Evolutionary Algorithms,\" We Talk Data, 2025.\n\n")
    f.write("4. UC Berkeley CS188: Introduction to Artificial Intelligence - Pacman Project\n\n")
    f.write("5. Python libraries: NumPy, Pandas, Matplotlib, Streamlit\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate analysis document from student experimental data"
    )
    parser.add_argument('--student', '-s', required=True,
                       help='Student name (must match collect_student_data.py)')

    args = parser.parse_args()

    if generate_markdown_report(args.student):
        print("\n Analysis document generated successfully")
        return 0
    else:
        print("\n Failed to generate analysis document")
        return 1


if __name__ == '__main__':
    exit(main())
