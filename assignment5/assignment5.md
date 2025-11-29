# Transmission and scenarios

Continue the model development from the lecture and the scenario work in assignment 4:

Implement transmission in your model.
Redo your scenario from assignment 4 or create a new scenario (preferably related to your research project).
How does your proposed scenario impact transmission?
Read the results from the scenario with Python.
Create one or several figures in Python illustrating how the scenario change the model results.

# Assignment 5 – Transmission and Scenarios
*Course: Energy System Modelling*  
*Author: Christopher A. Trotter*  
*Date: 2025-11-02*

---

## 🧩 Assignment Overview

This assignment continues the model development from the lecture and builds directly upon the scenario work from **Assignment 4**.  
The goal is to introduce **transmission** into the energy system model and analyze how different transmission capacities affect the cost-optimal system configuration.

### Objectives

1. **Implement transmission in the model.**
2. **Redo or design a new scenario** (preferably related to the previous research question).
3. **Analyze how the proposed scenario impacts transmission.**
4. **Read and visualize the model results using Python**, creating figures that show how system outcomes change across scenarios.

---

## ⚙️ Step 1: Concept — Add Transmission

### Background

In the previous assignments, Germany was represented as a **single aggregated energy system node**.  
To capture spatial diversity in generation and demand, we now extend the model into **multiple interconnected zones** linked by **transmission lines**.

Each node represents a sub-region with unique renewable resource profiles and demand levels, while transmission lines allow power exchange between nodes within given capacity limits.

### Conceptual Setup

We divide Germany into two zones:

| Node | Description | Characteristics |
|------|--------------|----------------|
| **North** | Wind-rich region | High wind potential, lower demand |
| **South** | Solar-rich region | High solar potential, higher demand |

These zones are connected via a **transmission line** (`TX_NS`) with a variable capacity limit (`CAP_TX`).

---

### Model Additions

Each region `n` has its own:
- Hourly demand `DEMAND[n,h]`
- Capacity factor for wind and solar `CF[t,n,h]`
- Generation capacity variable `CAP[t,n]`
- Generation dispatch variable `GEN[t,n,h]`

Transmission introduces:
- Power flow variable `FLOW[n,m,h]` between nodes  
- Transmission capacity variable `CAP_TX[n,m]`  
- Investment cost for transmission infrastructure

---

### Power Balance Equation

For each node `n` and hour `h`:

\[
\sum_t GEN_{t,n,h} + \sum_s DISCHARGE_{s,n,h} + \sum_{m} FLOW_{m \to n,h}
= DEMAND_{n,h} + \sum_s CHARGE_{s,n,h} + \sum_{m} FLOW_{n \to m,h}
\]

This ensures that supply plus imports equals demand plus exports.

### Transmission Capacity Constraints

\[
-FLOWMAX_{n,m} \leq FLOW_{n,m,h} \leq FLOWMAX_{n,m}
\]

### Transmission Investment Cost

\[
COST_{TX} = \sum_{n,m} c_{TX} \cdot CAP_{TX,n,m}
\]

---

## 🧮 Step 3: Implementation in Python (using PuLP)
The following example demonstrates how to extend the **Assignment 4** optimization model to include two connected zones: **North** and **South** Germany.  
Each region has its own renewable potential, demand, and battery storage, connected via a single transmission corridor. The implementation can be found in `assignment5.py`.