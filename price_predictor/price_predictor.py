import logging

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import pandas as pd
import numpy as np
from prophet import Prophet
from concurrent.futures import ThreadPoolExecutor
from serverutils.threading import get_optimal_worker_count
import threading
import uuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Time to keep cached images
CACHE_TIME = 1

# Thread-safe cache for storing prediction results
cache = {}
cache_lock = threading.Lock()

# Thread pool for handling concurrent requests
executor = ThreadPoolExecutor(max_workers=get_optimal_worker_count())
logging.info(f"ThreadPoolExecutor initialized with {executor._max_workers} workers")

# Data file and column mappings
data_file_mapping = {
    'super_market_prices': './data/supermarket-sales-data/annex3.csv',
    'super_market_sales': './data/supermarket-sales-data/annex2.csv',
}

data_column_names = {
    'super_market_prices': {'Date': 'ds', 'Wholesale Price (RMB/kg)': 'y'},
    'super_market_sales': {'Date': 'ds', 'Quantity Sold (kilo)': 'y'},
}


def load_data(data_name='super_market_prices'):
    file_path = data_file_mapping[data_name]
    data = pd.read_csv(file_path)
    data = data.rename(columns=data_column_names[data_name])
    data['ds'] = pd.to_datetime(data['ds'])
    data['Item Code'] = data['Item Code'].astype('string')
    return data


def run_price_predictor(product_id, time_period, optional_date):
    data = load_data('super_market_prices')

    if time_period:
        time_period = int(time_period)

    item_data = data[data['Item Code'] == product_id]

    his_data = item_data[['ds','y']].copy()
    his_data.columns = ["Date","Price"]
    his_data['Type'] = 'Historical'

    item_data.loc[:, 'ds'] = np.array(item_data['ds'])

    item_data['cap'] = item_data['y'].max() #* 1.2 # # Set a cap 20% higher than the max observed demand
    item_data['floor'] = 0 # Assuming demand can't go negative

    
    # Initialize Prophet model
    model = Prophet(growth='logistic', 
                changepoint_prior_scale=0.05,  # Lower values make the model less sensitive to trend changes
                yearly_seasonality=True,       # Enable yearly seasonality by default
                weekly_seasonality=False,      # Disable weekly seasonality if irrelevant
                daily_seasonality=False)
    
    model.add_seasonality(name='yearly', period=365.25, fourier_order=12)

    
    model.fit(item_data)
   # model = Prophet(yearly_seasonality=False, changepoint_prior_scale=0.001)
    #model.add_seasonality(name='yearly', period=365.25, fourier_order=9)
    #model.fit(item_data[['ds', 'y']])

    if optional_date:
        time_period = pd.to_datetime(optional_date) - item_data['ds'].max()
        time_period = time_period.days

    future = model.make_future_dataframe(periods=time_period)
    future['cap'] = item_data['cap'].iloc[0]  # Use the same cap from historical data
    future['floor'] = 0  # Prevent negative values

    forecast = model.predict(future)

    cast_data = forecast[['ds','yhat']].copy()
    cast_data.columns = ["Date","Price"]
    cast_data['Type'] = 'Forecast'
    cast_data = cast_data[cast_data['Date'] > his_data.max()["Date"]]
    graph_data = pd.concat([his_data, cast_data], ignore_index=True)

    predicted_price = None
    if optional_date:
        predicted_price = forecast[forecast['ds'] == optional_date]['yhat'].iloc[-1]

    return predicted_price, graph_data

