#!/usr/bin/env python3
# germany_scenarios.py
"""
Germany Electricity System Scenarios for TEK5410
BESS + DSM Flexibility Evaluation (USD)
Dynamic BESS Cost Forecast 2024-2035 Integration
Author: Christopher A. Trotter
"""

import pandas as pd
import numpy as np
import os, sys
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = "png"

# =============================================================================
# GLOBAL CONSTANTS
# =============================================================================
HOURS = 8760
CURTAILMENT_VALUE_USD_MWH = 30  # $30/MWh avoided curtailment

# =============================================================================
# LOAD DYNAMIC BESS COST FORECAST
# =============================================================================
def load_bess_cost_forecast(csv_path='data/battery_cost_forecast.csv'):
    """Load dynamic BESS cost forecast 2024-2035"""
    try:
        df = pd.read_csv(csv_path)
        df['Year'] = df['Year'].astype(int)
        df['Predicted_Cost_USD_per_kWh'] = pd.to_numeric(df['Predicted_Cost_USD_per_kWh'], errors='coerce')
        
        print(f"🔋 BESS COST FORECAST LOADED:")
        print(df[['Year', 'Predicted_Cost_USD_per_kWh']].to_string(index=False))
        
        return df.set_index('Year')['Predicted_Cost_USD_per_kWh'].to_dict()
    except Exception as e:
        print(f"⚠️  BESS forecast error: {e}")
        sys.exit(1) # requires forcast data.

# =============================================================================
# LOAD IEA ELECTRICITY DATA
# =============================================================================
def load_iea_data(csv_path='data/germany_electricity_supply.csv'):
    try:
        print(f"📂 Loading IEA 2024 data: {csv_path}")
        df = pd.read_csv(csv_path)
        
        if df.shape[1] == 4:
            df.columns = ['technology', 'value', 'year', 'units']
        else:
            df = df.iloc[1:].reset_index(drop=True)
            df.columns = ['technology', 'value', 'year', 'units']
        
        df['technology'] = df['technology'].str.strip().str.replace('"', '')
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna(subset=['value', 'year'])
        
        df_2024 = df[df['year'] == 2024].copy()
        
        generation = {}
        tech_mapping = {
            'Coal': 'Coal', 'Natural gas': 'Natural gas', 'Wind': 'Wind',
            'Solar PV': 'Solar PV', 'Hydropower': 'Hydropower', 'Biofuels': 'Biofuels',
            'Waste': 'Waste', 'Geothermal': 'Geothermal', 'Other sources': 'Other sources',
            'Oil': 'Oil', 'Nuclear': 'Nuclear'
        }
        
        for tech, exact_name in tech_mapping.items():
            mask = df_2024['technology'] == exact_name
            if mask.any():
                generation[tech] = float(df_2024[mask]['value'].iloc[0])
        
        total_gen_gwh = sum(generation.values())
        vres_gwh = generation.get('Wind', 0) + generation.get('Solar PV', 0)
        vres_share = vres_gwh / total_gen_gwh if total_gen_gwh > 0 else 0
        
        print(f"\n✅ 2024 SUMMARY:")
        print(f"   Total: {total_gen_gwh/1000:.0f} TWh | VRES: {vres_share:.1%}")
        
        return generation, total_gen_gwh / 1000, vres_share
        
    except Exception as e:
        print(f"❌ IEA data error: {e}")
        sys.exit(1) # requires IEA data.

