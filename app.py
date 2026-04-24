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
        background-color: #000000;
        border: 1px solid #00ff88;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    .success-box h4, .success-box p, .success-box strong {
        color: #ffffff !important;
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
    1. Select a problem (Pacman, Matrix, or Pseudocode)
    2. Adjust hyperparameters
    3. Click 'Run Evolution'
    4. Analyze results & export
    """)
    
    st.markdown("---")
    st.markdown("###  LLM Configuration")

    _llm_provider = st.selectbox(
        "LLM Provider",
        options=["ollama", "openai", "gemini", "local"],
        index=["ollama", "openai", "gemini", "local"].index(
            cfg.get("llm", "provider", default="ollama")
        ),
        help="ollama = local model via Ollama (recommended). openai/gemini = remote API.",
    )

    _default_models = {
        "ollama": cfg.get("llm", "model_name", default="qwen2.5-coder:7b"),
        "openai": "gpt-3.5-turbo",
        "gemini": "gemini-1.5-flash",
        "local": "llama-cpp",
    }
    _llm_model = st.text_input(
        "Model Name",
        value=_default_models.get(_llm_provider, cfg.get("llm", "model_name", default="qwen2.5-coder:7b")),
        help="For Ollama: name of a pulled model (e.g. qwen2.5-coder:7b). For remote: API model ID.",
    )

    if _llm_provider == "ollama":
        _ollama_host = st.text_input(
            "Ollama Host",
            value=cfg.get("llm", "ollama_host", default="http://localhost:11434"),
            help="URL of the running Ollama server.",
        )
    else:
        _ollama_host = cfg.get("llm", "ollama_host", default="http://localhost:11434")

    # Live status check
    import requests as _req
    if _llm_provider == "ollama":
        try:
            _tags = _req.get(f"{_ollama_host}/api/tags", timeout=3).json()
            _pulled = [m["name"] for m in _tags.get("models", [])]
            if _llm_model in _pulled:
                _llm_status = f" Running · `{_llm_model}`"
            elif _pulled:
                _llm_status = f" Server up · model `{_llm_model}` not found (available: {', '.join(_pulled[:3])})"
            else:
                _llm_status = " Server up but no models pulled"
        except Exception:
            _llm_status = " Ollama not reachable — start with `ollama serve`"
    else:
        import os as _os
        _has_key = bool(_os.getenv("LLM_API_KEY") or _os.getenv("OPENAI_API_KEY"))
        _llm_status = " API key set" if _has_key else " No API key (set LLM_API_KEY env var)"

    st.markdown(f"**Status:** {_llm_status}")

    st.markdown("---")
    st.markdown("###  System Status")
    st.markdown(f"**Cache:**  Enabled")

    # Check Pacman availability
    pacman_path = _HERE / "third_party/pacman/pacman.py"
    pacman_status = " Available" if pacman_path.exists() else " Simulation Mode"
    st.markdown(f"**Pacman:** {pacman_status}")

# Problem selection
problem = st.selectbox(" Select Problem", ["pacman", "matrix", "pseudocode"])

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
elif problem == "matrix":
    st.info("""
    **3x3 Matrix Multiplication Optimization**: This problem evolves code for matrix multiplication 
    with two competing objectives:
    - **Correctness**: The code must produce correct results (measured on test cases)
    - **Operation Cost**: Minimize the number of multiplication and addition operations
    
    **Fitness Function**: F = 0.7 × correctness + 0.3 × (1 - normalized_ops)
    
    The evolutionary algorithm mutates matrix multiplication implementations to find efficient algorithms 
    that maintain correctness while reducing computational cost.
    """)
else:  # pseudocode
    st.info("""
    **Pseudocode / Algorithm Description** *(Bonus Problem)*: This problem evolves sorting algorithm 
    implementations with four configurable fitness dimensions:
    - **Correctness**: Fraction of test cases producing correctly sorted output
    - **Runtime**: Inverse of average execution time — faster algorithms score higher
    - **Code Length**: Shorter, concise implementations score higher
    - **Readability**: Heuristic based on comment density and identifier naming quality
    
    **Fitness Function**: F = w₁×correctness + w₂×runtime + w₃×length + w₄×readability  (Σwᵢ = 1)
    
    Configure the weights using the sliders below. The seed algorithm is bubble sort — evolve it 
    toward insertion sort, merge sort, or quicksort!
    """)
    st.markdown("#### ⚖️ Configurable Fitness Weights")
    st.markdown("Adjust weights below. They must sum to **1.0** (auto-normalised).")
    _pc_col1, _pc_col2, _pc_col3, _pc_col4 = st.columns(4)
    with _pc_col1:
        _w_corr = st.slider("Correctness", 0.0, 1.0, 0.4, 0.05, key="w_corr",
                            help="Weight for fraction of test cases passed.")
    with _pc_col2:
        _w_run = st.slider("Runtime", 0.0, 1.0, 0.2, 0.05, key="w_run",
                           help="Weight for execution speed.")
    with _pc_col3:
        _w_len = st.slider("Code Length", 0.0, 1.0, 0.2, 0.05, key="w_len",
                           help="Weight for code conciseness.")
    with _pc_col4:
        _w_read = st.slider("Readability", 0.0, 1.0, 0.2, 0.05, key="w_read",
                            help="Weight for comment density and naming quality.")
    _w_total = _w_corr + _w_run + _w_len + _w_read
    if abs(_w_total - 1.0) > 0.01:
        # Auto-normalise
        if _w_total > 0:
            _w_corr /= _w_total; _w_run /= _w_total; _w_len /= _w_total; _w_read /= _w_total
        st.warning(f"Weights summed to {_w_total:.2f} — auto-normalised to 1.0")
    else:
        st.success(f"✅ Weights sum to {_w_total:.2f}")
    # Store into config so runner.py picks them up
    if "pseudocode" not in cfg.raw:
        cfg.raw["pseudocode"] = {}
    cfg.raw["pseudocode"]["w_correctness"] = round(_w_corr, 4)
    cfg.raw["pseudocode"]["w_runtime"] = round(_w_run, 4)
    cfg.raw["pseudocode"]["w_length"] = round(_w_len, 4)
    cfg.raw["pseudocode"]["w_readability"] = round(_w_read, 4)

# Show initial code before running
st.markdown("###  Initial Code")
if problem == "pacman":
    initial_code = _load_base_code(
        cfg.get("pacman", "base_agent_path"),
        fallback=str(_HERE / "data/templates/pacman_agent_template.py"),
    )
elif problem == "pseudocode":
    initial_code = _load_base_code(
        str(_HERE / "data/templates/pseudocode_base.py"),
        fallback=str(_HERE / "data/templates/pseudocode_base.py"),
    )
else:
    initial_code = _load_base_code(
        str(_HERE / "data/templates/matrix_base.py"),
        fallback=str(_HERE / "data/templates/matrix_base.py"),
    )
with st.expander("View Initial Code", expanded=False):
    st.code(initial_code, language="python")

# ── Human-in-the-Loop Code Editor ────────────────────────────────────────────
st.markdown("###  Human-in-the-Loop Code Editor")
st.markdown(
    "Edit the base code below before running evolution. "
    "Your code becomes the seed candidate for all three modes. "
    "Leave unchanged to use the default template."
)
_hitl_code = st.text_area(
    "Base Code (editable)",
    value=initial_code,
    height=280,
    key=f"hitl_{problem}",
    help="This code seeds the initial population. Modify it to test human-guided starting points.",
)
# Wire the human override into config so runner.py picks it up
if _hitl_code.strip() and _hitl_code.strip() != initial_code.strip():
    if problem not in cfg.raw:
        cfg.raw[problem] = {}
    cfg.raw[problem]["_human_code_override"] = _hitl_code
else:
    # Clear any stale override so the default template is used
    if problem in cfg.raw:
        cfg.raw[problem].pop("_human_code_override", None)

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
    num_runs = st.number_input(
        "Number of Runs",
        min_value=1,
        max_value=5,
        value=1,
        help="Run the full experiment multiple times and compare observations (problem bank 3-2).",
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
    run_btn = st.button(" Run Evolution", type="primary", use_container_width=True, icon=None)
    baseline_btn = st.button(" Run Baseline Only", help="Runs no_evolution mode and saves baseline CSV for competition comparison", use_container_width=True, icon=None)

if baseline_btn:
    cfg.raw["project"]["max_generations"] = 1
    cfg.raw["project"]["population_size"] = population
    cfg.raw["project"]["top_k"] = top_k
    cfg.raw["project"]["mutation_rate"] = 0.0
    with st.spinner("Running baseline (no evolution)..."):
        import time as _time
        from datetime import datetime as _dt
        _t0 = _time.time()
        try:
            from src.engine.runner import run_experiment as _run, history_to_df as _h2df
            import os as _os3
            if _llm_provider == "ollama":
                from src.llm.ollama_client import OllamaLLM as _OLLM
                _bllm = _OLLM(model=_llm_model, host=_ollama_host)
            elif _llm_provider == "local":
                from src.llm.local import LocalLLM as _LLLM
                _bllm = _LLLM()
            else:
                from src.llm.remote import RemoteLLM as _RLLM
                _bllm = _RLLM(provider=_llm_provider, api_key=_os3.getenv("LLM_API_KEY"), model=_llm_model)
            _res = _run(cfg, problem=problem, llm_override=_bllm)
            _elapsed = _time.time() - _t0
            _df = _h2df(_res)
            _df["total_experiment_time_s"] = _elapsed
            _out = _HERE / "outputs" / f"{problem}_baseline_{_dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
            _out.parent.mkdir(parents=True, exist_ok=True)
            _df.to_csv(_out, index=False)
            st.success(f" Baseline run complete ({_elapsed:.2f}s). Saved to: `{_out.name}`")
            st.dataframe(_df, width='stretch')
        except Exception as _e:
            st.error(f"Baseline run failed: {_e}")

if run_btn:
    cfg.raw["project"]["max_generations"] = generations
    cfg.raw["project"]["population_size"] = population
    cfg.raw["project"]["top_k"] = top_k
    cfg.raw["project"]["mutation_rate"] = mutation_rate

    # ── Live dashboard placeholders ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Live Evolution Dashboard")

    # Competition metrics strip (4 required prints always visible)
    comp_strip = st.empty()

    # Real-time per-mode progress bars
    _mode_labels = {"no_evolution": "Baseline", "random_mutation": "Random Mutation", "llm_guided": "LLM-Guided"}
    live_bars = {}
    live_metric_cols = {}
    for _m, _label in _mode_labels.items():
        _c1, _c2, _c3, _c4, _c5 = st.columns([2, 1, 1, 1, 1])
        _c1.markdown(f"**{_label}**")
        live_bars[_m] = _c1.progress(0, text="waiting…")
        live_metric_cols[_m] = (_c2.empty(), _c3.empty(), _c4.empty(), _c5.empty())

    live_chart_placeholder = st.empty()
    status_placeholder = st.empty()

    # Internal state for streaming chart
    _stream_data: dict = {"no_evolution": [], "random_mutation": [], "llm_guided": []}
    _stream_times: dict = {"no_evolution": [], "random_mutation": [], "llm_guided": []}
    _gen_counter = {"no_evolution": 0, "random_mutation": 0, "llm_guided": 0}
    _total_gens_seen: list = [generations]
    _experiment_start = time.time()

    def _on_generation(mode, gen, total_gens, best_fitness, metrics, elapsed):
        _total_gens_seen[0] = total_gens
        _stream_data[mode].append(best_fitness)
        _stream_times[mode].append(gen)
        _gen_counter[mode] = gen

        # Update progress bar for this mode
        pct = min(int(gen / max(total_gens, 1) * 100), 100)
        live_bars[mode].progress(pct, text=f"Gen {gen}/{total_gens}  |  Fitness {best_fitness:.4f}")

        # Update metric columns: gen / fitness / time / metric
        c2, c3, c4, c5 = live_metric_cols[mode]
        c2.metric("Gen", f"{gen}/{total_gens}")
        c3.metric("Fitness", f"{best_fitness:.4f}")
        c4.metric("Time(s)", f"{elapsed:.2f}")
        first_metric = list(metrics.items())[0] if metrics else ("—", 0)
        c5.metric(first_metric[0], f"{first_metric[1]:.3f}")

        # Update live chart
        chart_rows = []
        for _mode, _vals in _stream_data.items():
            for _g, _f in zip(_stream_times[_mode], _vals):
                chart_rows.append({"generation": _g, "fitness": _f, "mode": _mode})
        # Pad no_evolution as a flat reference line through the current generation
        # so it stays visible while other modes are still running
        if "no_evolution" in _stream_data and _stream_data["no_evolution"]:
            _no_evo_f = _stream_data["no_evolution"][-1]
            _no_evo_gens_seen = set(_stream_times["no_evolution"])
            _cur_max_gen = max(
                (max(_stream_times[_m]) for _m in _stream_data if _stream_times[_m]),
                default=1,
            )
            for _pad_g in range(2, _cur_max_gen + 1):
                if _pad_g not in _no_evo_gens_seen:
                    chart_rows.append({"generation": _pad_g, "fitness": _no_evo_f, "mode": "no_evolution"})
        if chart_rows:
            import pandas as _pd2
            _cdf = _pd2.DataFrame(chart_rows)
            live_chart_placeholder.line_chart(
                _cdf.pivot_table(index="generation", columns="mode", values="fitness"),
            )

        # Update competition metrics strip
        wall = time.time() - _experiment_start
        comp_strip.markdown(
            f"""
