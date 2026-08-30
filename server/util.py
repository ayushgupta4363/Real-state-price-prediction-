import json
import joblib
import numpy as np
import os

# global variable to hold loaded artifacts
__locations =None
__data_columns=None
__model =None
__scaler=None

def get_estimated_price(location, sqft, bhk, bath):
    try:
        loc_index = __data_columns.index(location.lower())
    except:
        loc_index = -1

    x = np.zeros(len(__data_columns))
    x[0] = sqft
    x[1] = bath
    x[2] = bhk
    if loc_index >= 0:
        x[loc_index] = 1

    # Check if scaler exists before transforming
    if __scaler is not None:
        x = __scaler.transform([x])
    else:
        x = [x]

    return round(__model.predict(x)[0], 2)

def load_saved_artifacts():
    print("loading saved artifacts...start")
    global __data_columns
    global __locations
    global __model
    global __scaler

    base_dir = os.path.dirname(__file__)
    artifacts_path = os.path.join(base_dir, "artifacts")

    # 1. Load data columns / locations JSON
    with open(os.path.join(artifacts_path, "columns.json"), "r") as f:
        __data_columns = json.load(f)["data_columns"]
        __locations = __data_columns[3:]  # first 3 are sqft, bath, bhk

    # 2. Load trained model
    model_path = os.path.join(artifacts_path, "bangalore_home_prices_model.joblib")
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            __model = joblib.load(f)

    # 3. Load scaler (ONLY if you actually created and saved scaler.joblib during training)
    scaler_path = os.path.join(artifacts_path, "scaler.joblib")
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as f:
            __scaler = joblib.load(f)
    else:
        __scaler = None  # Prevents crash if scaler file doesn't exist

    print("loading saved artifacts...done")

def get_location_names():
    return __locations    

if __name__ == '__main__':
    load_saved_artifacts()
    # Test call
    print(get_estimated_price('1st Phase JP Nagar', 1000, 2, 2))