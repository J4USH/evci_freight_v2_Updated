from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql.connector
from decimal import Decimal
from evci_tool.config import *
from evci_tool.model import *
from evci_tool.analysis import *
import matplotlib.pyplot as plt
import os
import traceback

import json
import pandas as pd

app = FastAPI()

# Pydantic model to define input structure
class AnalyzeRequest(BaseModel):
    analysisInput_ID: int
    site_id:int

class ErrorResponseModel(BaseModel):
    message: str

# Default UI inputs


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    print(traceback.format_exc())  # Get the stack trace as a string
    
    # Capture request details (e.g., method, URL)
    print(f"{request.method} {request.url}")
    error = str(exc.detail).replace("500:", "").strip()
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(error)}
    )

@app.post("/freights")
async def analyze(request: AnalyzeRequest):
    idSelect = request.analysisInput_ID
    filename = request.site_id

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
    results = [{**dict(zip(column_names, row))} for row in mycursor.fetchall()]
    print(results)
    if not results:
        mycursor.close()
        mydb.close()
        raise HTTPException(status_code=500, detail="No data found for given ID")

    db_input = results[0]

    if db_input["holiday_percentage"]!=0 and db_input["holiday_percentage"] is not None:
        db_input["holiday_percentage"]/=100.0
    if db_input["fast_charging"]!=0 and db_input["fast_charging"] is not None:
        db_input["fast_charging"]/=100.0
    if db_input["slow_charging"]!=0 and db_input["slow_charging"] is not None:
        db_input["slow_charging"]/=100.0

    if db_input["years_of_analysis"]!=0 and db_input["years_of_analysis"] is not None:
        yoe=db_input["years_of_analysis"]
    else:
        yoe=3

    # Close database connection
    

    # Format db_input for compatibility
    for key, value in db_input.items():
        if isinstance(value, Decimal):
            db_input[key] = float(value)
        if key == "years_of_analysis":
            if db_input[key]!=0:
                if db_input[key]==1:
                    db_input[key]=[1,2]
                else:
                    db_input[key] = list(range(1, db_input[key]+1))

    # Override defaults with database values if present
    for key in ui_inputs:
        if key in db_input:
            if db_input[key] is not None and db_input[key]!=0:
                ui_inputs[key] = db_input[key]
                print(key,ui_inputs[key])
    print(ui_inputs['cluster'])
    if ui_inputs['cluster'] == 1:
        ui_inputs['cluster']=True
    if ui_inputs['cluster'] == 0:
        ui_inputs['cluster']=False
    if "cluster" in db_input:
        if db_input['cluster'] is not None:
            ui_inputs['cluster']=db_input['cluster']



    if(db_input['capex_2w_charger'] is not None and db_input['capex_2w_charger']!=0):
        ui_inputs['capex_2W']=db_input['capex_2w_charger']
    if(db_input['capex_3w_charger'] is not None and db_input['capex_3w_charger']!=0):
        ui_inputs['capex_3WS']=db_input['capex_3w_charger']
    if(db_input['capex_4w_charger'] is not None and db_input['capex_4w_charger']!=0):
        ui_inputs['capex_4WS']=db_input['capex_4w_charger']
    if(db_input['capex_4wf_charger'] is not None and db_input['capex_4wf_charger']!=0):
        ui_inputs['capex_4WF']=db_input['capex_4wf_charger']
    if(db_input['year_1_conversion'] is not None and db_input['year_1_conversion']!=0):
        ui_inputs['year1_conversion']=db_input['year_1_conversion']/100.0
    if(db_input['year_2_conversion'] is not None and db_input['year_2_conversion']!=0):
        ui_inputs['year2_conversion']=db_input['year_2_conversion']/100.0
    if(db_input['year_3_conversion'] is not None and db_input['year_3_conversion']!=0):
        ui_inputs['year3_conversion']=db_input['year_3_conversion']/100.0
    if(db_input['hoarding_capex_cost'] is not None and db_input['hoarding_capex_cost']!=0):
        ui_inputs['hoarding cost']=db_input['hoarding_capex_cost']
    if(db_input['kiosk_capex_cost'] is not None and db_input['kiosk_capex_cost']!=0):
        ui_inputs['kiosk_cost']=db_input['kiosk_capex_cost']

    

    updateParams = (
    ui_inputs["backoff_factor"],
    yoe,
    ui_inputs["capex_2W"],
    ui_inputs["capex_3WS"],
    ui_inputs["capex_4WS"],
    ui_inputs["capex_4WF"],
    ui_inputs["hoarding cost"],
    ui_inputs["kiosk_cost"],
    ui_inputs["year1_conversion"],
    ui_inputs["year2_conversion"],
    ui_inputs["year3_conversion"],
    ui_inputs["holiday_percentage"],
    ui_inputs["fast_charging"],
    ui_inputs["slow_charging"],
    int(ui_inputs["cluster"]),  # Convert to int (1 for True, 0 for False)
    ui_inputs["cluster_th"],
    int(ui_inputs["plot_dendrogram"]),
    int(ui_inputs["use_defaults"]),    
    idSelect  # This is the `id` of the record to update
)
    print(ui_inputs)
    
    updateQuery = f"""
    UPDATE analysis_inputs
    SET
        backoff_factor = %s,
        years_of_analysis = %s,
        capex_2w_charger = %s,
        capex_3w_charger = %s,
        capex_4w_charger = %s,
        capex_4wf_charger = %s,
        hoarding_capex_cost = %s,
        kiosk_capex_cost = %s,
        year_1_conversion = %s,
        year_2_conversion = %s,
        year_3_conversion = %s,
        holiday_percentage = %s,
        fast_charging = %s,
        slow_charging = %s,
        cluster = %s,
        cluster_th = %s,
        plot_dendrogram = %s,
        use_default = %s
    WHERE id = %s;
"""
    mycursor.execute(updateQuery, updateParams)
    mydb.commit()




    # Run analysis
    idSelect=str(idSelect)
    filename=str(filename)
    
    s_u_df = analyze_sites(idSelect,filename, ui_inputs,idSelect,db_input)
    
    if ui_inputs["cluster"] and os.path.exists(f"{s_u_df}clustered_evci_analysis.json"):
        df1= pd.read_json(f'{s_u_df}clustered_evci_analysis.json')
    

        df1['analysis_id']=db_input['id']
        df1['outputFile']="clustered_evci_analysis"
        df1['createdby']=db_input['createdBy']


        df1.insert(0, 'analysis_id', df1.pop('analysis_id'))  # Move 'analysis_id' to the first column
        df1.insert(1, 'outputFile', df1.pop('outputFile')) 
    
    

    df2 = pd.read_json(f'{s_u_df}initial_evci_analysis.json')
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
    if ui_inputs['cluster'] and os.path.exists(f"{s_u_df}clustered_evci_analysis.json"):
        for _, row in df1.iterrows():

            mycursor.execute(insert_query, tuple(row))

    for _, row in df2.iterrows():

        mycursor.execute(insert_query, tuple(row))
    
    insert_query = f"""
            INSERT INTO analysis_response_file_logs 
            (site_ID, analysisInput_ID, outputFor, excelFilePath, isActive, createdBy) 
            VALUES (%s, %s, %s, %s, %s,%s)
            """
    data = [
                
                (filename, idSelect, "initial_evci_analysis", s_u_df+"initial_evci_analysis.xlsx", "1", db_input['createdBy']),
                
            ]
    
    if ui_inputs['cluster'] and os.path.exists(f"{s_u_df}clustered_evci_analysis.json"):
        data.append((filename, idSelect, "cluster_evci_analysis", s_u_df+"cluster_evci_analysis.xlsx", "1", db_input['createdBy']),)
    for row in data:
        mycursor.execute(insert_query, row)

    mydb.commit()
    mycursor.close()
    mydb.close()

    # Return JSON response
    return {"status":"success","message":"generated"}

