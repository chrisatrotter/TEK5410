\* Germany_2035_Flexibility *\
Maximize
OBJ: 40.2440585083 BESS_Effect - 0.0512 BESS_GW + 1.00605146271 DSM_Ind_GW
 + 1.00600146271 DSM_Pros_GW
Subject To
bess_max: BESS_Effect <= 0.7
bess_scale: BESS_Effect - 0.0666666666667 BESS_GW <= 0
dsm_max: 0.025 DSM_Ind_GW + 0.025 DSM_Pros_GW <= 0.3
total_max: BESS_Effect + 0.025 DSM_Ind_GW + 0.025 DSM_Pros_GW <= 0.95
Bounds
 BESS_Effect <= 0.7
 BESS_GW <= 20
 DSM_Ind_GW <= 12
 DSM_Pros_GW <= 4
End
