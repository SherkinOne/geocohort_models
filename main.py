from fastapi import FastAPI, Form, Request, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pathlib import Path
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
# from PIL import Image
# from enum import Enum
from bson import json_util
import os
from starlette.middleware.base import BaseHTTPMiddleware

import math
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Union


# // setup login cookies
app = FastAPI()  ## this is needed for running behind a proxy for traefik
 
# Load environment variables (optional)
from dotenv import load_dotenv

load_dotenv()

# app.include_router(uploadroutes.router)

# cookie_transport = CookieTransport(cookie_max_age=3600)
templates = Jinja2Templates(directory="templates")
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# // setup login cookies
# SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
# manager = LoginManager(SECRET_KEY, token_url="/login")
# manager.use_cookie = True
# manager.cookie_name = "auth_cookie"

# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

MONGODB_URI = os.getenv("MONGODB_CONNECTION_URI")
client = AsyncIOMotorClient(MONGODB_URI)
geoCohortDBClient = client["Geocohort"]


# Password  hashing setup
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# this is actually irrelevant for CSP as we are not using any external auth- but keep for reference
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip CSP for static files
        if request.url.path.startswith('/static/'):
            return await call_next(request)
            
        response = await call_next(request)
        
        # Only apply CSP to HTML responses
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type.lower():
            csp_policy = (
                "default-src 'self' http: https: data:; "
                "style-src 'self' 'unsafe-inline' http: https:; "
                "style-src-elem 'self' 'unsafe-inline' http: https:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http: https:; "
                "img-src 'self' data: http: https:; "
                "font-src 'self' data: http: https:; "
                "connect-src 'self' http: https:; "
                "frame-src 'self' http: https:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'self';"
            )
            response.headers["Content-Security-Policy"] = csp_policy
            # For older browsers
            response.headers["X-Content-Security-Policy"] = csp_policy
            response.headers["X-WebKit-CSP"] = csp_policy
        return response

app.add_middleware(CSPMiddleware)

# this gets the top level tabs for a given tab name from overall DB
async def get_keys_for_tabs(tab_name) :
    overallDB= geoCohortDBClient["Overall"]
    toMatch=  {
        '$match': {
            'Name':  tab_name
        }
    }
    keys = await overallDB.aggregate([
    toMatch, {
        '$project': {
            'mlkeys': {
                '$map': {
                    'input': {
                        '$objectToArray': '$ML'
                    }, 
                    'as': 'pair', 
                    'in': '$$pair.k'
                }
            }, "_id": 0
        }
    }
]).to_list(length=None)
    print("keys : ", keys)
    if keys is not None and 'mlkeys' in keys[0]:
        return keys[0]['mlkeys']    
    print("No keys found")
    return []

#get list of databases for a given tab name from overall DB
async def  get_db_names(tab_name) :
    overallDB= geoCohortDBClient["Overall"]
    toMatch=  {'Name':  tab_name}
    dbList = await overallDB.find_one(toMatch, {"ML": 1, "_id": 0})
    return dbList

# get metrics from a given database using energy model as example
async def  Energy_Consumption_Forecasting_overview(db_name) :
    overallDB= geoCohortDBClient[db_name]
    dbList = await overallDB.find_one({}, {"metrics": 1, "_id": 0})
    if dbList is not None and 'metrics' in dbList:
        return dbList['metrics']
    else:   
        return {}
    
# get metrics from a given database using anamolies
async def  Anomaly_Detection_Models_overview(db_name) :
    overallDB= geoCohortDBClient[db_name]
    dbList = await overallDB.find_one({}, {"anomaly_fraction":1, "anomaly_count":1 , "_id": 0})
    if dbList is not None :
        return dbList 
    else:
        return {}
    
async def Comfort_Optimisation_Models_overview(db_name) :
    print("DB NAME: ", db_name)
    overallDB= geoCohortDBClient[db_name]
    dbList = await overallDB.find_one({}, {"diagnostics": 1 , "_id": 0})
    if dbList is not None :
        return dbList['diagnostics']['predicted_next_state']
    else:
        return {}

#load dashboard data relative t o tab name
@app.get("/dashboard/{tab_name}")
async def dashboard(request: Request, tab_name: str):
    # so should be a swtich and return the data to the template
    print(tab_name)
    kDataToReturn = getTimeSeriesDemoData()
    ## get the top level tabs
    getDataBaseNames = await get_db_names(tab_name)
    topLeveltabs = await get_keys_for_tabs(tab_name)
    metricsData = {}
    match tab_name:
        case "Energy Consumption Forecasting" :
            for databaseName in getDataBaseNames['ML']:
                db_name =  getDataBaseNames['ML'][databaseName]['dbName']
                metricsData[ databaseName]= await Energy_Consumption_Forecasting_overview(db_name)
            # metricsDataForGraph = {}
            # for model, metrics in metricsData.items():
            #     for metric, value in metrics.items():
            #         if metric not in metricsDataForGraph:
            #             metricsDataForGraph[metric] = []
            #         metricsDataForGraph[metric].append({'category': model, 'value': value})
        case "Anomaly Detection Models":
            for databaseName in getDataBaseNames['ML']:
                db_name =  getDataBaseNames['ML'][databaseName]['dbName']
                metricsData[ databaseName]= await Anomaly_Detection_Models_overview(db_name)
                
        case "Comfort Optimisation Models" :
            for databaseName in getDataBaseNames['ML']:
                db_name =  getDataBaseNames['ML'][databaseName]['dbName']
                metricsData[ databaseName]= await Comfort_Optimisation_Models_overview(db_name)
    
    metricsDataForGraph = {}
    for model, metrics in metricsData.items():
         for metric, value in metrics.items():
                    if metric not in metricsDataForGraph:
                        metricsDataForGraph[metric] = []
                    metricsDataForGraph[metric].append({'category': model, 'value': value})
    #print( {"Data" : kDataToReturn,"dataForModels": [metricsDataForGraph], "tab_name": tab_name, "topLeveltabs":topLeveltabs})
    return templates.TemplateResponse("./index.html", {"request": request, "kdata" : kDataToReturn,"dataForModels": [metricsDataForGraph], "tab_name": tab_name, "topLeveltabs":topLeveltabs})

