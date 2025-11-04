# Returns (client, db) tuple for a given user_id
def get_mongo_client_and_db(user_id: int):
    if user_id == 0:
        uri = 'mongodb://heatSyncWebPlatform:h3atsync2024@52.17.206.238/eol_sensors'
        db_name = 'eol_sensors'
    elif user_id == 2:
        uri = 'mongodb://heatSyncTool:password@52.17.206.238/limerick_readings'
        db_name = 'limerick_readings'
    elif user_id == 1:
        uri = 'mongodb://HeatSyncTool:password@52.17.206.238/beaufort_readings'
        db_name = 'beaufort_readings'
    else:
        uri = 'mongodb://heatSyncWebPlatform:h3atsync2024@52.17.206.238/eol_sensors'
        db_name = 'eol_sensors'
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    return client, db

# Returns a collection from a db for a given readingType
def get_collection(db, user_id: int, readingType):
    print(f"User ID: {user_id}, Reading Type: {readingType}")
    dbName = None
    match readingType:
        case "electricity_readings":
            if user_id == 0:
                dbName = db["electricity_readings"]
            elif user_id == 1:
                dbName = db["hotdrop_electricity"]
            elif user_id == 2:
                dbName = db["chiselandoak_readings"]
        case "milesight_readings":
            if user_id == 0:
                dbName = db["milesight_readings"]
            elif user_id == 1:
                print("User ID 1 detected, using enginko_env database")
                dbName = db["enginko_env"]
            elif user_id == 2:
                dbName = db["chiselandoak_readings"]
        case "enginko_readings":
            if user_id == 0:
                dbName = db["enginko_readings"]
            elif user_id == 1:
                dbName = db["enginko_env"]
            elif user_id == 2:
                dbName = db["chiselandoak_readings"]
        case _:
            print(f"Warning: Unknown readingType '{readingType}'")
    print(f"Database Name: {dbName}")
    return dbName
import os
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from typing import Optional

from fastapi.responses import HTMLResponse,  RedirectResponse, Response
from fastapi_login import LoginManager
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Authentication setup
SECRET_KEY = os.environ["SECRET_KEY"]  # Will raise KeyError if not set
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Login manager setup
manager = LoginManager(SECRET_KEY, token_url="/auth/login")
manager.use_cookie = True
manager.cookie_name = "auth_cookie"


MONGODB_URI = None
### assign different datavases to different variables
HEATSYNC_TOOL_DB = None
heatSynctoolDBClient = None

## set db relative to the environment variable
def set_mongodb_uri(uri: int):
    global MONGODB_URI, HEATSYNC_TOOL_DB, heatSynctoolDBClient
    match uri:
        case 0:
            MONGODB_URI = 'mongodb://heatSyncWebPlatform:h3atsync2024@52.17.206.238/eol_sensors'
            client = AsyncIOMotorClient(MONGODB_URI)
            HEATSYNC_TOOL_DB = "eol_sensors"
            heatSynctoolDBClient = client[HEATSYNC_TOOL_DB]
            return  
        case 2  :  # matches either 1 or 2
            MONGODB_URI = 'mongodb://heatSyncTool:password@52.17.206.238/limerick_readings'
            client = AsyncIOMotorClient(MONGODB_URI)
            HEATSYNC_TOOL_DB = "limerick_readings"
            heatSynctoolDBClient = client[HEATSYNC_TOOL_DB]
        case 1:
            MONGODB_URI =  'mongodb://HeatSyncTool:password@52.17.206.238/beaufort_readings'
            client = AsyncIOMotorClient(MONGODB_URI)
            HEATSYNC_TOOL_DB = "beaufort_readings"
            heatSynctoolDBClient = client[HEATSYNC_TOOL_DB]
        case _:
            MONGODB_URI = 'mongodb://heatSyncWebPlatform:h3atsync2024@52.17.206.238/eol_sensors'
            client = AsyncIOMotorClient(MONGODB_URI)
            HEATSYNC_TOOL_DB = "eol_sensors"
            heatSynctoolDBClient = client[HEATSYNC_TOOL_DB]
    return
    
