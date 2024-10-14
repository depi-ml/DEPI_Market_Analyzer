from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd

app = Flask(__name__)

PREDICTION_SERVER_URL = 'http://localhost:5002'
SENTIMENT_SERVER_URL = 'http://localhost:5000'

product_id_name_mapping = pd.DataFrame()


def load_products():
    global product_id_name_mapping
    product_id_name_mapping = pd.read_csv('static/data/annex4.csv')
    return [{'product_id': row['Item Code'], 'product_name': row['Item Name']} for _, row in
            product_id_name_mapping.iterrows()]


products_data = load_products()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sentiment_analysis')
def sentiment_analysis():
    return render_template('sentiment_analysis.html')

@app.route('/get_products', methods=['GET'])
def get_products():
    # Serve product list as JSON for Streamlit dropdown
    return jsonify(products_data)

# -----Prediction part -----
def get_prediction(endpoint, data):
    try:
        url = f'{PREDICTION_SERVER_URL}/{endpoint}'
        product_id = data.get('product_id', None)
        time_period = data.get('time_period', None)
        optional_date = data.get('optional_date', None)

        if product_id and (time_period or optional_date):
            response = requests.post(url, json={
                'product_id': product_id,
                'time_period': time_period,
                'optional_date': optional_date
            })
            response.raise_for_status()

            result = response.json()
            
            # Get the data_path using the prediction_id
            result['data_path'] = f'{PREDICTION_SERVER_URL}/get_data/{result["prediction_id"]}'

            result['product_name'] = \
                product_id_name_mapping[product_id_name_mapping['Item Code'] == product_id]['Item Name'].iloc[0]

            result['optional_date'] = optional_date

            if endpoint == 'predict_price':
                prediction_name = 'predicted_price'
                result["type"] = "Price"
            else:
                prediction_name = 'predicted_demand'
                result["type"] = "Demand"

            if result[prediction_name]:
                result[prediction_name] = round(result[prediction_name], 2)

            return result
        
        else:
            return "Error: Product ID or time period is missing", 400

    except requests.RequestException as e:
        return {"error": f"An error occurred while communicating with the ML server: {str(e)}"}

@app.route('/price_prediction', methods=['POST'])
def price_prediction():
    data = request.json
    result = get_prediction('predict_price', data)
    return jsonify(result)

@app.route('/demand_prediction', methods=['POST'])
def demand_prediction():
    data = request.json
    result = get_prediction('predict_demand', data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)