<div style="background:#0d1117;border:1px solid #388bfd;border-radius:8px;
            padding:0.7rem 1.2rem;display:flex;gap:2rem;flex-wrap:wrap;">
  <span style="color:#e6edf3;">⏱ <b style="color:#58a6ff;">Running time:</b> {wall:.1f}s</span>
  <span style="color:#e6edf3;">🔄 <b style="color:#58a6ff;">Generations:</b> {gen} / {total_gens}</span>
  <span style="color:#e6edf3;">🏆 <b style="color:#58a6ff;">Best fitness:</b> {best_fitness:.4f}</span>
  <span style="color:#e6edf3;">🧬 <b style="color:#58a6ff;">Mode:</b> {mode}</span>
</div>""",
            unsafe_allow_html=True,
        )

    # Create progress tracking placeholder
    progress_placeholder = st.empty()

    with progress_placeholder.container():
        progress_bar = st.progress(0)
        status_text = st.empty()

    start_time = time.time()
    status_placeholder.info("⚙️ Initializing evolutionary algorithm…")

    try:
        # Build LLM instance from sidebar selection
        import os as _os2, io as _io_cap, contextlib as _ctx
        if _llm_provider == "ollama":
            from src.llm.ollama_client import OllamaLLM
            _llm_instance = OllamaLLM(model=_llm_model, host=_ollama_host)
        elif _llm_provider == "local":
            from src.llm.local import LocalLLM
            _llm_instance = LocalLLM()
        else:
            from src.llm.remote import RemoteLLM
            _api_key = _os2.getenv("LLM_API_KEY") or _os2.getenv("OPENAI_API_KEY")
            _llm_instance = RemoteLLM(provider=_llm_provider, api_key=_api_key, model=_llm_model)

        # Run one or more times (for multiple-observation requirement)
        all_dfs = []
        _terminal_log = ""
        for _run_i in range(int(num_runs)):
            if num_runs > 1:
                status_text.text(f"Run {_run_i+1}/{int(num_runs)} in progress…")
            _buf = _io_cap.StringIO()
            with _ctx.redirect_stdout(_buf):
                _res = run_experiment(
                    cfg, problem=problem,
                    llm_override=_llm_instance,
                    on_generation=_on_generation,
                )
            _terminal_log += f"\n{'='*60}\n RUN {_run_i+1}\n{'='*60}\n" + _buf.getvalue()
            _rdf = history_to_df(_res)
            _rdf["run"] = _run_i + 1
            all_dfs.append(_rdf)

        elapsed_time = time.time() - start_time
        df_all = pd.concat(all_dfs, ignore_index=True)
        results = _res  # last run for code display

        progress_bar.progress(100)
        status_text.text("✅ Evolution complete!")
        progress_placeholder.empty()
        status_placeholder.empty()
        
        # ── Final competition metrics strip ───────────────────────────────
        _no_evo_final = df_all[df_all["mode"] == "no_evolution"]["fitness"].iloc[-1] if "no_evolution" in df_all["mode"].values else 0
        _llm_final    = df_all[df_all["mode"] == "llm_guided"]["fitness"].iloc[-1] if "llm_guided" in df_all["mode"].values else 0
        _rand_final   = df_all[df_all["mode"] == "random_mutation"]["fitness"].iloc[-1] if "random_mutation" in df_all["mode"].values else 0
        _improvement  = ((_llm_final - _no_evo_final) / max(abs(_no_evo_final), 1e-6)) * 100

        st.markdown(f"""
