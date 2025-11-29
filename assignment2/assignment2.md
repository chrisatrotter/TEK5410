# Assignment 2: Optimization of Liberland's Future Energy System  

In this second assignment, we will be focusing on the mathematical formulation and GAMS implementation of an optimal electricity generation mix for the Free Republic of Liberland.

The objective is to **minimize the total cost of electricity generation** while satisfying constraints on demand, emissions, and technology-specific requirements. The analysis involves:

1. Extracting relevant information from the assignment text,  
2. Structuring the optimization problem mathematically,  
3. Implementing it in GAMS, and  
4. Verifying the results against problem requirements.  

## Problem Description  
The Free Republic of Liberland, a micronation between Croatia and Serbia, seeks to design a future energy system to meet a projected **annual electricity demand of at least 4,000 GWh**.  

Four technologies are considered:  

- Onshore wind  
- Natural gas  
- Small modular nuclear reactors (SMR)  
- Run-of-river hydro power  

### Technology Data  

| Technology   | LCOE ($/MWh) | Emission Factor (tCO₂e/MWh) |
|--------------|--------------|------------------------------|
| Onshore Wind | 150          | 0                            |
| Natural Gas  | 100          | 0.2                          |
| SMR (Nuclear)| 400          | 0                            |
| Hydro Power  | 160          | 0                            |  

### Constraints  
- **Demand constraint:** Total generation ≥ 4,000 GWh  
- **Emissions constraint:** Annual CO₂ emissions ≤ 100,000 tCO₂e  
- **Wind limit:** Wind generation ≤ 1,200 GWh  
- **SMR minimum:** SMR generation ≥ 200 GWh  
- **Non-negativity:** Generation values ≥ 0  


## Mathematical Formulation  

### Decision Variables  
- $(w)$: Onshore wind generation (GWh)  
- $(g)$: Natural gas generation (GWh)  
- $(n)$: SMR generation (GWh)  
- $(h)$: Hydro generation (GWh)  

### Objective Function  
The cost is based on **LCOE × generation × 1,000**, since LCOE is in $/MWh and generation is in GWh:  

$$
\min Z = 1000 \, \big( 150 \cdot w + 100 \cdot g + 400 \cdot n + 160 \cdot h \big), \quad w, g, n, h \ge 0
$$

### Constraints  

1. **Demand constraint:**  
$$
w + g + n + h \;\; \ge \;\; 4000 \;\text{GWh}, \quad w, g, n, h \ge 0
$$

2. **Emissions constraint (only natural gas emits):**  
$$
0.2 \;\text{tCO₂e/MWh} \times 1000 \;\text{MWh/GWh} \times g \;\le\; 100{,}000 \;\text{tCO₂e} 
\quad \Rightarrow \quad g \;\le\; 500 \;\text{GWh}
$$

3. **Wind generation limit:**  
$$
w \;\leq\; 1200 \;\text{GWh}, \quad w \ge 0
$$

4. **SMR minimum requirement:**  
$$
n \;\geq\; 200 \;\text{GWh}, \quad n \ge 0
$$

5. **Non-negativity:**  
$$
w, g, n, h \;\geq\; 0 \;\text{GWh}
$$



## GAMS Implementation  
As part of the assignment, there will also be a file included for the GAMS implementation, the file is called `assignment2.gms`.

## Conclusion

The optimization analysis demonstrates that the **most cost-efficient and feasible energy system for Liberland** consists of a careful combination of wind, natural gas, SMR, and hydro power. Using **linear programming**, the model ensures that the **annual electricity demand of 4,000 GWh is fully met**, greenhouse gas emissions are kept **within the 100,000 tCO₂e limit**, and technology-specific requirements are satisfied, including the **maximum wind generation of 1,200 GWh** and the **minimum SMR generation of 200 GWh**.

The **optimal generation mix** prioritizes the lowest-cost technologies while respecting these constraints:

| Technology | Generation (GWh) |
| ---------- | ---------------- |
| Wind       | 1200             |
| Gas        | 500              |
| SMR        | 200              |
| Hydro      | 2100             |

This allocation achieves a **total system cost of \$646 million**, calculated as:

$$
\begin{aligned}
Z &= 1000 \cdot (150 \cdot 1200 + 100 \cdot 500 + 400 \cdot 200 + 160 \cdot 2100) \\
  &= 1000 \cdot (180{,}000 + 50{,}000 + 80{,}000 + 336{,}000) \\
  &= 646{,}000{,}000 \;\text{USD}
\end{aligned}
$$

This result confirms that the **proposed generation mix represents the optimal design** for Liberland’s electricity system under the given assumptions. The solution effectively **balances cost, environmental limits, and technological constraints**, demonstrating that:

* **Wind power** contributes the maximum feasible amount to leverage renewable energy without exceeding aesthetic or land-use limitations.
* **Natural gas** provides cost-efficient flexibility within the emissions cap.
* **SMR** meets the minimum required level to support Liberland’s interest in nuclear technology despite its high cost.
* **Hydro power** fills the remaining demand to ensure full coverage of electricity needs.

In conclusion, this assignment identifies a **practical, implementable, and optimal strategy** for Liberland’s energy system, ensuring a **cost-effective, environmentally compliant, and reliable electricity supply**. The approach can serve as a blueprint for **future energy planning** in small-scale systems with similar constraints.
