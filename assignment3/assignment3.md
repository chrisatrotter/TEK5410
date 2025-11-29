# Electricity Demand Analysis - ENTSO-E Data

## Introduction
This project analyzes electricity demand data for **Germany** and the **United Kingdom**, sourced from the [ENTSO-E Transparency Portal](https://transparency.entsoe.eu/).  

The script processes two CSV files:  

- `Total_Load_Day_Ahead_Actual_2024_Germany.csv`  
- `Total_Load_Day_Ahead_Actual_2024_UK.csv`  

It follows the assignment requirements:  

> **Assignment**  
> - Download electricity demand data for at least two countries from the ENTSO-E Transparency Portal for the last year (2024).  
> - Combine the files into one tidy DataFrame.  
> - Ensure time and date are properly recognized.  
> - Calculate the total yearly demand of the chosen countries.  
> - Calculate the hourly total demand across countries.  
> - Identify when demand is highest and lowest.  
> - Identify any problems with the data.  
> - Describe problems and suggest potential fixes (concept only, no code needed).  

---

## Script
The script (`total_load.py`) performs the following steps:  

1. **Load CSV files** for Germany and the UK.  
2. **Rename columns** for consistency (`Forecast_DE`, `Actual_DE`, `Forecast_UK`, `Actual_UK`).  
3. **Parse datetime** strings to extract start times, convert to `datetime`, and set as index.  
4. **Convert load columns to numeric**, handling `"N/A"` values by coercing them to `NaN`.  
5. **Resample to hourly resolution** (Germany: 15-min → hourly, UK: 30-min → hourly).  
6. **Combine datasets** into one tidy DataFrame, aligning timestamps.  
7. **Calculate total yearly demand** (GWh/TWh) using the original resolution data.  
8. **Save outputs**:  
   - `tidy_combined_dataframe.csv` (hourly combined data)  
   - `hourly_total_demand.csv` (hourly total demand across both countries)  
9. **Identify demand extremes** (highest and lowest hourly demand with timestamps).  
10. **Check data quality**, including missing values, date ranges, and resolution mismatches.  

---

## Description of Problems Found
Analysis revealed several issues:  

- **Missing values**: Both actual and forecast loads contain `"N/A"`. The UK forecast is often 100% missing, reducing reliability and potentially biasing results.  
- **Temporal misalignment**: Germany uses 15-minute intervals, the UK 30-minute intervals. Without resampling, combined analysis is inaccurate.  
- **Coverage gaps**: If datasets do not cover January 1–December 31, yearly totals underestimate true demand.  
- **Timezone differences**: Germany data is CET/CEST, while UK data may be GMT/BST, causing a possible 1-hour offset.  
- **Data quality concerns**: ENTSO-E data often shows reporting delays, inconsistencies, and missing forecasts across countries.  

---

## Potential Fixes (Conceptual Only)
To address these issues:  

- **Missing values**: Use interpolation (e.g., linear or forward/backward fill) for short gaps; supplement with national operator data (e.g., National Grid ESO for the UK) for long gaps.  
- **Temporal misalignment**: Standardize to a common hourly resolution via resampling; convert UK timestamps to CET/CEST.  
- **Coverage gaps**: Verify full-year coverage and merge multiple files if necessary.  
- **Timezone handling**: Explicitly adjust UK timestamps to align with continental Europe.  
- **Data quality checks**: Cross-validate with secondary sources (Eurostat, national statistics) and document assumptions (e.g., `"N/A"` ≠ zero).  

---

## Script Notes
- **Outputs**:  
  - `tidy_combined_dataframe.csv` → Hourly aligned demand data (Germany + UK).  
  - `hourly_total_demand.csv` → Hourly total demand across both countries.  

- **For lecture discussion**:  
  - How datetime parsing and resampling align mismatched datasets.  
  - The formula for calculating energy demand (MW × hours → MWh → GWh/TWh).  
  - The importance of validating time coverage and handling missing values.  
  - Conceptual fixes for data issues before performing analysis.  
