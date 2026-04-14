# Student Data Collection Guide for Round 2 Submission

## Overview

This guide explains how each group member should collect their individual experimental data for the AOA Project Round 2 submission (due 04/13/2026).

## Requirements

Each group member must:
1. Run experiments with **one unique parameter configuration**
2. Collect detailed data including:
   - Runtime performance
   - Steps per generation
   - Generation count
   - Fitness scores across iterations
   - Comparative plots with analysis
3. Submit two files:
   - `student_name_data.csv` - Raw experimental data
   - `student_name_data.docx` - Analysis document with screenshots

## Quick Start

### Step 1: Choose Your Configuration

Each group member should pick a **different** configuration ID (1-8):

| Config ID | Name | Description | Parameters |
|-----------|------|-------------|------------|
| 1 | Fast Exploration | High mutation, aggressive exploration | gens=8, pop=6, k=2, mut=0.6 |
| 2 | Balanced Standard | Default balanced configuration | gens=10, pop=8, k=3, mut=0.35 |
| 3 | Conservative | Low mutation, careful refinement | gens=12, pop=10, k=4, mut=0.2 |
| 4 | Elite-Focused | Large elite selection | gens=10, pop=12, k=6, mut=0.3 |
| 5 | Rapid Evolution | Quick evolution, few generations | gens=5, pop=10, k=3, mut=0.5 |
| 6 | Deep Search | Extended evolution, many gens | gens=15, pop=8, k=3, mut=0.4 |
| 7 | Small Population | Minimal population | gens=10, pop=5, k=2, mut=0.45 |
| 8 | Large Population | Diverse large population | gens=8, pop=15, k=5, mut=0.35 |

### Step 2: Run Data Collection

```bash
# Replace "Your Name" with your actual name
# Replace 1 with your chosen config ID (1-8)
python3 collect_student_data.py --student "Your Name" --config-id 1
```

**Example:**
```bash
python3 collect_student_data.py --student "John Doe" --config-id 1
```

This will:
- Run experiments on both Pacman and Matrix problems
- Generate CSV files with all required data
- Create fitness comparison plots
- Generate detailed analysis plots
- Save everything to `./student_data/Your_Name/`

### Step 3: Generate Analysis Document

```bash
python3 generate_analysis_doc.py --student "Your Name"
```

This will create a detailed markdown report: `student_data/Your_Name/Your_Name_analysis_report.md`

### Step 4: Convert to DOCX (Required Format)

**Option A: Using Pandoc (Recommended)**
```bash
# Install pandoc if needed
brew install pandoc  # macOS
# or: sudo apt-get install pandoc  # Linux

# Convert markdown to DOCX
cd student_data/Your_Name/
pandoc Your_Name_analysis_report.md -o Your_Name_data.docx
```

**Option B: Manual Conversion**
1. Open the markdown file in any text editor
2. Copy content to Microsoft Word or Google Docs
3. The images will need to be inserted manually
4. Save as `student_name_data.docx`

**Option C: Online Converter**
- Use https://pandoc.org/try/ or similar markdown-to-docx converters

## Output Files

After running the scripts, you'll have:

```
student_data/Your_Name/
├── configuration.json                    # Experiment configuration
├── Your_Name_pacman_data.csv            # Raw Pacman data  SUBMIT THIS
├── Your_Name_matrix_data.csv            # Raw Matrix data  SUBMIT THIS
├── pacman_fitness_comparison.png         # Fitness plot
├── matrix_fitness_comparison.png         # Fitness plot
├── pacman_detailed_analysis.png          # Detailed analysis
├── matrix_detailed_analysis.png          # Detailed analysis
├── Your_Name_analysis_summary.txt        # Text summary
└── Your_Name_analysis_report.md          # Full markdown report
```

## What to Submit

For Round 2 (04/13/2026), each group member submits:

1. **CSV Files** (both):
   - `Your_Name_pacman_data.csv`
   - `Your_Name_matrix_data.csv`

2. **Analysis Document**:
   - `Your_Name_data.docx` (converted from markdown)
   - Must include screenshots/plots from the generated PNG files

## Understanding Your Results

### CSV Data Columns