# =============================================================================
# SCENARIO MODEL WITH DYNAMIC BESS COSTS
# =============================================================================
class GermanyScenarios:
    def __init__(self):
        self.generation_2024, self.demand_2024_twh, self.vres_share_2024 = load_iea_data()
        self.bess_cost_forecast = load_bess_cost_forecast()
        
        print(f"\n✅ MODEL READY")
        print(f"   Demand 2024: {self.demand_2024_twh:.0f} TWh")
        print(f"   BESS 2035: ${self.bess_cost_forecast[2035]:.0f}/kWh")
        print(f"   Cost drop 2024→2035: {((192-self.bess_cost_forecast[2035])/192*100):.0f}%")

    def get_bess_cost(self, year):
        """Get year-specific BESS cost from forecast"""
        return self.bess_cost_forecast.get(year, self.bess_cost_forecast[2035])

    def generate_demand_profile(self, year, electrification_factor=1.0):
        t = np.arange(HOURS)
        seasonal = 0.20 * np.sin(2 * np.pi * t / HOURS)
        daily = 0.25 * np.sin(2 * np.pi * (t % 24) / 24)
        weekly = 0.10 * np.sin(2 * np.pi * t / (HOURS/7) + np.pi)
        
        profile = 1.0 + seasonal + daily + weekly + 0.04 * np.random.randn(HOURS)
        profile = np.maximum(profile, 0.45)
        
        annual_twh = self.demand_2024_twh * (1.02 ** (year - 2024)) * electrification_factor
        avg_mw = annual_twh * 1e6 / HOURS
        return pd.Series(avg_mw * (profile / profile.mean()), 
                        index=pd.date_range(f'{year}-01-01', periods=HOURS, freq='h'))

    def vres_profile(self, year, vres_target, electrification_factor=1.0):
        demand = self.generate_demand_profile(year, electrification_factor)
        total_demand_twh = demand.sum() / 1e6
        vres_capacity_gw = (total_demand_twh / vres_target) * 1.10
        
        mix = {'wind_onshore': 0.60, 'wind_offshore': 0.20, 'solar_pv': 0.20}
        capacities = {k: v * vres_capacity_gw for k, v in mix.items()}
        
        t = np.arange(HOURS)
        cfs = {}
        cfs['wind_onshore'] = 0.28 * (0.90 + 0.20 * np.sin(2*np.pi*t/HOURS + np.pi/2))
        cfs['wind_onshore'] += 0.10 * np.sin(2*np.pi*(t%24)/24 + np.pi/3)
        cfs['wind_offshore'] = 0.45 * (0.95 + 0.15 * np.sin(2*np.pi*t/HOURS))
        
        solar_daily = np.maximum(0, np.sin(np.pi * (t % 24) / 12))
        solar_seasonal = 1 + 0.40 * np.sin(2 * np.pi * t / HOURS + np.pi / 2)
        cfs['solar_pv'] = 0.11 * solar_daily * solar_seasonal
        
        total_vres = sum(capacities[tech] * 1000 * cfs[tech] for tech in capacities)
        return pd.Series(total_vres, index=demand.index), total_demand_twh, vres_capacity_gw

    def dsm_profile(self, demand, dsm_ind_gw, dsm_pros_gw):
        t = np.arange(HOURS)
        weekday = 0.7 + 0.3 * np.sin(2 * np.pi * t / (HOURS/7) + np.pi)
        business = np.maximum(0, np.sin(np.pi * ((t % 24) - 13) / 5))
        ind_profile = np.maximum(0.35, weekday * business * 1.2)
        
        evening = np.maximum(0, np.sin(np.pi * ((t % 24) - 19) / 3))
        weekend = 1 + 0.4 * (1 + np.sin(2 * np.pi * t / (HOURS/7)))
        pros_profile = np.maximum(0.25, evening * weekend)
        
        dsm_ind = np.minimum(dsm_ind_gw * 1000 * ind_profile, demand * 0.12)
        dsm_pros = np.minimum(dsm_pros_gw * 1000 * pros_profile, demand * 0.06)
        return pd.Series(0.85 * (dsm_ind + dsm_pros), index=demand.index)

    def run_scenario(self, scenario_name, year=2035, electrification_factor=1.0, 
                     vres_target=0.80, bess_gw=0, dsm_ind_gw=0, dsm_pros_gw=0, bess_duration=4):
        """Run scenario with year-specific BESS costs"""
        
        bess_cost_kwh = self.get_bess_cost(year)
        
        vres_gen, total_demand_twh, vres_capacity_gw = self.vres_profile(
            year, vres_target, electrification_factor
        )
        demand = self.generate_demand_profile(year, electrification_factor)
        
        # Baseline curtailment
        curtailment_no_flex = np.maximum(0, vres_gen - demand).sum() / 1e6
        vres_util_no_flex = min(100, (vres_gen.sum() - curtailment_no_flex * 1e6) / total_demand_twh * 100)
        
        # DSM
        if dsm_ind_gw > 0 or dsm_pros_gw > 0:
            dsm_shift = self.dsm_profile(demand, dsm_ind_gw, dsm_pros_gw)
            effective_demand = demand - dsm_shift
        else:
            effective_demand = demand
        
        raw_curtailment = np.maximum(0, vres_gen - effective_demand).sum() / 1e6
        
        # BESS effectiveness (GW + duration dependent)
        max_effect = min(0.70, bess_gw / 15.0)
        duration_factor = min(1.0, bess_duration / 8.0)
        bess_effectiveness = max_effect * duration_factor
        
        curtailment_flex = raw_curtailment * (1 - bess_effectiveness)
        vres_util_flex = min(100, (vres_gen.sum() - curtailment_flex * 1e6) / total_demand_twh * 100)
        
        # Economics with DYNAMIC BESS costs
        bess_gwh = bess_gw * bess_duration
        bess_cap_cost = bess_gwh * bess_cost_kwh * 1e6 / 1e9  # $B
        bess_annual_cost = bess_cap_cost * 0.10
        
        dsm_annual_cost = ((dsm_ind_gw * 1000 * 50) + (dsm_pros_gw * 1000 * 100)) * HOURS / 1e9
        
        savings_twh = curtailment_no_flex - curtailment_flex
        savings_usd = savings_twh * CURTAILMENT_VALUE_USD_MWH * 1e6 / 1e9
        
        total_cost = bess_annual_cost + dsm_annual_cost
        net_benefit = savings_usd - total_cost
        
        return {
            'scenario': scenario_name,
            'year': year,
            'bess_cost_kwh': round(bess_cost_kwh, 0),
            'electrification': f"{electrification_factor:.0%}",
            'vres_target': f"{vres_target:.0%}",
            'demand_twh': round(total_demand_twh, 0),
            'vres_capacity_gw': round(vres_capacity_gw, 0),
            'bess_gw': round(bess_gw, 1),
            'bess_duration_h': bess_duration,
            'bess_gwh': round(bess_gwh, 1),
            'dsm_ind_gw': dsm_ind_gw,
            'dsm_pros_gw': dsm_pros_gw,
            'curtailment_no_flex_twh': round(curtailment_no_flex, 1),
            'curtailment_flex_twh': round(curtailment_flex, 1),
            'curtailment_reduction_twh': round(savings_twh, 1),
            'vres_util_no_flex': f"{vres_util_no_flex:.0f}%",
            'vres_util_flex': f"{vres_util_flex:.0f}%",
            'bess_cap_cost_busd': round(bess_cap_cost, 2),
            'bess_annual_cost_busd': round(bess_annual_cost, 2),
            'dsm_annual_cost_busd': round(dsm_annual_cost, 2),
            'curtailment_savings_busd': round(savings_usd, 2),
            'total_cost_busd': round(total_cost, 2),
            'net_benefit_busd': round(net_benefit, 2),
            'bess_effectiveness_pct': round(bess_effectiveness * 100, 1)
        }

    def run_all_scenarios(self):
        """Multi-year scenarios with dynamic BESS costs"""
        scenarios = [
            # Baseline scenarios (no flexibility)
            ('2024_Baseline', 2024, 1.00, 0.421, 0, 0, 0, 4),
            ('2030_Conservative', 2030, 1.10, 0.65, 0, 0, 0, 4),
            ('2030_80VRES', 2030, 1.15, 0.80, 0, 0, 0, 4),
            
            # 🔥 2035 Optimal Hybrid (varying BESS duration)
            ('2035_Hybrid_4h', 2035, 1.20, 0.85, 10, 8, 2, 4),
            ('2035_Hybrid_8h', 2035, 1.20, 0.85, 10, 8, 2, 8),
            ('2035_Hybrid_12h', 2035, 1.20, 0.85, 10, 8, 2, 12),
            
            # 🔥 2035 Aggressive (varying BESS duration)
            ('2035_Aggressive_4h', 2035, 1.25, 0.90, 15, 12, 4, 4),
            ('2035_Aggressive_8h', 2035, 1.25, 0.90, 15, 12, 4, 8),
            ('2035_Aggressive_12h', 2035, 1.25, 0.90, 15, 12, 4, 12),
            
            # 🔥 Bonus: Earlier deployment scenarios
            ('2028_Early_Deploy', 2028, 1.10, 0.70, 8, 6, 2, 6),
            ('2032_Mid_Deploy', 2032, 1.15, 0.80, 12, 10, 3, 8),
        ]
        
        print("\n🔍 RUNNING MULTI-YEAR SCENARIOS...")
        results = []
        for name, yr, elec, vres_t, bess, dsm_ind, dsm_pros, bess_dur in scenarios:
            bess_cost = self.get_bess_cost(yr)
            print(f"   {name} ({yr}) | BESS: ${bess_cost:.0f}/kWh")
            result = self.run_scenario(name, yr, elec, vres_t, bess, dsm_ind, dsm_pros, bess_dur)
            results.append(result)
        
        return pd.DataFrame(results)

    def save_profiles(self):
        os.makedirs('results', exist_ok=True)
        os.makedirs('plots/profiles', exist_ok=True)
        
        # 2035 Optimal profiles
        demand = self.generate_demand_profile(2035, 1.20)
        vres_gen, demand_twh, vres_gw = self.vres_profile(2035, 0.85, 1.20)
        dsm = self.dsm_profile(demand, 8, 2)
        
        # Calculate effective demand and curtailment for plotting
        effective_demand = demand - dsm
        curtailment = np.maximum(0, vres_gen - effective_demand)
        
        # Helper function to save with timestamp column
        def save_csv_with_timestamp(df, filename, col_name):
            df_reset = df.reset_index()
            df_reset.columns = ['timestamp', col_name]
            df_reset.to_csv(f'results/{filename}', index=False)
        
        # Save CSV data WITH TIMESTAMP AND DESCRIPTIVE HEADERS
        save_csv_with_timestamp(demand, 'demand_2035.csv', 'Germany_2035_Hourly_Demand_MW')
        save_csv_with_timestamp(vres_gen, 'vres_2035.csv', 'Germany_2035_VRES_Generation_MW')
        save_csv_with_timestamp(dsm, 'dsm_2035.csv', 'Germany_2035_DSM_Flexibility_MW')
        save_csv_with_timestamp(effective_demand, 'effective_demand_2035.csv', 'Germany_2035_Effective_Demand_MW')
        save_csv_with_timestamp(curtailment, 'curtailment_2035.csv', 'Germany_2035_Curtailment_MW')
        
        # PLOT 1: Annual Profile Overview
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=demand.index, y=demand/1000, name='Demand', line=dict(color='blue', width=2)))
        fig1.add_trace(go.Scatter(x=demand.index, y=vres_gen/1000, name='VRES Generation', line=dict(color='green', width=2)))
        fig1.add_trace(go.Scatter(x=demand.index, y=effective_demand/1000, name='Effective Demand (w/ DSM)', 
                                 line=dict(color='purple', width=2, dash='dash')))
        fig1.add_trace(go.Scatter(x=demand.index, y=curtailment/1000, name='Curtailment', 
                                 line=dict(color='red', width=2), fill='tonexty'))
        
        fig1.update_layout(
            title=f'Germany 2035: Demand vs VRES + Flexibility<br><sup>{demand_twh:.0f} TWh Demand | {vres_gw:.0f} GW VRES</sup>',
            xaxis_title='Time (Hour)', yaxis_title='Power (GW)',
            height=500, width=1400, template='plotly_white',
            showlegend=True, legend=dict(x=0.02, y=0.98)
        )
        fig1.write_image('plots/profiles/annual_overview_2035.png', scale=2)
        
        # PLOT 2: Weekly Profile (Week 26 - peak summer)
        week_start = pd.Timestamp('2035-07-01 00:00')
        week_data = slice(24*7*25, 24*7*26)  # Week 26
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=demand.index[week_data], y=demand.iloc[week_data]/1000, 
                                 name='Demand', line=dict(color='blue', width=3)))
        fig2.add_trace(go.Scatter(x=demand.index[week_data], y=vres_gen.iloc[week_data]/1000, 
                                 name='VRES', line=dict(color='gold', width=3)))
        fig2.add_trace(go.Scatter(x=demand.index[week_data], y=effective_demand.iloc[week_data]/1000, 
                                 name='w/ DSM', line=dict(color='purple', width=3, dash='dot')))
        fig2.add_trace(go.Scatter(x=demand.index[week_data], y=curtailment.iloc[week_data]/1000, 
                                 name='Curtailment', line=dict(color='red', width=3), 
                                 fill='tonexty', fillcolor='rgba(255,0,0,0.2)'))
        
        fig2.update_layout(
            title='Germany 2035: Peak Summer Week (Week 26)',
            xaxis_title='Time', yaxis_title='Power (GW)',
            height=500, width=1400, template='plotly_white'
        )
        fig2.write_image('plots/profiles/weekly_summer_2035.png', scale=2)
        
        # PLOT 3: Daily Profile (Peak Summer Day)
        day_start = pd.Timestamp('2035-07-15 00:00')
        day_data = slice(24*183, 24*184)  # July 15
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=demand.index[day_data], y=demand.iloc[day_data]/1000, 
                                 name='Demand', line=dict(color='blue', width=4)))
        fig3.add_trace(go.Scatter(x=demand.index[day_data], y=vres_gen.iloc[day_data]/1000, 
                                 name='VRES', line=dict(color='gold', width=4)))
        fig3.add_trace(go.Scatter(x=demand.index[day_data], y=effective_demand.iloc[day_data]/1000, 
                                 name='w/ DSM', line=dict(color='purple', width=4, dash='dot')))
        fig3.add_trace(go.Scatter(x=demand.index[day_data], y=curtailment.iloc[day_data]/1000, 
                                 name='Curtailment', line=dict(color='red', width=4), 
                                 fill='tonexty', fillcolor='rgba(255,0,0,0.3)'))
        
        fig3.update_layout(
            title='Germany 2035: Peak Summer Day (July 15)',
            xaxis_title='Hour of Day', yaxis_title='Power (GW)',
            height=500, width=1000, template='plotly_white'
        )
        fig3.write_image('plots/profiles/daily_peak_2035.png', scale=2)
        
        # PLOT 4: DSM Profile
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=demand.index, y=dsm/1000, name='DSM Shift', 
                                 line=dict(color='orange', width=3)))
        fig4.add_trace(go.Scatter(x=demand.index, y=demand/1000, name='Total Demand', 
                                 line=dict(color='blue', width=2), opacity=0.7))
        
        fig4.update_layout(
            title='DSM Flexibility Profile (10 GW total)',
            xaxis_title='Time (Hour)', yaxis_title='Power (GW)',
            height=500, width=1400, template='plotly_white'
        )
        fig4.write_image('plots/profiles/dsm_profile_2035.png', scale=2)
        
        print(f"✅ Profiles saved: {demand_twh:.0f} TWh demand")
        print("✅ Profile CSV files with headers:")
        print("   ⚡ results/demand_2035.csv (timestamp, Germany_2035_Hourly_Demand_MW)")
        print("   🌞 results/vres_2035.csv (timestamp, Germany_2035_VRES_Generation_MW)")
        print("   🔄 results/dsm_2035.csv (timestamp, Germany_2035_DSM_Flexibility_MW)")
        print("   📉 results/effective_demand_2035.csv (timestamp, Germany_2035_Effective_Demand_MW)")
        print("   ❌ results/curtailment_2035.csv (timestamp, Germany_2035_Curtailment_MW)")
        print("✅ Profile plots saved:")
        print("   📈 plots/profiles/annual_overview_2035.png")
        print("   📅 plots/profiles/weekly_summer_2035.png") 
        print("   🌞 plots/profiles/daily_peak_2035.png")
        print("   🔄 plots/profiles/dsm_profile_2035.png")