# Helpers
def rand_normal(mean: float = 0.0, std_dev: float = 1.0) -> float:
    # Box-Muller transform to generate normal distribution
    u = 1.0 - random.random()
    v = 1.0 - random.random()
    return mean + std_dev * math.sqrt(-2.0 * math.log(u)) * math.cos(2.0 * math.pi * v)

#taken from php
def metrics(y: List[float], yhat: List[float]) -> Dict[str, Union[float, Any]]:
    n = len(y)
    if n == 0:
        return {"MAE": 0, "RMSE": 0, "R2": 0, "MAPE_pct": 0}
    mae = 0.0
    mse = 0.0
    mean = sum(y) / n
    ss_tot = 0.0
    ss_res = 0.0
    mape = 0.0
    for i in range(n):
        e = y[i] - yhat[i]
        mae += abs(e)
        mse += e * e
        ss_tot += (y[i] - mean) ** 2
        ss_res += e * e
        den = max(abs(y[i]), 1e-6)
        mape += abs((y[i] - yhat[i]) / den)
    rmse = math.sqrt(mse / n)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else float('nan')
    return {
        "MAE": round(mae / n, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "MAPE_pct": round((mape / n) * 100.0, 4)
    }


def map3(times: List[str], actual: List[float], pred: List[float]) -> List[Dict[str, Any]]:
    return [{"time": times[i], "actual": actual[i], "temperature_C": pred[i]} for i in range(len(times))]

#taken from php
def getTimeSeriesDemoData():
# Time series (last 24h, 15-min cadence)
    elbow = []
    sil = []
    for k in range(2, 9):
        inertia = 1200.0 / k + rand_normal(0, 10)
        silhouette = 0.4 + 0.25 * math.exp(-((k - 3.5) / 1.5) ** 2) + rand_normal(0, 0.01)
        elbow.append({"k": k, "inertia": round(max(100.0, inertia), 2)})
        sil.append({"k": k, "silhouette": round(min(0.99, max(0.2, silhouette)), 3)})
    payload = {
        "elbow": elbow,
        "silhouette": sil
    }
    return payload

# API endpoint to get database names for a given tab - also this is redundant now
@app.get("/get_db_names/{tab_name}")
async def get_graph_data(tab_name: str, graph_name: str):
    db_names = await get_db_names(tab_name)
    return db_names

# this is comfort optimisation data
@app.post("/dashboard/get_ifc_data", response_class=HTMLResponse)
async def get_graph_data(request: Request, graphType: str = Form(...), activePage: str = Form(...)):
    listOfDBs = await get_db_names(activePage)
    dbForData = listOfDBs['ML'][graphType]['dbName']
    dbToUSe= geoCohortDBClient[dbForData]
    comfort_data = await dbToUSe.find({}, {"comfort" : "$recommendations", "_id": 0}).to_list(length=None)
        # return json_util.dumps(docs)
    return JSONResponse(content=jsonable_encoder({"results" : comfort_data[0]}), status_code=200)
 
 # get graph data for a given graph type and active page
@app.post("/dashboard/get_graph_data", response_class=HTMLResponse)
async def get_graph_data(request: Request, graphType: str = Form(...), activePage: str = Form(...)):
    listOfDBs = await get_db_names(activePage)
    dbForData = listOfDBs['ML'][graphType]['dbName']
    dbToUSe= geoCohortDBClient[dbForData]
    latest_doc = await dbToUSe.aggregate([
    {
        "$group": {
            "_id": None,
            "maxDate": {"$max": "$timestamp"}
        }
    }
]).to_list(length=None)
    latest_date = latest_doc[0]['maxDate']
    if latest_date:
        latest_date = datetime.strptime(latest_date, "%Y-%m-%d %H:%M:%S%z")
        # Set range for the day (assuming latest_date is a Python datetime object)
        if latest_date.tzinfo is None:
            latest_date = latest_date.replace(tzinfo=timezone.utc)
        start_of_day = datetime(latest_date.year, latest_date.month, latest_date.day, tzinfo=timezone.utc)
        # Fetch all docs for the latest full day
        docs =await dbToUSe.find({
            "timestamp": {
                "$gte": str(start_of_day)   ,
            }
        },{"_id": 0}).to_list(length=None)
        # return json_util.dumps(docs)
        return JSONResponse(content=jsonable_encoder({"results" : docs}), status_code=200)
    return []
