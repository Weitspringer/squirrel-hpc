"""Contains the carbon coefficients [gCO2eq / kWh] of different fuels in power generation of various countries.

Hydro, geothermal, wind, solar (utility scale), biomass (dedicated), nuclear:
https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf

Brown coal, hard coal, gas (1% leakage), oil (crude):
https://www.volker-quaschning.de/datserv/CO2-spez/index_e.php

Waste:
https://zerowasteeurope.eu/2020/03/understanding-the-carbon-impacts-of-waste-to-energy/

Oil (TBD):
https://iea.blob.core.windows.net/assets/743af33c-b2f5-4a93-a925-1b08f6438e61/EmissionsfromOilandGasOperationinNetZeroTransitions.pdf

"""

CO2E = {
    "de": {
        "Hydro Run-of-River": 24,
        "Biomass": 230,
        "Fossil brown coal / lignite": 1049,
        "Fossil hard coal": 867,
        "Fossil oil": 500,
        "Fossil gas": 466,
        "Geothermal": 38,
        "Hydro water reservoir": 24,
        "Others": 0,
        "Waste": 540,
        "Wind offshore": 12,
        "Wind onshore": 11,
        "Solar": 48,
        "Nuclear": 12,
    }
}
