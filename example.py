# AUTOGENERATED! DO NOT EDIT! File to edit: ../index.ipynb.

# %% auto 0
__all__ = []

# %% ../index.ipynb 1
from evci_tool.config import *
from evci_tool.model import *
from evci_tool.analysis import *

# Inputs from UI
ui_inputs = { 
    "backoff_factor": 1,
    "M": ["3WS", "4WS", "4WF"],
    "years_of_analysis": [1,2,3],
    "capex_2W": 2500,
    "capex_3WS": 112000,
    "capex_4WS": 250000,
    "capex_4WF": 1500000,
    "hoarding cost": 900000,
    "kiosk_cost": 180000,
    "year1_conversion": 0.05,
    "year2_conversion": 0.15,
    "year3_conversion": 0.25,
    "holiday_percentage": 1,
    "fast_charging": 0.25,
    "slow_charging": 0.25,
    "cluster": True,
    "cluster_th": 0.02,
    "plot_dendrogram": True,
    "use_defaults": False    
}
s_u_df = analyze_sites('chandigarh_karnal', ui_inputs)