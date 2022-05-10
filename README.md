# GREEN-strategy
The fundamental code of a multi-UAV energy efficiency optimization strategy is shown in this project. In the simulation experiment, we consider a multi-UAV communication system composed of 4 UAVs and 4 GTs. Because of the noconvex issue, we employ SCA technology to iteratively jointly optimize the initial trajectory of multiple UAVs to achieve an optimal energy-efficient trajectory design scheme.

Specially, we provide reference codes for UAV speed optimization, UAV path initialization, multi-UAV hovering locations selection, and GREEN strategy with SCA and result showing.

It is worth noting that the function named 'GREEN' is the core step in each iteration of Dinkelbach's algorithm, which is the iterative solution process after converting MAX F(X)/Y(X)---> MAX F(X)-λY(X). 