def run_demand_predictor(product_id, time_period, optional_date):
    data = load_data('super_market_sales')

    if time_period:
        time_period = int(time_period)

    item_data = data[data['Item Code'] == product_id]

    # Handling Negative Quantities
    item_data = item_data[item_data['y'] >= 0]

    

    # Ensure the 'ds' column is a numpy array
    item_data.loc[:, 'ds'] = np.array(item_data['ds'])

    # Aggregate demands on the same days
    item_data = item_data.groupby('ds', as_index=False)['y'].sum()

    his_data = item_data[['ds','y']].copy()
    his_data.columns = ["Date","Price"]
    his_data['Type'] = 'Historical'

 
    item_data['cap'] = item_data['y'].max() #* 1.2 # # Set a cap 20% higher than the max observed demand
    item_data['floor'] = 0 # Assuming demand can't go negative 

     # Optional: Remove outliers (you can adjust the threshold as needed)
    item_data = item_data[item_data['y'] >= item_data['y'].quantile(0.02)]  # Remove bottom 2% outliers
    item_data = item_data[item_data['y'] <= item_data['y'].quantile(0.98)]  # Remove top 2% outliers

    

    # Initialize Prophet model
    model = Prophet(growth='logistic', 
                changepoint_prior_scale=0.05,  # Lower values make the model less sensitive to trend changes
                yearly_seasonality=True,       # Enable yearly seasonality by default
                weekly_seasonality=False,      # Disable weekly seasonality if irrelevant
                daily_seasonality=False)
    model.add_seasonality(name='yearly', period=365.25, fourier_order=12)

    # Optional: Add specific seasonality or tuning
    #model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    #model.add_seasonality(name='yearly', period=365.25, fourier_order=12)
    print(item_data.info())
    print(item_data.describe())
    model.fit(item_data)
    '''model = Prophet(yearly_seasonality=False, changepoint_prior_scale=0.001)
    model.add_seasonality(name='yearly', period=365.25, fourier_order=9)
    model.fit(item_data[['ds', 'y']])'''

    if optional_date:
        time_period = pd.to_datetime(optional_date) - item_data['ds'].max()
        time_period = time_period.days

    future = model.make_future_dataframe(periods=time_period)
    future['cap'] = item_data['cap'].iloc[0]  # Use the same cap from historical data
    future['floor'] = 0  # Prevent negative values

    forecast = model.predict(future)

    cast_data = forecast[['ds','yhat']].copy()
    cast_data.columns = ["Date","Price"]
    cast_data['Type'] = 'Forecast'
    cast_data = cast_data[cast_data['Date'] > his_data.max()["Date"]]
    graph_data = pd.concat([his_data, cast_data], ignore_index=True)

    predicted_demand = None
    if optional_date:
        predicted_demand = forecast[forecast['ds'] == optional_date]['yhat'].iloc[-1]
    print(product_id)
    print(graph_data.describe())

    return predicted_demand, graph_data

def cache_prediction(product_id, time_period, optional_date, prediction_type):
    if prediction_type == 'price':
        predicted_value, graph_data = run_price_predictor(product_id, time_period, optional_date)
    elif prediction_type == 'demand':
        predicted_value, graph_data = run_demand_predictor(product_id, time_period, optional_date)
    else:
        raise ValueError("Invalid prediction type")

    # Generate a unique ID for this prediction
    prediction_id = str(uuid.uuid4())

    # save data_graph
    data_path = f'temp_{prediction_id}.csv'
    graph_data.to_csv(data_path, index=False)

    # Store the result in the cache
    with cache_lock:
        cache[prediction_id] = {
            'product_id': product_id,
            'predicted_value': predicted_value,
            'data_path': data_path,
            'timestamp': datetime.now(),
            'prediction_type': prediction_type
        }

    return prediction_id


@app.route('/predict_price', methods=['POST'])
def predict_price():
    data = request.json
    product_id = str(data['product_id'])
    time_period = data['time_period']
    optional_date = data.get('optional_date')

    # Run the prediction in a separate thread
    future = executor.submit(cache_prediction, product_id, time_period, optional_date, 'price')
    prediction_id = future.result()

    response = {
        'prediction_id': prediction_id,
        'product_id': product_id,
        'predicted_price': cache[prediction_id]['predicted_value']
    }

    return jsonify(response)

@app.route('/predict_demand', methods=['POST'])
def predict_demand():
    data = request.json
    product_id = str(data['product_id'])
    time_period = data['time_period']
    optional_date = data.get('optional_date')

    # Run the prediction in a separate thread
    future = executor.submit(cache_prediction, product_id, time_period, optional_date, 'demand')
    prediction_id = future.result()

    response = {
        'prediction_id': prediction_id,
        'product_id': product_id,
        'predicted_demand': cache[prediction_id]['predicted_value']
    }

    return jsonify(response)

@app.route('/get_data/<prediction_id>', methods=['GET'])
def get_data(prediction_id):
    with cache_lock:
        if prediction_id not in cache:
            return "Data not found", 404
        data_path = cache[prediction_id]['data_path']

    return send_file(data_path, mimetype='text/csv')

def delete_file_if_exists(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")

def clean_cache():
    with cache_lock:
        current_time = datetime.now()
        for prediction_id in list(cache.keys()):
            if current_time - cache[prediction_id]['timestamp'] > timedelta(minutes=1):
                data_path = cache[prediction_id]['data_path']
                delete_file_if_exists(data_path)
                del cache[prediction_id]
                print(f"Removed cache entry and data for prediction_id: {prediction_id}")

# Run cache cleaning every 5 minutes
def cache_cleaning_job():
    clean_cache()
    threading.Timer(300, cache_cleaning_job).start()

if __name__ == '__main__':
    cache_cleaning_job()  # Start the cache cleaning job
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)