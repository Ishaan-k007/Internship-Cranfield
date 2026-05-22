# Cranfield Internship: Aerodynamic Wing Optimisation

A parametric wing design study using OpenVSP's vortex-lattice solver (VSPAERO) coupled with Random Forest surrogate models to explore and optimise NACA four-series airfoil configurations for different mission profiles.

---

## Project Overview

The project is structured as a three-stage pipeline:

```
Stage 1 — Simulation            Stage 2 — Mission Selector        Stage 3 — Optimisation
┌───────────────────┐           ┌──────────────────────────┐    ┌──────────────────────┐
│  01_simulate.py   │ ──CSV──►  │  02_mission_selector.py  │    │  03_optimise.py      │
│                   │           │                          │    │                      │
│  OpenVSP sweep    │           │  RF surrogate + mission  │    │  SLSQP constrained   │
│  over NACA        │           │  filtering (STOL,        │    │  optimisation of     │
│  parameters       │           │  Glider, UAV, Trainer,   │    │  L/D subject to      │
│  → CL, CD, L/D    │           │  Utility)                │    │  CD ≤ 0.02           │
└───────────────────┘           └──────────────────────────┘    └──────────────────────┘
```

### Design space explored

| Parameter       | Range                     |
|----------------|---------------------------|
| Camber          | 0, 0.02, 0.04, 0.06       |
| Camber location | 0.3, 0.4, 0.5             |
| Thickness/chord | 0.09, 0.12, 0.15          |
| Span (m)        | 2, 6, 8, 12, 16           |
| Root chord (m)  | 1, 1.5, 2, 2.5, 3         |
| Tip chord (m)   | 0.2, 0.6, 1.0, 1.4, 1.8  |
| Angle of attack | 0°, 4°, 8°, 12°, 16°     |

Mach number fixed at 0.17; Reynolds number fixed at 4.46 × 10⁶.

---

## Prerequisites

### 1. OpenVSP (required for Stage 1 only)

Download **OpenVSP 3.43.0** for Windows from the [OpenVSP releases page](http://openvsp.org/):

- Extract to a known location (e.g. `C:\OpenVSP\OpenVSP-3.43.0-win64\`)
- The Python bindings are inside `<OpenVSP_root>\python\openvsp\`

> **Stages 2 and 3 do not require OpenVSP.** They only need `vspaero_results.csv`, which is already included in the repository.

### 2. Python 3.10+

Check your version:
```bash
python --version
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/Ishaan-k007/Internship-Cranfield.git
cd Internship-Cranfield
```

### Create and activate a virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration (Stage 1 only)

`myscript.py` contains two hardcoded paths that **must be updated** before running:

| Line | Variable | Purpose |
|------|----------|---------|
| 7 | `sys.path.append(...)` | Path to the OpenVSP Python module |
| 10 | `vsp.SetVSPAEROPath(...)` | Path to the VSPAERO executable |

Edit the config block at the top of `01_simulate.py` to match your OpenVSP installation:

```python
# Line 7 — point to your OpenVSP Python bindings
sys.path.append(r"C:\OpenVSP\OpenVSP-3.43.0-win64\python\openvsp")

# Line 10 — point to the VSPAERO binary directory
vsp.SetVSPAEROPath(r"C:\OpenVSP\OpenVSP-3.43.0-win64\python\openvsp\openvsp")
```

The script also writes geometry files and results to `RESULTS_DIR`. Change that variable in the config block if needed.

---

## Usage

### Stage 1 — Run the OpenVSP simulation sweep

> **Only required if you want to regenerate the dataset.** A pre-generated `vspaero_results.csv` is already included.

```bash
python 01_simulate.py
```

This sweeps all parameter combinations (~900 configurations × 5 angles of attack), calls VSPAERO for each, and writes results to `vspaero_results.csv`. Expect a long runtime.

**Output:** `vspaero_results.csv` with columns:
`Angle of attack, Span, Root Chord, Tip Chord, Camber, Camber_Loc, Thickness, CL, CD, L/D`

---

### Stage 2 — Mission-based airfoil selector

```bash
python 02_mission_selector.py
```

Trains Random Forest regressors on `vspaero_results.csv`, then enters an interactive loop where you select a mission profile and receive the top-ranked airfoil configurations.

**Available missions:**

| Mission    | Min L/D | Max CD | Min CL | Max α |
|-----------|---------|--------|--------|-------|
| STOL       | 10      | 0.045  | 0.7    | 6°    |
| Glider     | 25      | 0.035  | 0.7    | 6°    |
| UAV_Loiter | 15      | 0.035  | 0.6    | 6°    |
| Trainer    | 12      | 0.035  | 0.6    | 6°    |
| Utility    | 10      | 0.045  | 0.7    | 7°    |

**Example session:**
```
=== Mission-Based Selector ===
Enter mission (STOL, Glider, UAV_Loiter, Trainer, Utility): Glider

=== Top Airfoils for Glider ===
   Camber  Camber_Loc  Thickness  Span  Root Chord  Tip Chord  Angle of attack    CL      CD     L/D
...
Check another mission? (y/n): n
```

---

### Stage 3 — Constrained optimisation

```bash
python 03_optimise.py
```

Fits surrogate models for L/D and CD, runs an SLSQP optimisation to maximise L/D subject to CD ≤ 0.02, then enters an interactive loop for custom predictions.

**Example output:**
```
=== Optimization Result ===
Optimal Camber:    0.0423
Optimal CamberLoc: 0.4100
Optimal Thickness: 0.0952
Predicted L/D at Optimum: 18.7432
Predicted CD at Optimum:  0.01987
============================
```


---

## Repository Structure

```
Internship-Cranfield/
├── 01_simulate.py          # Stage 1: OpenVSP parametric sweep
├── 02_mission_selector.py  # Stage 2: Mission-based selector (ML)
├── 03_optimise.py          # Stage 3: Constrained optimisation (ML + SLSQP)
├── vspaero_results.csv     # Pre-generated simulation dataset (400+ rows)
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

---

## Known Limitations

- **Windows only (Stage 1):** OpenVSP Python bindings are available for Windows and Linux but the paths in `myscript.py` are Windows-specific.
- **Hardcoded paths:** `myscript.py` must be manually edited before use (see Configuration above).
- **No test suite:** Results from Stages 2 and 3 should be sanity-checked against known NACA data.
- **Dataset size:** The current CSV covers 400+ combinations; extrapolating beyond the training domain will reduce surrogate accuracy.
