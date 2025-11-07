from fastapi import FastAPI, Form, Request, Depends, HTTPException
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
print("MONGODB_URI: ", MONGODB_URI)
client = AsyncIOMotorClient(MONGODB_URI)
geoCohortDBClient = client["Geocohort"]


# Password  hashing setup
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


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
    return keys[0]['mlkeys']

async def  get_db_names(tab_name) :
    overallDB= geoCohortDBClient["Overall"]
    toMatch=  {'Name':  tab_name}
    dbList = await overallDB.find_one(toMatch, {"ML": 1, "_id": 0})
    print ("DB LIST: ", dbList)
    return dbList

async def  get_db_metrics(db_name) :
    overallDB= geoCohortDBClient[db_name]
    dbList = await overallDB.find_one({}, {"metrics": 1, "_id": 0})
    if dbList is not None and 'metrics' in dbList:
        return dbList['metrics']
    else:
        return {}

@app.get("/dashboard/{tab_name}")
async def dashboard(request: Request, tab_name: str):
    # so should be a swtich and return the data to the template
    dataToReturn = getTimeSeriesDemoData()
    ## get the top level tabs

    topLeveltabs = await get_keys_for_tabs(tab_name)
    getDataBaseNames = await get_db_names(tab_name)
    metricsData = {}
    for databaseName in getDataBaseNames['ML']:
        db_name =  getDataBaseNames['ML'][databaseName]['dbName']
        k=getDataBaseNames['ML']
        metricsData[ databaseName]= await get_db_metrics(db_name)
    print("Metrics Data: ", metricsData)
    match tab_name:
        case "Predictive_Temperature_Modeling":
            pass
        case "Energy_Consumption_Forecasting":
            pass
        case "Comfort_Optimisation_Models":
            pass
        case "Anomaly_Detection_Models":
            pass
        case "Load_Balancing_Models":
            pass
        case "Behavioural_Change_Impact_Models":
            pass  
        case "Dynamic_Pricing_Optimisation_Models":
            pass  
        case "Predictive_Maintenance_Modeling":
            pass
        case "Energy_Efficiency_Profiling":
            pass
        case "Zone-Based_Load_Forecasting":
            pass
        # case _:
        #     raise HTTPException(status_code=404, detail="Dashboard not found")
    print("Tab Name: ", tab_name)
    return templates.TemplateResponse("./index.html", {"request": request, "dataForModels": [dataToReturn], "tab_name": tab_name, "topLeveltabs":topLeveltabs})



# Helpers
def rand_normal(mean: float = 0.0, std_dev: float = 1.0) -> float:
    # Box-Muller transform to generate normal distribution
    u = 1.0 - random.random()
    v = 1.0 - random.random()
    return mean + std_dev * math.sqrt(-2.0 * math.log(u)) * math.cos(2.0 * math.pi * v)


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

def getTimeSeriesDemoData():
# Time series (last 24h, 15-min cadence)
    points = 96
    current_ts = int(time.time())
    end_ts = current_ts - (current_ts % (15 * 60))
    times = [datetime.fromtimestamp(end_ts - i * 900, tz=timezone.utc).isoformat() for i in reversed(range(points))]

    actual = []
    for t_str in times:
        ts = datetime.fromisoformat(t_str).timestamp()
        hour = datetime.utcfromtimestamp(ts).hour + datetime.utcfromtimestamp(ts).minute / 60.0
        diurnal = 2.2 * math.sin(2.0 * math.pi * (hour - 14.0) / 24.0)
        actual.append(round(20.0 + diurnal + rand_normal(0, 0.25), 3))


    def make_pred(actual: List[float], bias: float, noise: float) -> List[float]:
        return [round(v + bias + rand_normal(0, noise), 3) for v in actual]


    pred_arima = make_pred(actual, 0.06, 0.25)
    pred_sarimax = make_pred(actual, 0.02, 0.20)
    pred_lstm = make_pred(actual, 0.01, 0.18)

    met_arima = metrics(actual, pred_arima)
    met_sarimax = metrics(actual, pred_sarimax)
    met_lstm = metrics(actual, pred_lstm)

    results = [
        {"model": "ARIMA(2,1,2)", "metrics": met_arima, "predictions": map3(times, actual, pred_arima)},
        {"model": "SARIMAX(1,1,1)x(1,0,1,60)", "metrics": met_sarimax, "predictions": map3(times, actual, pred_sarimax)},
        {"model": "LSTM(w=24,h=1)", "metrics": met_lstm, "predictions": map3(times, actual, pred_lstm)}
    ]

    scores = [
        {"model": results[0]["model"], **met_arima},
        {"model": results[1]["model"], **met_sarimax},
        {"model": results[2]["model"], **met_lstm}
    ]

    elbow = []
    sil = []
    for k in range(2, 9):
        inertia = 1200.0 / k + rand_normal(0, 10)
        silhouette = 0.4 + 0.25 * math.exp(-((k - 3.5) / 1.5) ** 2) + rand_normal(0, 0.01)
        elbow.append({"k": k, "inertia": round(max(100.0, inertia), 2)})
        sil.append({"k": k, "silhouette": round(min(0.99, max(0.2, silhouette)), 3)})

    payload = {
        "job_id": "python-demo",
        "family": "ptm",
        "results": results,
        "scores": scores,
        "elbow": elbow,
        "silhouette": sil
    }

    return payload