# =============================================================================
# PLOTTING FUNCTIONS
# =============================================================================
def plot_bess_cost_evolution(bess_forecast):
    """Plot BESS cost forecast"""
    fig = go.Figure()
    years = list(bess_forecast.keys())
    costs = list(bess_forecast.values())
    
    fig.add_trace(go.Scatter(x=years, y=costs, mode='lines+markers', 
                            name='BESS Cost Forecast', line=dict(color='orange', width=3)))
    
    fig.update_layout(
        title='Battery Cost Forecast 2024-2035',
        xaxis_title='Year', yaxis_title='Cost ($/kWh)',
        template='plotly_white', height=500, width=1000
    )
    fig.write_image('plots/bess_cost_forecast.png', scale=2)
    print("✅ BESS cost forecast plot saved")

def plot_flex_deployment(results_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=results_df['scenario'], y=results_df['bess_gw'], name='BESS GW'))
    dsm_total = results_df['dsm_ind_gw'] + results_df['dsm_pros_gw']
    fig.add_trace(go.Bar(x=results_df['scenario'], y=dsm_total, name='DSM GW'))
    fig.update_layout(title='Deployment', barmode='group', height=500)
    return fig

def plot_economics(results_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=results_df['scenario'], y=results_df['curtailment_savings_busd'], name='Savings'))
    fig.add_trace(go.Bar(x=results_df['scenario'], y=results_df['bess_annual_cost_busd'], name='BESS Cost'))
    fig.add_trace(go.Bar(x=results_df['scenario'], y=results_df['dsm_annual_cost_busd'], name='DSM Cost'))
    fig.add_trace(go.Bar(x=results_df['scenario'], y=results_df['net_benefit_busd'], name='Net Benefit'))
    fig.update_layout(title='Economics ($B/year)', barmode='group', height=500)
    return fig

