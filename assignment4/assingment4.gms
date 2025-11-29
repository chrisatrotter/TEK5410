*====================================================================
*  Assignment 4.1 - High-Electrification + Battery Storage (2024)
*====================================================================

Sets
    h                           'Hours'
    t                           'Technologies'
    stor(t)                     'Storage technology';

Alias (h, hh);

*-------------------  PARAMETERS -------------------
Parameters
    demand(h)   'Hourly demand (MW)'
    cf(t;h)     'Capacity factor (0-1)'
    a(t)        'Annuitised cost (k€/MW)'
    vom(t)      'VOM cost (€/MWh)'
    fuel(t)     'Fuel cost (€/MWh)'
    co2(t)      'CO2 intensity (tCO2/MWh)'
    eta_stor(t) 'Round-trip efficiency 0.90'
    dur_stor(t) 'Duration (h) 4 hours';

*-------------------  TABLE DATA -------------------
* Numeric table: h1..h7 rows, columns: demand, cf_wind, cf_solar, cf_gas
Table raw_data(h,*)  'Input data: demand, cf_*'
$include "baseline_data_gams.txt";

*--- Map table columns to model parameters ------------------
demand(h)     = raw_data(h,1);
cf('wind',h)  = raw_data(h,2);
cf('solar',h) = raw_data(h,3);
cf('gas',h)   = raw_data(h,4);

*--- High-Electrification: +20% demand -------------------------
demand(h) = demand(h) * 1.20;

*--- Technology costs (k€/MW annuitised) -----------------------
a('wind')  = 67.653;
a('solar') = 48.140;
a('gas')   = 52.041;
a('batt')  = 80 + 320/4;   * 80 k€/MW power + 80 k€/MWh energy (4h)

vom('wind') = 2.3;   vom('solar') = 0.01;   vom('gas') = 4.0;   vom('batt') = 0.0;
fuel('gas') = 21.6;  fuel(t)$(not sameas(t,'gas')) = 0;
co2('gas')  = 0.202; co2(t)$(not sameas(t,'gas')) = 0;

*-------------------  VARIABLES -------------------
Positive Variables
    CAP(t)      'Installed capacity (MW)'
    GEN(t,h)    'Generation (MW)'
    CHARGE(t,h) 'Charging power (MW)'
    STO(t,h)    'State-of-charge (MWh)'
    STO0(t)     'Initial SOC (MWh)';

Free Variable COST 'Total system cost (M€)';

*-------------------  EQUATIONS -------------------
Equations
    obj, bal(h), cap_lim(t,h), stor_bal(t,h), stor_soc(t,h),
    stor_pow_lim(t,h), stor_init(t);

* Objective function
obj..
    COST =e=
        sum(t, a(t)*CAP(t)) +
        sum((t,h), (vom(t)+fuel(t))*GEN(t,h)) +
        sum((t,h)$stor(t), vom(t)*CHARGE(t,h));

* Energy balance
bal(h)..
    sum(t, GEN(t,h)) + sum(t$stor(t), CHARGE(t,h)) =e= demand(h);

* Capacity limits for non-storage tech
cap_lim(t,h)$(not stor(t))..
    GEN(t,h) =l= CAP(t) * cf(t,h);

*---------------- Storage energy balance -------------------
stor_bal(t,h)$stor(t)$(ord(h)=1)..
    STO(t,h) =e= eta_stor(t)*CHARGE(t,h) - GEN(t,h);

stor_bal(t,h)$stor(t)$(ord(h)>1)..
    STO(t,h) =e= STO(t,h-1) + eta_stor(t)*CHARGE(t,h) - GEN(t,h);

* Storage energy capacity limit
stor_soc(t,h)$stor(t)..
    STO(t,h) =l= dur_stor(t) * CAP(t);

* Storage power limit
stor_pow_lim(t,h)$stor(t)..
    GEN(t,h) + CHARGE(t,h) =l= CAP(t);

* Initial SOC
stor_init(t)$stor(t)..
    STO0(t) =e= 0;

Model highRES /all/;

*====================================================================
*  CASE 1 - High-Electrification WITHOUT battery
*====================================================================
CAP.fx('batt') = 0;
solve highRES using lp minimizing COST;

Parameter res_no_batt(*,*);
res_no_batt('CAP','wind')  = CAP.l('wind');
res_no_batt('CAP','solar') = CAP.l('solar');
res_no_batt('CAP','gas')   = CAP.l('gas');
res_no_batt('COST','')     = COST.l;
res_no_batt('EMIS','')     = sum(h, co2('gas')*GEN.l('gas',h));

*====================================================================
*  CASE 2 - High-Electrification WITH optimal battery
*====================================================================
CAP.fx('batt') = NaN;    * release fixed value
CAP.lo('batt') = 0; CAP.up('batt') = +inf;
solve highRES using lp minimizing COST;

Parameter res_with_batt(*,*);
res_with_batt('CAP','wind')   = CAP.l('wind');
res_with_batt('CAP','solar')  = CAP.l('solar');
res_with_batt('CAP','gas')    = CAP.l('gas');
res_with_batt('CAP','batt')   = CAP.l('batt');
res_with_batt('COST','')      = COST.l;
res_with_batt('EMIS','')      = sum(h, co2('gas')*GEN.l('gas',h));
res_with_batt('Energy','batt')= sum(h, GEN.l('batt',h));

*====================================================================
*  Export results
*====================================================================
execute_unload 'results.gdx', res_no_batt, res_with_batt;
execute 'gdxdump results.gdx symout=res_no_batt   format=csv > res_no_batt.csv';
execute 'gdxdump results.gdx symout=res_with_batt format=csv > res_with_batt.csv';

display "=== SOLVE SUMMARY ===";
display res_no_batt, res_with_batt;
