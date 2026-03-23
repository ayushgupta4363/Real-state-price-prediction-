import json
import joblib
import numpy as np
import os

# global variable to hold loaded artifacts
__locations =None
__data_columns=None
__model =None
__scaler=None

def get_estimated_price(location,sqft,bhk,bath):
    try :
        loc_index=__data_columns.index(location.lower())
    except :
        loc_index = -1

    x=np.zeros(len(__data_columns))
    x[0]= sqft
    x[1]= bath
    x[2]= bhk
    if loc_index >=0:
        x[loc_index]=1

    # Apply scaling before predicting
    x_scaled = __scaler.transform([x])
    return round(__model.predict(x_scaled)[0], 2)    

def load_saved_artifacts():
    print("loading saved artifacts...start")
    global __data_columns
    global __locations
    global __model
    global __scaler

   # Get the absolute path to the artifacts folder
    base_dir = os.path.dirname(__file__)
    # If util.py and artifacts are in the same 'server' folder, use this:
    artifacts_path = os.path.join(base_dir, "artifacts")

    with open(os.path.join(artifacts_path, "columns.json"), "r") as f:
        __data_columns = json.load(f)['data_columns']
        __locations = __data_columns[3:]

    __scaler = joblib.load(os.path.join(artifacts_path, "scaler.joblib"))
    __model = joblib.load(os.path.join(artifacts_path, "bangalore_home_prices_model.joblib"))
    print("loading saved artifacts...done")

def get_location_names():
    return __locations    

if __name__ == '__main__':
    load_saved_artifacts()
    # Test call
    print(get_estimated_price('1st Phase JP Nagar', 1000, 2, 2))