def save_plots(results_df, bess_forecast):
    os.makedirs('plots', exist_ok=True)
    
    # BESS cost evolution
    plot_bess_cost_evolution(bess_forecast)
    
    # Scenario plots
    plots = [
        plot_flex_deployment, 
        plot_economics
    ]
    names = ['deployment', 'economics', 'utilization']
    
    for i, (plot_func, name) in enumerate(zip(plots, names)):
        fig = plot_func(results_df)
        filename = f"plots/{name}_germany.png"
        fig.write_image(filename, width=1200, height=600, scale=2)
        print(f"✅ {name}.png")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("🇩🇪 GERMANY FLEXIBILITY OPTIMIZATION")
    print("🔋 Dynamic BESS Cost Forecast | 2024-2035 Scenarios")
    print("=" * 60)
    
    # Initialize model
    model = GermanyScenarios()
    
    # Generate profiles
    model.save_profiles()
    
    # Run scenarios
    results_df = model.run_all_scenarios()
    
    # Display results
    print("\n📊 RESULTS BY YEAR & BESS DURATION")
    cols = ['scenario', 'year', 'bess_cost_kwh', 'bess_duration_h', 'bess_gwh', 
            'curtailment_reduction_twh', 'net_benefit_busd']
    print(results_df[cols].round(1).to_string(index=False))
    
    # Best scenario
    best = results_df.loc[results_df['net_benefit_busd'].idxmax()]
    print(f"\n🎯 BEST: {best['scenario']}")
    print(f"   💰 ${best['net_benefit_busd']:.1f}B/year | BESS: ${best['bess_cost_kwh']}/kWh")
    print(f"   🛡️ {best['curtailment_reduction_twh']:.1f} TWh saved")
    
    # Generate plots
    save_plots(results_df, model.bess_cost_forecast)
    
    # Export
    os.makedirs('results', exist_ok=True)
    results_df.to_csv('results/flexibility_scenarios.csv', index=False)
    
    # Summary table
    summary = results_df[['scenario', 'year', 'bess_cost_kwh', 'bess_duration_h', 
                         'curtailment_reduction_twh', 'net_benefit_busd']].round(1)
    summary.to_csv('results/summary.csv', index=False)
    
    print("\n✅ ANALYSIS COMPLETE!")
