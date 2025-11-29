# 🇩🇪 Germany Electricity System Flexibility Analysis  
### **Optimal BESS + DSM Deployment for High-VRES Integration (2024–2035)**  
**TEK5410 Research Project – University of Oslo**

This repository contains a complete Python modeling framework for analyzing **Germany’s electricity system flexibility needs** under increasing **wind and solar penetration**. The model quantifies optimal deployment of:

- **Battery Energy Storage Systems (BESS)**
- **Demand-Side Management (DSM)**
- **High VRES penetration (up to 90%)**
- **Electrification growth (100–125%)**
- **Dynamic battery cost trajectories (BNEF 2010–2035)**

The workflow generates **8760-hour profiles**, **simulates 11 scenarios**, computes **curtailment**, **flexibility effectiveness**, **economic outcomes**, and validates results with **linear programming (PuLP)**.

---

# ⭐ Key Findings (from the TEK5410 Research Report)

**Germany's 2035 high-VRES scenario requires large-scale flexibility.**  
Without BESS or DSM, an 85% VRES system generates **1,341 TWh** of annual overproduction—**76% more than annual demand**.

### 🔋 Optimal configuration (2035)
**10 GW × 8 h BESS + 10 GW DSM**  
→ **882 TWh curtailment reduction (66%)**  
→ **$20.7 billion/year net system benefit**  
→ **100% VRES utilization (vs 38% baseline)**  

### 💡 Why 8 hours?
The model’s hourly analysis shows Germany’s solar-overgeneration window is **~8 hours per day (10:00–18:00)**.  
8h BESS captures **all solar surplus** at lowest cost; 12h adds capital cost with no additional benefit.

### 📉 Battery cost threshold
Dynamic battery cost forecast (fitted to BNEF data) shows:

- 2024: **$192/kWh**  
- 2030: **$104/kWh**  
- 2035: **$64/kWh**

**Economic viability occurs at $80–100/kWh**, enabling profitable deployment by **2028**.

### 🧠 DSM synergy
Industrial + prosumer DSM shifts **~10 GW midday**, reducing peak curtailment **150 → 50 GW**.  
DSM amplifies BESS effectiveness by **20–30%**.

### 🔍 LP validation  
PuLP optimization (same inputs) finds:

- **9.8 GW BESS**
- **12 GW industrial DSM**

→ **$37.7B annual benefit**  
→ Confirms model structure + shows value of continuous optimization.

---

# 📁 Repository Structure

```
research-report/
├── code/                     # All scenario and optimization scripts
│   ├── data/                 # Inputs used by the model
│   ├── germany_scenarios.py  # Main scenario engine (8760h simulation)
│   ├── germany_flexibility_optimization_pulp.py  # LP optimization
│   ├── utils.py
│   ├── requirements.txt
│   ├── results/              # Hourly profiles and aggregated outputs
│   ├── plots/                # Generated figures (profiles, DSM, costs)
│   └── scripts/              # Preprocessing utilities
│
├── data/                     # Raw IEA & Energy-Charts datasets
├── figures/                  # Static figures (IEA, BNEF, cost trends)
├── readings/                 # Reference papers & background material
├── TEK5410_research_project.pdf
├── IEA_Germany2025.pdf
└── README.md
```

---

# 🚀 How to Run the Model

### 1. Install Dependencies
```bash
pip install -r code/requirements.txt
```

### 2. Run the Scenario Engine (8760h simulation)
```bash
python code/germany_scenarios.py
```

This will:

- Load IEA 2024 demand & generation data  
- Load dynamic BESS cost trajectory (2024–2035)  
- Generate hourly demand, VRES, DSM profiles  
- Evaluate 11 scenarios  
- Produce plots + CSV outputs  

### 3. (Optional) Run LP Optimization
```bash
python code/germany_flexibility_optimization_pulp.py
```

---

# 📊 Outputs

### ✔ Scenario Results
- VRES utilization & curtailment  
- Net economic benefit  
- Optimal BESS + DSM mix  
- Annual/weekly/daily profiles  

### ✔ Generated Files
Located in `code/results/`:

- `demand_2035.csv`  
- `vres_2035.csv`  
- `effective_demand_2035.csv`  
- `dsm_2035.csv`  
- `curtailment_2035.csv`

### ✔ Plots  
Saved in `code/plots/`:

- Daily/weekly/annual profiles  
- Curtailment curves  
- DSM activity  
- Battery cost forecast  
- Deployment comparisons  
- LP optimization outputs  

---

# 🧠 Model Overview

### 1. **Demand Modeling**
- Based on IEA 2024 baseline  
- 2% annual growth + electrification (1.00–1.25×)  
- Seasonal, diurnal, and weekly structure  
- Noise + load-floor enforcement  

### 2. **VRES Modeling**
Wind/solar mix: **60% onshore, 20% offshore, 20% solar**  
Capacity scaled to meet target VRES share + **10% overbuild**.

### 3. **DSM Module**
Two segments:

- **Industrial (6–12 GW)** — weekday, business-hour availability  
- **Prosumer (2–4 GW)** — evening + weekend bias  

Max DSM = **18% of demand** with **85% utilization**.

### 4. **BESS Effectiveness Model**
Effectiveness = function of **power capacity (GW)** and **duration (h)**:

- Scales up to **15 GW saturation**
- Duration saturates at **8 hours**
- Max practical impact: **70% curtailment reduction**

### 5. **Economic Model**
- BESS cost based on dynamic 2010–2035 BNEF curve  
- Annualized via 10% capital recovery  
- DSM cost differentiation: industrial vs prosumer  
- Curtailment avoidance valued at **$30/MWh**  

---

# 🔬 Scenario Summary (11 simulations)

| Scenario | Year | VRES | Elec. | BESS | DSM | Curtailment↓ | Net Benefit |
|---------|------|------|-------|------|------|---------------|-------------|
| Hybrid 8h (Optimal) | 2035 | 85% | 120% | 10 GW × 8h | 10 GW | **882 TWh** | **$20.7B** |
| Early Deploy | 2028 | 70% | 110% | 8 GW × 6h | 8 GW | 555 TWh | $11.8B |
| Mid Deploy | 2032 | 80% | 115% | 12 GW | 13 GW | 917 TWh | $19.8B |
| Aggressive 8h | 2035 | 90% | 125% | 15 GW × 8h | 16 GW | 876 TWh | $16.8B |

---

# 🧪 Validation (Linear Programming – PuLP)

LP optimization verifies the heuristic and reveals optimal continuous values:

- **9.8 GW BESS**
- **12 GW industrial DSM**
- **$37.7B net benefit**

Confirms: correct scaling rules, duration choice, and industrial DSM effectiveness.

---

# 📚 References & Readings
All references, IEA reports, and literature used in the analysis are included in the `readings/` folder.  
The full research report is here: **`report/TEK5410_report.pdf`**

---

# 📞 Contact  
**Christopher A. Trotter**  
Department of Mathematics, University of Oslo  
📧 chrisatrotter@gmail.com