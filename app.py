import streamlit as st
import pandas as pd
import time
from pathlib import Path
from datetime import datetime

from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df, plot_results
from src.engine.runner import _load_base_code


st.set_page_config(
    page_title="Evolve - Evolutionary Algorithm Discovery", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Evolve: Evolutionary Algorithm Discovery System inspired by AlphaEvolve"
    }
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    div.row-widget.stRadio > div {
        flex-direction: row;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

_HERE = Path(__file__).parent
cfg = Config.load(str(_HERE / "config.yaml"))

# Header with gradient styling
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title(" Evolve: Evolutionary Algorithm Discovery")
st.markdown("*A Simplified Evolutionary Agent for Algorithm Discovery - Inspired by AlphaEvolve*")
st.markdown('</div>', unsafe_allow_html=True)

# Sidebar with project information
with st.sidebar:
    st.markdown("###  About Evolve")
    st.markdown("""
    This system uses evolutionary algorithms to discover and optimize code solutions.
    
    **Key Features:**
    -  Multiple evolution strategies
    -  LLM-guided improvements
    -  Comprehensive analytics
    -  Export capabilities
    -  Fitness caching
    """)
    
    st.markdown("---")
    st.markdown("###  Quick Guide")
    st.markdown("""
    1. Select a problem (Pacman or Matrix)
    2. Adjust hyperparameters
    3. Click 'Run Evolution'
    4. Analyze results & export
    """)
    
    st.markdown("---")
    st.markdown("###  System Status")
    
    # Check LLM availability
    try:
        from src.llm.remote import RemoteLLM
        import os
        has_api_key = bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
        llm_status = " Available" if has_api_key else " No API Key"
    except:
        llm_status = " Not Configured"
    
    st.markdown(f"**LLM API:** {llm_status}")
    st.markdown(f"**Cache:**  Enabled")
    
    # Check Pacman availability
    pacman_path = _HERE / "third_party/pacman/pacman.py"
    pacman_status = " Available" if pacman_path.exists() else " Simulation Mode"
    st.markdown(f"**Pacman:** {pacman_status}")

# Problem selection
problem = st.selectbox(" Select Problem", ["pacman", "matrix"])

# Display problem description based on selection
st.markdown("###  Algorithm / Problem Description")
if problem == "pacman":
    st.info("""
    **Pacman Agent Optimization**: This problem evolves game-playing agents using evolutionary algorithms 
    to maximize three objectives:
    - **Score**: Points earned in the game (higher is better)
    - **Survival Time**: Number of timesteps the agent stays alive (higher is better)  
    - **Efficiency**: Minimize unnecessary steps/moves (lower is better)
    
    **Fitness Function**: F = 0.6 × score + 0.3 × survival_time - 0.1 × steps
    
    The evolutionary algorithm generates candidate agents through mutations, evaluates each using the UC Berkeley 
    Pacman simulator, and selects the best performers for the next generation.
    """)
else:
    st.info("""
    **3x3 Matrix Multiplication Optimization**: This problem evolves code for matrix multiplication 
    with two competing objectives:
    - **Correctness**: The code must produce correct results (measured on test cases)
    - **Operation Cost**: Minimize the number of multiplication and addition operations
    
    **Fitness Function**: F = 0.7 × correctness + 0.3 × (1 - normalized_ops)
    
    The evolutionary algorithm mutates matrix multiplication implementations to find efficient algorithms 
    that maintain correctness while reducing computational cost.
    """)

# Show initial code before running
st.markdown("###  Initial Code")
if problem == "pacman":
    initial_code = _load_base_code(
        cfg.get("pacman", "base_agent_path"),
        fallback=str(_HERE / "data/templates/pacman_agent_template.py"),
    )
else:
    initial_code = _load_base_code(
        str(_HERE / "data/templates/matrix_base.py"),
        fallback=str(_HERE / "data/templates/matrix_base.py"),
    )
with st.expander("View Initial Code", expanded=False):
    st.code(initial_code, language="python")

st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("###  Hyperparameters")
    generations = st.number_input(
        "Number of Generations", 
        min_value=1, 
        max_value=50, 
        value=cfg.get("project", "max_generations"),
        help="Number of evolutionary cycles to run. More generations allow better optimization but take longer."
    )
    population = st.number_input(
        "Population Size", 
        min_value=2, 
        max_value=50, 
        value=cfg.get("project", "population_size"),
        help="Number of candidate solutions per generation. Larger populations explore more but are slower."
    )
    top_k = st.number_input(
        "Top-K Selection", 
        min_value=1, 
        max_value=20, 
        value=cfg.get("project", "top_k"),
        help="Number of best candidates to keep as parents for next generation (elitism)."
    )
    mutation_rate = st.slider(
        "Mutation Rate", 
        min_value=0.0, 
        max_value=1.0, 
        value=cfg.get("project", "mutation_rate"),
        help="Probability of mutation vs. cloning. Higher values increase exploration."
    )
    
    # Validation
    if top_k >= population:
        st.warning(" Top-K should be less than population size for effective evolution.")
    
    st.markdown("---")
    st.markdown("#####  Recommended Presets")
    preset_col1, preset_col2 = st.columns(2)
    with preset_col1:
        if st.button(" Fast", help="Quick experimentation"):
            generations = 5
            population = 6
            top_k = 2
            mutation_rate = 0.4
    with preset_col2:
        if st.button(" Optimal", help="Balanced performance"):
            generations = 10
            population = 8
            top_k = 3
            mutation_rate = 0.35
    
    st.markdown("---")
    run_btn = st.button(" Run Evolution", type="primary", use_container_width=True)

if run_btn:
    cfg.raw["project"]["max_generations"] = generations
    cfg.raw["project"]["population_size"] = population
    cfg.raw["project"]["top_k"] = top_k
    cfg.raw["project"]["mutation_rate"] = mutation_rate

    # Create progress tracking placeholder
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    with progress_placeholder.container():
        st.markdown("###  Evolution in Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
    start_time = time.time()
    
    # Simulate progress updates (in real implementation, this would be callbacks from evolve.py)
    with status_placeholder.container():
        st.info(" Initializing evolutionary algorithm...")
        time.sleep(0.5)
        
    try:
        results = run_experiment(cfg, problem=problem)
        elapsed_time = time.time() - start_time
        
        progress_bar.progress(100)
        status_text.text(" Evolution completed successfully!")
        time.sleep(1)
        progress_placeholder.empty()
        
        # Success message with timing
        st.markdown(f"""
        <div class="success-box">
            <h4> Evolution Completed Successfully</h4>
            <p> <strong>Total Time:</strong> {elapsed_time:.2f} seconds</p>
            <p> <strong>Generations:</strong> {generations}</p>
            <p> <strong>Population Size:</strong> {population}</p>
            <p> <strong>Problem:</strong> {problem.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        df = history_to_df(results)
        out_plot = str(_HERE / f"outputs/{problem}_fitness.png")
        plot_results(df, out_plot)
        
    except Exception as e:
        progress_placeholder.empty()
        st.error(f" Error during evolution: {str(e)}")
        st.exception(e)
        st.stop()

    with col2:
        st.markdown("###  Results & Analysis")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([" Overview", " Detailed Metrics", " Comparison", " Export"])
        
        with tab1:
            # Fitness visualization with multiple series
            st.markdown("#### Fitness Evolution Across Generations")
            st.line_chart(df, x="generation", y="fitness", color="mode")
            
            # Show the saved plot
            if Path(out_plot).exists():
                st.image(out_plot, use_column_width=True)
            
            # Best scores comparison with styling
            st.markdown("####  Best Scores by Mode")
            best_scores = (
                df.sort_values(["mode", "generation"]).groupby("mode").tail(1)[
                    ["mode", "fitness"]
                ].copy()
            )
            best_scores["fitness"] = best_scores["fitness"].round(4)
            
            # Add rank and color coding
            best_scores = best_scores.sort_values("fitness", ascending=False).reset_index(drop=True)
            best_scores["rank"] = range(1, len(best_scores) + 1)
            best_scores = best_scores[["rank", "mode", "fitness"]]
            
            st.dataframe(
                best_scores,
                use_container_width=True,
                column_config={
                    "rank": st.column_config.NumberColumn(" Rank", help="Performance rank"),
                    "mode": st.column_config.TextColumn("Evolution Mode"),
                    "fitness": st.column_config.NumberColumn("Fitness Score", format="%.4f")
                },
                hide_index=True
            )
            
            # Statistical summary
            st.markdown("####  Statistical Summary")
            summary_stats = df.groupby("mode")["fitness"].agg([
                ("mean", "mean"),
                ("std", "std"),
                ("min", "min"),
                ("max", "max"),
                ("final", "last")
            ]).round(4)
            st.dataframe(summary_stats, use_container_width=True)
        
        with tab2:
            # Detailed metrics and convergence analysis
            st.markdown("####  Convergence Analysis")
            
            # Calculate improvement rate
            improvement_data = []
            for mode in df["mode"].unique():
                mode_df = df[df["mode"] == mode].sort_values("generation")
                if len(mode_df) > 1:
                    initial_fitness = mode_df.iloc[0]["fitness"]
                    final_fitness = mode_df.iloc[-1]["fitness"]
                    improvement = ((final_fitness - initial_fitness) / max(abs(initial_fitness), 0.0001)) * 100
                    improvement_data.append({
                        "Mode": mode,
                        "Initial Fitness": f"{initial_fitness:.4f}",
                        "Final Fitness": f"{final_fitness:.4f}",
                        "Improvement %": f"{improvement:.2f}%"
                    })
            
            if improvement_data:
                st.dataframe(pd.DataFrame(improvement_data), use_container_width=True, hide_index=True)
            
            # Generation-by-generation breakdown
            st.markdown("####  Generation-by-Generation Evolution")
            for mode in ["no_evolution", "random_mutation", "llm_guided"]:
                if mode in results:
                    with st.expander(f" {mode.upper().replace('_', ' ')}", expanded=False):
                        mode_history = []
                        prev_best_fitness = 0.0
                        for gen in results[mode].history:
                            avg_fitness = sum(c.fitness or 0 for c in gen.candidates) / len(gen.candidates)
                            best_fitness = gen.best.fitness if gen.best.fitness else 0.0
                            improvement = best_fitness - prev_best_fitness if mode_history else 0.0
                            mode_history.append({
                                "Generation": gen.generation,
                                "Best Fitness": f"{best_fitness:.4f}",
                                "Avg Fitness": f"{avg_fitness:.4f}",
                                "Population": len(gen.candidates),
                                "Improvement": f"{improvement:.4f}"
                            })
                            prev_best_fitness = best_fitness
                        st.dataframe(pd.DataFrame(mode_history), use_container_width=True, hide_index=True)
        
        with tab3:
            # Comparison and operation explanations
            st.markdown("####  Operation Explanations")
            st.markdown("""
            **Evolutionary Operations Performed:**
            
            1. **Clone**: Exact copy of parent code (no modification)
            2. **Mutate**: Random modifications including:
               - **Random Perturb**: Tweaks numeric literals in the code
               - **Line Swap**: Exchanges two random lines of code
               - **Template Replace**: Injects code fragments from template library
            3. **LLM Improve**: AI-guided code refinement using language models (in `llm_guided` mode)
            
            **Selection Strategy:**
            - Each generation evaluates all candidates using the fitness function
            - Top-K candidates (elite) are preserved
            - New candidates are generated from elite parents through mutations
            - Process repeats for the specified number of generations
            """)
            
            # Operation statistics
            st.markdown("##### Operation Statistics (Final Generation)")
            op_rows = []
            for mode, res in results.items():
                last_gen = res.history[-1]
                counts = {}
                for cand in last_gen.candidates:
                    op = cand.meta.get("op", "unknown")
                    counts[op] = counts.get(op, 0) + 1
                for op, count in counts.items():
                    op_rows.append({"Mode": mode, "Operation": op, "Count": count})
            if op_rows:
                op_df = pd.DataFrame(op_rows)
                st.dataframe(op_df, use_container_width=True, hide_index=True)
                
                # Visualization of operations
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(10, 4))
                for mode in op_df["Mode"].unique():
                    mode_data = op_df[op_df["Mode"] == mode]
                    ax.bar(mode_data["Operation"] + f" ({mode})", mode_data["Count"], alpha=0.7, label=mode)
                ax.set_xlabel("Operation Type")
                ax.set_ylabel("Count")
                ax.set_title("Operation Distribution by Mode")
                ax.legend()
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
        
        with tab4:
            # Export and download options
            st.markdown("####  Export Results")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                # Download best code
                best_mode = best_scores.iloc[0]["mode"]
                best_code_str = results[best_mode].best_code
                
                st.download_button(
                    label=" Download Best Code",
                    data=best_code_str,
                    file_name=f"best_{problem}_{best_mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                    mime="text/plain",
                    help="Download the best performing code solution"
                )
                
                # Download CSV data
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label=" Download Results CSV",
                    data=csv_data,
                    file_name=f"results_{problem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download complete results data"
                )
            
            with col_exp2:
                # Download full report
                report_content = f"""
# Evolutionary Algorithm Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Configuration
- Problem: {problem}
- Generations: {generations}
- Population Size: {population}
- Top-K: {top_k}
- Mutation Rate: {mutation_rate}
- Elapsed Time: {elapsed_time:.2f}s

## Results Summary
{best_scores.to_string()}

## Best Solution ({best_mode})
```python
{best_code_str}
```

## Statistical Analysis
{summary_stats.to_string()}
"""
                st.download_button(
                    label=" Download Full Report",
                    data=report_content,
                    file_name=f"report_{problem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    help="Download comprehensive analysis report"
                )
                
                # Show raw data preview
                st.markdown("#####  Raw Data Preview")
                st.dataframe(df.head(20), use_container_width=True)
        
        # Final best solution - prominent display
        st.markdown("---")
        st.markdown("###  Final Best Solution")
        best_mode = best_scores.iloc[0]["mode"]
        best_fitness = best_scores.iloc[0]["fitness"]
        
        st.markdown(f"""
        <div class="success-box">
            <h4> Winner: {best_mode.upper().replace('_', ' ')}</h4>
            <p><strong>Fitness Score:</strong> {best_fitness:.4f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("View Best Solution Code", expanded=True):
            st.code(results[best_mode].best_code, language="python")

# References section
st.markdown("---")
st.markdown("###  References")
st.markdown("""
1. **AlphaEvolve**: A. Novikov et al., "AlphaEvolve: A coding agent for scientific and algorithmic discovery," 
   arXiv:2506.13131, Jun. 2025. [DOI: 10.48550/arXiv.2506.13131](https://doi.org/10.48550/arXiv.2506.13131)

2. **Evolutionary Algorithms**: S. Tamilselvi, "Introduction to Evolutionary Algorithms," in *Genetic Algorithms*, 
   IntechOpen, 2022. [DOI: 10.5772/intechopen.104198](https://doi.org/10.5772/intechopen.104198)

3. **Overview of Evolutionary Algorithms**: H. Amit, "An Overview of Evolutionary Algorithms," *We Talk Data*, 
   [Medium Article](https://medium.com/we-talk-data/an-overview-of-evolutionary-algorithms-90a52526603e)

4. **UC Berkeley Pacman AI Project**: [Project Overview](http://ai.berkeley.edu/project_overview.html)

5. **Streamlit Documentation**: [Streamlit](https://streamlit.io/)

6. **FastAPI Documentation**: [FastAPI](https://fastapi.tiangolo.com/)

7. **LangChain for LLM Integration**: [LangChain Documentation](https://python.langchain.com/)

8. **Llama.cpp**: [GitHub Repository](https://github.com/ggerganov/llama.cpp)
""")

st.markdown("---")
st.caption(" Note: Pacman evaluation requires the UC Berkeley Pacman project in ./third_party/pacman/")
