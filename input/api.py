from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from decimal import Decimal
from evci_tool.config import *
from evci_tool.model import *
from evci_tool.analysis import *
import matplotlib.pyplot as plt
import os

import json
import pandas as pd

app = FastAPI()

# Pydantic model to define input structure
class AnalyzeRequest(BaseModel):
    id: int

# Default UI inputs
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

@app.post("/freights")
async def analyze(request: AnalyzeRequest):
    idSelect = request.id

    # Database connection and query
    query = "SELECT * FROM analysis_inputs WHERE id = %s;"
    mydb = mysql.connector.connect(
        host="139.59.23.75",
        port=5782,
        user="dbadminusr",
        password="$D3vel0per2024",
        database="EVCI"
    )
    mycursor = mydb.cursor()
    mycursor.execute(query, (idSelect,))

    # # Retrieve column names and data
    column_names = [i[0] for i in mycursor.description]
    results = [{**dict(zip(column_names, row)), "plot_dendrogram": "true"} for row in mycursor.fetchall()]
    print(results)
    if not results:
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=404, detail="No data found for given ID")

    db_input = results[0]

    # Close database connection
    

    # Format db_input for compatibility
    for key, value in db_input.items():
        if isinstance(value, Decimal):
            db_input[key] = float(value)
        elif key == "years_of_analysis":  
            db_input[key] = list(range(1, db_input[key]+1))
        

    # Override defaults with database values if present
    for key in ui_inputs:
        if key in db_input:
            if db_input[key] is not None:
                ui_inputs[key] = db_input[key]

    
    if(db_input['capex_2w_charger'] is not None):
        ui_inputs['capex_2W']=db_input['capex_2w_charger']
    if(db_input['capex_3w_charger'] is not None):
        ui_inputs['capex_3WS']=db_input['capex_3w_charger']
    if(db_input['capex_4w_charger'] is not None):
        ui_inputs['capex_4WS']=db_input['capex_4w_charger']
    if(db_input['capex_4wf_charger'] is not None):
        ui_inputs['capex_4WF']=db_input['capex_4wf_charger']
    if(db_input['hoarding_capex_cost'] is not None):
        ui_inputs['hoarding cost']=db_input['hoarding_capex_cost']
    if(db_input['kiosk_capex_cost'] is not None):
        ui_inputs['kiosk_cost']=db_input['kiosk_capex_cost']
    if(db_input['year_1_conversion'] is not None):
        ui_inputs['year1_conversion']=db_input['year_1_conversion']
    if(db_input['year_2_conversion'] is not None):
        ui_inputs['year2_conversion']=db_input['year_2_conversion']
    if(db_input['year_3_conversion'] is not None):
        ui_inputs['year3_conversion']=db_input['year_3_conversion']
    


    if ui_inputs["cluster"] == 1:
        ui_inputs["cluster"]=True
    else:
        ui_inputs["cluster"]=False

    if ui_inputs["plot_dendrogram"] == 1:
        ui_inputs["plot_dendrogram"]=True
    else:
        ui_inputs["plot_dendrogram"]=False
    # Run analysis
    filepath='chandigarh_karnal'

    
    s_u_df = analyze_sites(filepath, ui_inputs)

    df1= pd.read_json(f'output\{filepath}\clustered_evci_analysis.json')
    df2 = pd.read_json(f'output\{filepath}\initial_evci_analysis.json')

    df1['analysis_id']=db_input['id']
    df1['outputFile']="clustered_evci_analysis"
    df1['createdby']=db_input['createdBy']


    df1.insert(0, 'analysis_id', df1.pop('analysis_id'))  # Move 'analysis_id' to the first column
    df1.insert(1, 'outputFile', df1.pop('outputFile')) 
    
    


    df2['analysis_id']=db_input['id']
    df2['outputFile']="initial_evci_analysis"
    df2['createdby']=db_input['createdBy']


    df2.insert(0, 'analysis_id', df2.pop('analysis_id'))  # Move 'analysis_id' to the first column
    df2.insert(1, 'outputFile', df2.pop('outputFile'))


    insert_query = f"""
INSERT INTO analysis_responses (
    analysisInput_ID, output_for, location_name, latitude, longitude, 
    transformer_name, transformer_latitude, transformer_longitutde, transformer_distance, 
    number_of_vehicle, year_1, kiosk_hoarding, hoarding_margin, geometry, utiliztion, 
    unserviced, capex, opex, margin, max_vehicles, estimated_vehicles, createdBy) VALUES ( %s, %s, %s, %s, %s, 0, 0, 0, 0,%s, %s, %s, %s, 0, %s, %s, %s, %s, %s, %s, %s, %s)
"""
    
    for _, row in df1.iterrows():

        mycursor.execute(insert_query, tuple(row))

    for _, row in df2.iterrows():

        mycursor.execute(insert_query, tuple(row))
    

    json_data1 = df1.to_json(orient='records', indent=4)
    json_data2 = df2.to_json(orient='records', indent=4)

    mydb.commit()
    mycursor.close()
    mydb.close()

    # Return JSON response
    return json_data1,json_data2