def get_db_name(user_id: int, readingType):
    """ Function to get the database name based on user_id and readingType.
    """
    print(f"User ID: {user_id}, Reading Type: {readingType}")
    print(heatSynctoolDBClient)
    dbName = None
    match readingType:
        case "electricity_readings":
            if user_id == 0:
                dbName = heatSynctoolDBClient["electricity_readings"]
            elif user_id == 1:
                dbName = heatSynctoolDBClient["hotdrop_electricity"]
            elif user_id == 2:
                dbName = heatSynctoolDBClient["chiselandoak_readings"]
        case "milesight_readings":
            if user_id == 0:
                dbName = heatSynctoolDBClient["milesight_readings"]
            elif user_id == 1:
                print("User ID 1 detected, using enginko_env database")
                dbName = heatSynctoolDBClient["enginko_env"]
            elif user_id == 2:
                dbName = heatSynctoolDBClient["chiselandoak_readings"]
        case "enginko_readings":
            if user_id == 0:
                dbName = heatSynctoolDBClient["enginko_readings"]
            elif user_id == 1:
                dbName = heatSynctoolDBClient["enginko_env"]
            elif user_id == 2:
                dbName = heatSynctoolDBClient["chiselandoak_readings"]
        case _:
            print(f"Warning: Unknown readingType '{readingType}'")
            # Optionally set dbName to a default or raise an error
    print(f"Database Name: {dbName}")
    return dbName


# //check the ConnectionAbortedError
async def get_token_from_cookie(request: Request):
    token = request.cookies.get("auth_cookie")  # Use the actual cookie name
    if not token:
       return None
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Not authenticated",
        # )
    return token