<div style="background:#0d1117;border:2px solid #00ff88;border-radius:10px;
            padding:1rem 1.5rem;margin:1rem 0;">
  <h4 style="color:#00ff88;margin:0 0 0.8rem 0;">✅ Evolution Complete — Competition Metrics</h4>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">
    <div style="background:#161b22;border-radius:8px;padding:0.7rem;text-align:center;">
      <div style="color:#8b949e;font-size:0.75rem;">⏱ Total Time</div>
      <div style="color:#58a6ff;font-size:1.4rem;font-weight:bold;">{elapsed_time:.2f}s</div>
    </div>
    <div style="background:#161b22;border-radius:8px;padding:0.7rem;text-align:center;">
      <div style="color:#8b949e;font-size:0.75rem;">🔄 Generations</div>
      <div style="color:#58a6ff;font-size:1.4rem;font-weight:bold;">{generations} × 3 modes</div>
    </div>
    <div style="background:#161b22;border-radius:8px;padding:0.7rem;text-align:center;">
      <div style="color:#8b949e;font-size:0.75rem;">🏆 LLM Best Fitness</div>
      <div style="color:#00ff88;font-size:1.4rem;font-weight:bold;">{_llm_final:.4f}</div>
    </div>
    <div style="background:#161b22;border-radius:8px;padding:0.7rem;text-align:center;">
      <div style="color:#8b949e;font-size:0.75rem;">📈 vs Baseline</div>
      <div style="color:{'#00ff88' if _improvement >= 0 else '#ff4444'};font-size:1.4rem;font-weight:bold;">
        {'▲' if _improvement >= 0 else '▼'}{abs(_improvement):.1f}%
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        df = history_to_df(results)
        out_plot = str(_HERE / f"outputs/{problem}_fitness.png")
        plot_results(df, out_plot)

        # Terminal output panel
        with st.expander("🖥️ Terminal Output (Running Time · Generations · Score/Cost · Fitness per Iteration)", expanded=False):
            st.code(_terminal_log, language="text")
        
    except Exception as e:
        progress_placeholder.empty()
        st.error(f" Error during evolution: {str(e)}")
        st.exception(e)
        st.stop()

    with col2:
        st.markdown("###  Results & Analysis")

        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Overview", "🔬 Detailed Metrics",
            "🔀 Code Diff", "📊 Comparison", "💾 Export",
        ])

        with tab1:
            # Fitness visualization with multiple series
            st.markdown("#### Fitness Evolution Across Generations")
            st.line_chart(df, x="generation", y="fitness", color="mode")

            # Baseline CSV overlay if available
            _baseline_files = sorted((_HERE / "outputs").glob(f"{problem}_baseline_*.csv"), reverse=True)
            if _baseline_files:
                try:
                    _bdf = pd.read_csv(_baseline_files[0])
                    _baseline_val = _bdf["fitness"].iloc[-1]
                    st.markdown(
                        f"**📂 Baseline reference** (`{_baseline_files[0].name}`): "
                        f"fitness = **{_baseline_val:.4f}** — "
                        f"LLM improvement = **{((_llm_final - _baseline_val)/max(abs(_baseline_val),1e-6)*100):+.1f}%**"
                    )
                except Exception:
                    pass

            # Best scores comparison
            st.markdown("#### 🏅 Best Scores by Mode")
            best_scores = (
                df.sort_values(["mode", "generation"]).groupby("mode").tail(1)[
                    ["mode", "fitness"]
                ].copy()
            )
            best_scores["fitness"] = best_scores["fitness"].round(4)
            best_scores = best_scores.sort_values("fitness", ascending=False).reset_index(drop=True)
            best_scores["rank"] = range(1, len(best_scores) + 1)
            best_scores = best_scores[["rank", "mode", "fitness"]]
            
            st.dataframe(
                best_scores,
                width='stretch',
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
            st.dataframe(summary_stats, width='stretch')
        
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
                st.dataframe(pd.DataFrame(improvement_data), width='stretch', hide_index=True)
            
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
                                "Generation": gen.generation + 1,  # 1-indexed
                                "Best Fitness": f"{best_fitness:.4f}",
                                "Avg Fitness": f"{avg_fitness:.4f}",
                                "Population": len(gen.candidates),
                                "Improvement": f"{improvement:.4f}"
                            })
                            prev_best_fitness = best_fitness
                        st.dataframe(pd.DataFrame(mode_history), width='stretch', hide_index=True)
        
        with tab3:
            # ── Code Diff: initial vs best evolved ───────────────────────
            st.markdown("#### 🔀 Code Evolution Diff — Baseline vs Best Evolved")
            import difflib as _difflib

            _best_mode_for_diff = best_scores.iloc[0]["mode"] if len(best_scores) else "llm_guided"
            _evolved_code = results[_best_mode_for_diff].best_code if _best_mode_for_diff in results else ""
            _diff_lines = list(_difflib.unified_diff(
                initial_code.splitlines(keepends=True),
                _evolved_code.splitlines(keepends=True),
                fromfile="initial_code (baseline)",
                tofile=f"best_evolved ({_best_mode_for_diff})",
                lineterm="",
            ))
            if _diff_lines:
                _diff_text = "".join(_diff_lines)
                st.code(_diff_text, language="diff")
                _added   = sum(1 for l in _diff_lines if l.startswith("+") and not l.startswith("+++"))
                _removed = sum(1 for l in _diff_lines if l.startswith("-") and not l.startswith("---"))
                st.caption(f"Lines added: **{_added}** · Lines removed: **{_removed}** · Net: **{_added - _removed:+d}**")
            else:
                st.info("No code change detected — evolution converged to the initial code.")

            st.markdown("#### 📋 Side-by-Side Code View")
            _dcol1, _dcol2 = st.columns(2)
            with _dcol1:
                st.markdown("**Initial (baseline) code**")
                st.code(initial_code, language="python")
            with _dcol2:
                st.markdown(f"**Best evolved code ({_best_mode_for_diff})**")
                st.code(_evolved_code, language="python")

        with tab4:
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
                st.dataframe(op_df, width='stretch', hide_index=True)
                
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
        
        with tab5:
            # Export and download options
            st.markdown("#### 💾 Export Results")
            
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
                csv_data = df_all.to_csv(index=False)
                st.download_button(
                    label=" Download Results CSV",
                    data=csv_data,
                    file_name=f"results_{problem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download complete results data (all runs)"
                )

                # Excel download (grading requirement: Excel or .csv)
                import io as _io_xl
                try:
                    _xl_buf = _io_xl.BytesIO()
                    df_all.to_excel(_xl_buf, index=False, engine="openpyxl")
                    st.download_button(
                        label=" Download Results Excel",
                        data=_xl_buf.getvalue(),
                        file_name=f"results_{problem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Download complete results as Excel workbook",
                    )
                except Exception:
                    st.caption("Excel export unavailable (install openpyxl)")
            
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
                st.dataframe(df.head(20), width='stretch')
        
        # Final best solution - prominent display
        st.markdown("---")
        st.markdown("###  Final Best Solution")
        best_mode = best_scores.iloc[0]["mode"]
        best_fitness = best_scores.iloc[0]["fitness"]
        
        st.markdown(f"""
        <div style="background-color:#000000;border:1px solid #00ff88;border-radius:8px;padding:1.2rem;margin:1rem 0;">
            <h4 style="color:#00ff88;margin:0 0 0.6rem 0;">&#127942; Winner: {best_mode.upper().replace('_', ' ')}</h4>
            <p style="color:#ffffff;margin:0.3rem 0;"><strong style="color:#aaffcc;">Fitness Score:</strong> {best_fitness:.4f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("View Best Solution Code", expanded=True):
            st.code(results[best_mode].best_code, language="python")

# LLM Reflection section (always visible after a run or as reference)
st.markdown("---")
st.markdown("###  LLM-Based Evolution: Reflection")
st.markdown("""
The **LLM-Guided** mode uses a language model (Ollama / remote API) to propose code improvements at each 
generation instead of purely random mutations. Here is a reflection on what was observed:

**What the LLM does:**  
Given the current best candidate's code and a task prompt (e.g., *"Improve the Pacman agent to maximize 
score and survival while minimizing steps"*), the LLM generates a revised version of the code. The prompt 
is structured as a few-shot instruction that includes the parent fitness score so the model has context 
about the current performance level.

**Why it may outperform random mutation:**  
Random mutation applies syntactic perturbations (numeric tweaks, line swaps) that are semantically blind. 
The LLM encodes domain knowledge about algorithm structure—it can, for example, add smarter heuristics 
or reorder decision logic in ways that a random mutation cannot. This targeted exploration reduces wasted 
evaluations on invalid or clearly regressive variants.

**Observed limitations:**  
- LLM outputs are non-deterministic; the same prompt can yield different code each call.  
- The model can hallucinate syntax errors or semantically incorrect code, which the evaluator penalizes.  
- Without fine-tuning on Pacman/matrix domains, improvement is incremental rather than dramatic.  
- Latency per LLM call is higher than a random mutation, making it slower per generation.

**Comparison of 3 methods:**  
| Method | Exploration | Domain Knowledge | Speed | Typical Outcome |
|---|---|---|---|---|
| No Evolution | None (baseline) | None | Fastest | Constant fitness |
| Random Mutation | Broad, random | None | Fast | Gradual improvement |
| LLM-Guided | Focused, semantic | High | Slow | Best final fitness |
""")

# Future improvements section
st.markdown("---")
st.markdown("###  Future Improvements")
st.markdown("""
Based on our experiments, the following directions offer the most promising paths forward:

1. **Multi-objective Pareto evolution** — instead of a single scalar fitness, maintain a Pareto front across 
   objectives (score, survival, efficiency) so the system does not sacrifice one dimension to optimize another.

2. **Fine-tuned LLM for code evolution** — fine-tune a small model specifically on Pacman/algorithm 
   improvement pairs to reduce hallucinations and increase the hit-rate of beneficial mutations.

3. **Self-adaptive hyperparameters** — evolve the mutation rate, population size, and top-k alongside the 
   candidate code (meta-evolution / CMA-ES style adaptation) rather than using a fixed schedule.

4. **Diversity preservation** — add a novelty/crowding penalty to prevent premature convergence to a local 
   optimum when multiple candidates collapse to identical code.

5. **Parallel evaluation** — run candidate evaluations concurrently (multiprocessing or async) to 
   dramatically reduce wall-clock time per generation.

6. **Memory-augmented LLM prompts** — include a rolling summary of the best N historical candidates and 
   their fitness in the LLM prompt so the model can reason about the optimization trajectory rather than 
   improving each candidate independently.
""")

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
