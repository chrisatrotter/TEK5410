Sets
    tech "Technologies" /wind "Onshore wind", gas "Natural gas", smr "SMR nuclear", hydro "Hydro power"/;

Parameters
    lcoe(tech) "LCOE in $/MWh"
        /wind 150, gas 100, smr 400, hydro 160/
    emis_fact(tech) "Emission factor in tCO2e/MWh"
        /wind 0, gas 0.2, smr 0, hydro 0/
    demand "Annual demand in GWh" /4000/
    max_emis "Max emissions in tCO2e" /100000/
    max_wind "Max wind generation in GWh" /1200/
    min_smr "Min SMR generation in GWh" /200/;

Positive Variables
    gen(tech) "Annual generation by technology in GWh";

Free Variable
    total_cost "Total system cost in $";

Equations
    eq_obj "Objective: minimize total cost"
    eq_demand "Meet or exceed demand"
    eq_emissions "Emissions limit"
    eq_wind_max "Wind generation limit"
    eq_smr_min "Minimum SMR generation";

eq_obj .. total_cost =e= sum(tech, lcoe(tech) * gen(tech) * 1000);
eq_demand .. sum(tech, gen(tech)) =g= demand;
eq_emissions .. sum(tech, emis_fact(tech) * gen(tech) * 1000) =l= max_emis;
eq_wind_max .. gen('wind') =l= max_wind;
eq_smr_min .. gen('smr') =g= min_smr;

Model liberland_energy /all/;

Solve liberland_energy using lp minimizing total_cost;

Display gen.l, total_cost.l;