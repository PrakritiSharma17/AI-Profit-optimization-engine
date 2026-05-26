import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from excel_handler import validate_and_process_file
from pricing_engine import PricingEngine
from groq_service import GroqService

load_dotenv()

app = Flask(__name__)
# Enable CORS for frontend requests
CORS(app)

# Initialize Services
pricing_engine = PricingEngine()
groq_service = GroqService()

# In-memory history for temporary storage
history = []

@app.route('/predict-price', methods=['POST'])
def predict_price():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Calculate prediction
        prediction = pricing_engine.calculate_prediction(data)
        
        # Build the prompt for Groq
        prompt_data = {
            "product_name": data.get("product_name", "Unknown Product"),
            "cost_price": data.get("cost_price", 0),
            "competitor_price": data.get("competitor_price", 0),
            "optimized_price": prediction["optimized_price"],
            "demand_level": data.get("demand_level", "Medium"),
            "stock": data.get("stock", 0)
        }
        
        # Get AI recommendation
        ai_response = groq_service.get_recommendation([prompt_data])
        prediction['ai_recommendation'] = ai_response

        # Save to history
        history.append(prediction)

        return jsonify(prediction), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            # Parse excel/csv to list of dicts
            df_records = validate_and_process_file(file)
            
            # Predict each row
            results = []
            for row in df_records:
                pred = pricing_engine.calculate_prediction(row)
                pred['original_data'] = row
                results.append(pred)

            # Optional: Batch AI recommendation for the overview
            # For simplicity, we can get a single AI summary based on the highest risk or lowest margin product, or just return the data and let the frontend query.

            # Save batch to history
            history.extend(results)

            return jsonify({'message': 'File processed successfully', 'results': results}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/market-trend', methods=['GET'])
def get_market_trend():
    # Simulated simple market trend data for charting
    trends = [
        {"month": "Jan", "demand": 65, "competitorAvg": 120},
        {"month": "Feb", "demand": 72, "competitorAvg": 118},
        {"month": "Mar", "demand": 85, "competitorAvg": 115},
        {"month": "Apr", "demand": 80, "competitorAvg": 110},
        {"month": "May", "demand": 95, "competitorAvg": 105},
        {"month": "Jun", "demand": 110, "competitorAvg": 100},
    ]
    return jsonify({'trends': trends}), 200

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({'history': history}), 200

@app.route('/ai-recommendation', methods=['POST'])
def get_ai_recommendation():
    try:
        data = request.json
        # Batch analysis
        recommendation = groq_service.get_recommendation(data.get('items', []))
        return jsonify({'recommendation': recommendation}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'message': 'AI Based Profit Optimization Engine API',
        'endpoints': {
            'predict-price': 'POST /predict-price',
            'upload-excel': 'POST /upload-excel',
            'market-trend': 'GET /market-trend',
            'history': 'GET /history',
            'ai-recommendation': 'POST /ai-recommendation'
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