Your CSV files contain:
- `mode`: Evolution mode (no_evolution, random_mutation, llm_guided)
- `generation`: Generation number (0 to max_generations-1)
- `fitness`: Overall fitness score
- `metric_*`: Individual metrics (score, steps, survival for Pacman; correct, ops for Matrix)
- `student_name`: Your name
- `config_id`: Your configuration ID
- `runtime_seconds`: Total runtime
- `timestamp`: When the experiment ran

### Interpreting Fitness Scores

**Pacman:**
- Fitness = 0.6 × score + 0.3 × survival_time - 0.1 × steps
- Higher is better
- Goal: Maximize score and survival while minimizing steps

**Matrix:**
- Fitness = 0.7 × correctness + 0.3 × (1 - normalized_ops)
- Range: 0.0 to 1.0
- Goal: Maximize correctness while minimizing operations

### Comparing Evolution Modes

1. **No Evolution (Baseline)**
   - Runs for 1 generation only
   - Shows initial code performance
   - Reference point for improvements

2. **Random Mutation**
   - Uses stochastic operators:
     - Random parameter perturbation
     - Line swapping
     - Template replacement
   - Explores solution space randomly

3. **LLM-Guided**
   - Uses language models for intelligent improvements
   - Understands problem context
   - Makes targeted optimizations

## Troubleshooting

### Problem: "command not found: python3"
**Solution:** Use `python` instead of `python3`, or install Python 3.

### Problem: "No module named 'src'"
**Solution:** Make sure you're running from the project root directory:
```bash
cd /path/to/AOA/Project
python3 collect_student_data.py --student "Your Name" --config-id 1
```

### Problem: "Error running pacman experiment"
**Solution:** Pacman files might be missing. The system will still run Matrix experiments.
Check that `./third_party/pacman/pacman.py` exists.

### Problem: Script runs very slowly
**Solution:** This is normal. Evolution can take several minutes depending on:
- Your configuration (more generations = longer runtime)
- Your computer's speed
- LLM API response times

Expected runtimes:
- Config 5 (Rapid): ~2-5 minutes
- Config 2 (Balanced): ~5-10 minutes
- Config 6 (Deep Search): ~15-20 minutes

## Tips for Analysis Document

In your DOCX document, make sure to include:

1. **Clear screenshots** of all generated plots
2. **Detailed analysis** of:
   - Why your configuration was chosen
   - What you observed in the results
   - Comparison between evolution modes
   - Impact of your specific parameters
3. **Runtime data** with explanations
4. **Fitness progression** tables and observations
5. **Conclusions** about what worked well and what didn't

## Group Coordination

To avoid conflicts:
1. Create a shared spreadsheet listing who uses which config ID
2. Each member picks a unique ID (1-8)
3. If more than 8 members, reuse IDs but modify parameters slightly
4. Share your output directory name in the group chat

## Example Workflow

```bash
# 1. Navigate to project directory
cd ~/Desktop/AOA/Project

# 2. Run data collection (takes 5-10 minutes)
python3 collect_student_data.py --student "Alice Smith" --config-id 2

# 3. Check outputs
ls -lh student_data/Alice_Smith/

# 4. Generate analysis document
python3 generate_analysis_doc.py --student "Alice Smith"

# 5. Convert to DOCX
cd student_data/Alice_Smith/
pandoc Alice_Smith_analysis_report.md -o Alice_Smith_data.docx

# 6. Verify files
ls -lh
# Should see: Alice_Smith_pacman_data.csv, Alice_Smith_matrix_data.csv, Alice_Smith_data.docx

# 7. Submit these files to Canvas
```

## Questions?

If you encounter issues:
1. Check this guide thoroughly
2. Read the error messages carefully
3. Ask in the group chat
4. Check `logs/` directory for detailed error logs
5. Run `python3 test_integration.py` to verify system health

## Submission Checklist

Before submitting, verify:

- [ ] Ran `collect_student_data.py` with your name and config ID
- [ ] Generated CSV files exist and contain data
- [ ] Generated all plots (PNG files)
- [ ] Created analysis markdown document
- [ ] Converted markdown to DOCX format
- [ ] DOCX includes all plots as images
- [ ] DOCX has detailed analysis text
- [ ] Files are named correctly: `Your_Name_data.csv` and `Your_Name_data.docx`
- [ ] Submitted to Canvas before deadline (04/13/2026, 11:59 PM)

Good luck! 