# //check if user loggged in
async def get_current_user(token: str = Depends(get_token_from_cookie)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token  is not None:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            # raise credentials_exception
            return None
    else :
        return None


#  _______HEATSYNC___________________________________________________________

### ENERGY DASHBOARD   ####
## get sensor readings from the database
## get sensor readings from the database
async def get_electricity_readings(user_id: int, collection):
    """
    Dependency to get the database client.
    """
    print("getting electricity readings for user:", user_id)
    seven_days_ago = datetime.utcnow() - timedelta(days=6)
    seven_days_ago_iso = seven_days_ago.isoformat()  # ISO 8601 format string (e.g., '2025-07-22T05:49:00.000000')
    # readings_cursor =heatSynctoolDBClient.find(
    #     {"Timestamp": {"$gte": seven_days_ago_iso}},
    #     {"_id": 0, "result": 1, "Timestamp": 1})
    filter_query = {}
    projection = {"_id": 0, "result": 1, "Timestamp": 1}
    if user_id == 2:
        filter_query = {
            "Timestamp": {"$gte": seven_days_ago_iso},
            "DevEUI": "d46352000000099f"
        }
    else:
        filter_query = {
            "Timestamp": {"$gte": seven_days_ago_iso}
        }

    print(f"Querying electricity readings for user {user_id} with filter: {filter_query}")

    # Call find with filter and projection separately
    readings_cursor = collection.find(filter_query, projection)
    sensor_readings = await readings_cursor.to_list(length=None)
    print(f"Retrieved {len(sensor_readings)} readings for user {user_id}")
    return sensor_readings


### ENERGY DASHBOARD ROUTES
@router.get("/energymonitor/{user_id}", response_class=HTMLResponse)
async def energy_monitor_page(request: Request,  user_id: int) -> HTMLResponse:
    print(f"Loading energy monitor dashboard {user_id}")
    client, db = get_mongo_client_and_db(user_id)
    collection = get_collection(db, user_id, "electricity_readings")
    print(collection)
    electricty_readings_json = await get_electricity_readings(user_id, collection)
    return templates.TemplateResponse("./dashboard/energy_monitor_dashboard.html", {"request": request, "electricityReadings": electricty_readings_json,  "user_id": user_id})

# ____________________________________________________________#

##MAIN DASHBOARD 
###MAIN DASHBOARD ROUTES


##convert date string to ISO format
def convert_date_str_to_iso(date_str):
    # Input example: '3/1/2024, 12:05:56 PM'
    # Parse with strptime, then convert to ISO format string with 'Z' (UTC assumed)
    dt = datetime.strptime(date_str, '%m/%d/%Y, %I:%M:%S %p')
    # Add 'Z' to indicate UTC timezone (assumed)
    iso_date = dt.isoformat() + 'Z'  
    return iso_date

#convert engico readings to a format that can be used in the main dashboard
async def convert_readings(resultsData):
    results = []
    for data in resultsData:
    # Map first group
        if 'date1' in data and data['date1'] is not None and 'readings1' in data:
            d1 = convert_date_str_to_iso(data['date1'])
            r1 = data['readings1']
            results.append({
                'date': d1,
                'temp': float(r1.get('temperature', 0)),
                'humidity': int(float(r1.get('humidity', 0))),
                'pressure': float(r1.get('pressure', 0)),  # optional, add if needed
                'lux': int(r1.get('lux', 0)),             # optional
                'voc': int(r1.get('voc', 0)),             # optional
                'co2': int(r1.get('co2', 0))
            })

        # Map second group
        if 'date2' in data and data['date2'] is not None and 'readings2' in data:
            d2 = convert_date_str_to_iso(data['date2'])
            r2 = data['readings2']
            results.append({
                'date': d2,
                'temp': float(r2.get('temperature', 0)),
                'humidity': int(float(r2.get('humidity', 0))),
                'pressure': float(r2.get('pressure', 0)),
                'lux': int(r2.get('lux', 0)),
                'voc': int(r2.get('voc', 0)),
                'co2': int(r2.get('co2', 0)),
            })
    # If you want to match exactly your desired fields (e.g., only date, humidity, temp, co2):
    # you can return a filtered version, for example:
    simplified_results = []
    for res in results:
        simplified_results.append({
            'date': res['date'],
            'humidity': res['humidity'],
            'temp': res['temp'],
            'co2': res['co2'],
            'lux': res.get('lux', 0),  # optional, add if needed
            'tvoc': res.get('voc', 0),  # optional, add if needed
            'pressure': res.get('pressure', 0)  # optional, add if needed
        })

    return simplified_results
 
#get data from database
async def getTempCO2Humidity(user_id: int, collection):
    """
    Dependency to get the database client.
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=6)
    seven_days_ago_iso = seven_days_ago.isoformat()  # ISO 8601 format string (e.g., '2025-07-22T05:49:00.000000')
    if user_id == 0:
     readings_cursor = collection.find(
            {"Timestamp": {"$gte": seven_days_ago_iso}},
            {"_id": 0, "date": "$Timestamp",
            "humidity": "$decoded.humidity",
            "temp": "$decoded.temperature",
            "co2": "$decoded.co2"})
     sensor_readings = await readings_cursor.to_list(length=None)
    elif user_id == 1:
            readings_cursor = collection.aggregate ([
   {"$match": {
        "result" : {
          "$elemMatch" :{ "variable" :"date" , "value" :{"$gte":seven_days_ago_iso}}
    }}},
    {        "$project": {
            "_id": 0,
            "firstGroup": { "$slice": ["$result", 0, 7] },
            "secondGroup": { "$slice": ["$result", 7, {"$size": "$result"}] }        }    },
    {        "$project": {
            "date1": {
                "$arrayElemAt": [
                    {                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$firstGroup",
                                    "as": "item",
                                    "cond": { "$eq": ["$$item.variable", "date"] }
                                }
                            },
                            "as": "dateItem",
                            "in": "$$dateItem.value"                        }                    },
                    0
                ]
            },
            "readings1": {
                "temperature": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",                                        "cond": { "$eq": ["$$item.variable", "temperature"] }                                    }                                },
                                "as": "tempItem",
                                "in": "$$tempItem.value"
                            }
                        },
                        0
                    ]
                },
                "humidity": {
                    "$arrayElemAt": [
                        {                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "humidity"] }
                                    }
                                },
                                "as": "humidityItem",
                                "in": "$$humidityItem.value"
                            }
                        },
                        0
                    ]
                },
                "pressure": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "pressure"] }
                                    }
                                },
                                "as": "pressureItem",
                                "in": "$$pressureItem.value"
                            }
                        },
                        0
                    ]
                },
                "lux": {
                    "$arrayElemAt": [                       {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "lux"] }
                                    }
                                },
                                "as": "luxItem",
                                "in": "$$luxItem.value"
                            }
                        },
                        0
                    ]
                },
                "voc": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "voc"] }
                                    }
                                },
                                "as": "vocItem",
                                "in": "$$vocItem.value"
                            }
                        },
                        0
                    ]
                },
                "co2": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "co2"] }
                                    }
                                },
                                "as": "co2Item",
                                "in": "$$co2Item.value"
                            }
                        },
                        0
                    ]
                }
            },

            "date2": {
                "$arrayElemAt": [
                    {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$secondGroup",
                                    "as": "item",
                                    "cond": { "$eq": ["$$item.variable", "date"] }
                                }
                            },
                            "as": "dateItem",
                            "in": "$$dateItem.value"
                        }
                    },
                    0
                ]
            },

            "readings2": {
                "temperature": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "temperature"] }
                                    }
                                },
                                "as": "tempItem",
                                "in": "$$tempItem.value"
                            }
                        },
                        0
                    ]
                },
                "humidity": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "humidity"] }
                                    }
                                },
                                "as": "humidityItem",
                                "in": "$$humidityItem.value"
                            }
                        },
                        0
                    ]
                },
                "pressure": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "pressure"] }
                                    }
                                },
                                "as": "pressureItem",
                                "in": "$$pressureItem.value"
                            }
                        },
                        0
                    ]
                },
                "lux": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "lux"] }
                                    }
                                },
                                "as": "luxItem",
                                "in": "$$luxItem.value"
                            }
                        },
                        0
                    ]
                },
                "voc": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "voc"] }
                                    }
                                },
                                "as": "vocItem",
                                "in": "$$vocItem.value"
                            }
                        },
                        0
                    ]
                },
                "co2": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "co2"] }
                                    }
                                },
                                "as": "co2Item",
                                "in": "$$co2Item.value"
                            }
                        },
                        0
                    ]
                },
                "battery": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "battery"] }
                                    }
                                },
                                "as": "batteryItem",
                                "in": "$$batteryItem.value"
                            }
                        },
                        0
                    ]
                }
            }
        }
    }
]) 
            sensor_readings = await readings_cursor.to_list(length=None)
            sensor_readings =  await convert_readings(  sensor_readings )
    elif user_id == 2:
        readings_cursor = collection.find(
            {"Timestamp": {"$gte": seven_days_ago_iso}, "DevEUI": "24e124710c401923"},
            {"_id": 0, "date": "$Timestamp",
            "humidity": "$result.humidity",
            "temp": "$result.temperature",
            "co2": "$result.co2"})
        sensor_readings = await readings_cursor.to_list(length=None)
            
    return sensor_readings


@router.get("/", response_class=HTMLResponse)
async def rootResuest(request: Request,  response: Response,current_user: Optional[str] = Depends(get_current_user)) -> HTMLResponse:
        return RedirectResponse(url="/home/1", status_code=303)

 # this is the root- this will send you to the login page or main dashboard if logged in
@router.get("/home/{user_id}", response_class=HTMLResponse)
async def home(request: Request, user_id: int, response: Response,current_user: Optional[str] = Depends(get_current_user)) -> HTMLResponse:
    client, db = get_mongo_client_and_db(user_id)
    collection = get_collection(db, user_id, "milesight_readings")
    print("Home")
    TempCO2HumidityData = await getTempCO2Humidity(user_id, collection)
    print("Now render")
    return templates.TemplateResponse("./dashboard/complete_dashboard.html", {"request": request, "TempCO2Humidity": TempCO2HumidityData, "user_id": user_id})
# return templates.TemplateResponse("index.html", {"request": request, "TempCO2Humidity": TempCO2HumidityData, "user_id": user_id})
#  __________________________________________________________________

##COMFORT DASHBOARD
###Comfort DASHBOARD ROUTES

async def get_graph_data(collection, user_id: int):
        dateString = datetime.utcnow() - timedelta(days=6)
        print(dateString )
        dateString = dateString.isoformat()  # ISO 8601 format string (e.g., '2025-07-22T05:49:00.000000')
        if user_id == 0:
            readings_cursor = collection.find(
            {"Timestamp": {"$gte": dateString}},
            { '_id': 0,
                'date': '$Timestamp',
                'humidity': '$decoded.humidity',
                'temp': '$decoded.temperature',
                'pm25': '$decoded.pm2_5',
                'pm10': '$decoded.pm10',
                'tvoc': '$decoded.tvoc'})
            sensor_readings = await readings_cursor.to_list(length=None)
        elif user_id == 2:
            print("Here")
            readings_cursor = collection.find(
            {"Timestamp": {"$gte": dateString}, "DevEUI": "24e124710c401923"},
            { '_id': 0,
                'date': '$Timestamp',
                'humidity': '$result.humidity',
                'temp': '$result.temperature',
                'pm25': '$result.pm2_5',
                'pm10': '$result.pm10',
                'tvoc': '$result.tvoc'})
            sensor_readings = await readings_cursor.to_list(length=None)
        elif user_id == 1:
            print("User ID 1 detected, using enginko_env database - aggre")
            readings_cursor = collection.aggregate ([
    {"$match":  {"Timestamp": {"$gte": dateString}} },
    {        "$project": {
            "_id": 0,
            "firstGroup": { "$slice": ["$result", 0, 7] },
            "secondGroup": { "$slice": ["$result", 7, {"$size": "$result"}] }        }    },
    {        "$project": {
            "date1": {
                "$arrayElemAt": [
                    {                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$firstGroup",
                                    "as": "item",
                                    "cond": { "$eq": ["$$item.variable", "date"] }
                                }
                            },
                            "as": "dateItem",
                            "in": "$$dateItem.value"                        }                    },
                    0
                ]
            },
            "readings1": {
                "temperature": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",                                        "cond": { "$eq": ["$$item.variable", "temperature"] }                                    }                                },
                                "as": "tempItem",
                                "in": "$$tempItem.value"
                            }
                        },
                        0
                    ]
                },
                "humidity": {
                    "$arrayElemAt": [
                        {                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "humidity"] }
                                    }
                                },
                                "as": "humidityItem",
                                "in": "$$humidityItem.value"
                            }
                        },
                        0
                    ]
                },
                "pressure": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "pressure"] }
                                    }
                                },
                                "as": "pressureItem",
                                "in": "$$pressureItem.value"
                            }
                        },
                        0
                    ]
                },
                "lux": {
                    "$arrayElemAt": [                       {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "lux"] }
                                    }
                                },
                                "as": "luxItem",
                                "in": "$$luxItem.value"
                            }
                        },
                        0
                    ]
                },
                "voc": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "voc"] }
                                    }
                                },
                                "as": "vocItem",
                                "in": "$$vocItem.value"
                            }
                        },
                        0
                    ]
                },
                "co2": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$firstGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "co2"] }
                                    }
                                },
                                "as": "co2Item",
                                "in": "$$co2Item.value"
                            }
                        },
                        0
                    ]
                }
            },

            "date2": {
                "$arrayElemAt": [
                    {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$secondGroup",
                                    "as": "item",
                                    "cond": { "$eq": ["$$item.variable", "date"] }
                                }
                            },
                            "as": "dateItem",
                            "in": "$$dateItem.value"
                        }
                    },
                    0
                ]
            },

            "readings2": {
                "temperature": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "temperature"] }
                                    }
                                },
                                "as": "tempItem",
                                "in": "$$tempItem.value"
                            }
                        },
                        0
                    ]
                },
                "humidity": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "humidity"] }
                                    }
                                },
                                "as": "humidityItem",
                                "in": "$$humidityItem.value"
                            }
                        },
                        0
                    ]
                },
                "pressure": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "pressure"] }
                                    }
                                },
                                "as": "pressureItem",
                                "in": "$$pressureItem.value"
                            }
                        },
                        0
                    ]
                },
                "lux": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "lux"] }
                                    }
                                },
                                "as": "luxItem",
                                "in": "$$luxItem.value"
                            }
                        },
                        0
                    ]
                },
                "voc": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "voc"] }
                                    }
                                },
                                "as": "vocItem",
                                "in": "$$vocItem.value"
                            }
                        },
                        0
                    ]
                },
                "co2": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "co2"] }
                                    }
                                },
                                "as": "co2Item",
                                "in": "$$co2Item.value"
                            }
                        },
                        0
                    ]
                },
                "battery": {
                    "$arrayElemAt": [
                        {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$secondGroup",
                                        "as": "item",
                                        "cond": { "$eq": ["$$item.variable", "battery"] }
                                    }
                                },
                                "as": "batteryItem",
                                "in": "$$batteryItem.value"
                            }
                        },
                        0
                    ]
                }
            }
        }
    }
]) 
            sensor_readings = await readings_cursor.to_list(length=None)
            sensor_readings =  await convert_readings(  sensor_readings )
        
        # print("Sensors Readings: ", sensor_readings)
        # Replace table with actual collection
        return sensor_readings


async def get_last_readings(collection,  user_id: int):
        dateString = datetime.utcnow() - timedelta(days=6)
        dateString = dateString.isoformat()  # ISO 8601 format string (e.g., '2025-07-22T05:49:00.000000')
        if user_id == 0:
            readings_cursor = collection.find(
            {"Timestamp": {"$gte": dateString}},
            {  '_id': 0,
                'decoded.temperature': 1,
                'decoded.humidity': 1,
                'decoded.pm2_5': 1,
                'decoded.pm10': 1,
                'decoded.tvoc': 1}).sort("Timestamp", -1).limit(1)
        elif user_id == 1:
            print("1 - DOESNT EXIST")
            readings_cursor =None
        elif user_id == 2:
              readings_cursor = collection.find(
            {"Timestamp": {"$gte": dateString}, "DevEUI": None},
            {  '_id': 0,
                'decoded.temperature': 1,
                'decoded.humidity': 1,
                'decoded.pm2_5': 1,
                'decoded.pm10': 1,
                'decoded.tvoc': 1}).sort("Timestamp", -1).limit(1)
        if readings_cursor is None:
            sensor_readings = []
        else :      
         sensor_readings = await readings_cursor.to_list(length=None)
        # Replace table with actual collection
        return sensor_readings

async def get_light_level_changes(collection ,user_id: int):
        dateString = datetime.utcnow() - timedelta(days=6)
        dateString = dateString.isoformat()  # ISO 8601 format string (e.g., '2025-07-22T05:49:00.000000')
        pipeline = [
            {'$unwind': {'path': "$result", 'includeArrayIndex': "arrayNo"}},
            {'$match': {'result.variable': "lux"}},
            {'$group': {
                '_id': "$Timestamp",
                'uniqueValues': {'$addToSet': "$result.value"},
                'arrayNo': {'$addToSet': "$arrayNo"},
                'count': {'$sum': 1}
            }},
            {'$match': {'$expr': {'$gt': [{'$size': "$uniqueValues"}, 1]}}},
            {'$sort': {'_id': 1}},
            {'$project': {'_id': 0, 'arrayNo': 1, 'uniqueValues': 1, 'Timestamp': "$_id"}}
        ]
        readings_cursor = collection.aggregate(pipeline)
        sensor_readings = await readings_cursor.to_list(length=None)
        return sensor_readings

### ENERGY DASHBOARD ROUTES
@router.get("/comfort/{user_id}", response_class=HTMLResponse)
async def comfort_monitor_page(request: Request,  user_id: int) -> HTMLResponse:
    client, db = get_mongo_client_and_db(user_id)
    collection_milesight = get_collection(db, user_id, "milesight_readings")
    graph_data = await get_graph_data(collection_milesight, user_id)
    last_readings = await get_last_readings(collection_milesight, user_id)
    collection_enginko = get_collection(db, user_id, "enginko_readings")
    light_level_changes = await get_light_level_changes(collection_enginko, user_id)
    return templates.TemplateResponse(
        "dashboard/heatsync_comfort_settings_dashboard.html",
        {
            "request": request,
            "graph_data": graph_data,
            "last_readings": last_readings or [],
            "light_level_changes": light_level_changes,
            "user_id": user_id,
            "section": "two",
            "data": {"text": "Section Two"}
        }
    )