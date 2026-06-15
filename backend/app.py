from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from excel_handler import validate_and_process_file
from database import create_tables, list_products
from ai_pricing_service import AIPricingService
from model_retraining import ModelRetrainingPipeline
from groq_service import GroqService
from setup_and_train import generate_sample_training_data

load_dotenv()

app = Flask(__name__)
# Enable CORS for frontend requests
CORS(app)

# Initialize Services
pricing_service = AIPricingService()
groq_service = GroqService()
retraining_pipeline = ModelRetrainingPipeline()

# In-memory history for temporary storage
history = []

# Frontend build directory for single-host deployment
FRONTEND_DIST = Path(__file__).resolve().parent.parent / 'frontend' / 'dist'

# Initialize database schema on startup if possible
try:
    create_tables()
except Exception as e:
    print(f"Database initialization error: {e}")

@app.route('/api/predict-price', methods=['POST'])
def predict_price():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        prediction = pricing_service.optimize_price(data)
        history.append(prediction)
        return jsonify(prediction), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        df_records = validate_and_process_file(file)
        results = []
        for row in df_records:
            prediction = pricing_service.optimize_price(row)
            prediction['original_data'] = row
            results.append(prediction)
            history.append(prediction)

        return jsonify({'message': 'File processed successfully', 'results': results}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-trend', methods=['GET'])
def get_market_trend():
    # Simulated market trends; can be replaced with DB-backed trends later
    trends = [
        {"month": "Jan", "demand": 65, "competitorAvg": 120},
        {"month": "Feb", "demand": 72, "competitorAvg": 118},
        {"month": "Mar", "demand": 85, "competitorAvg": 115},
        {"month": "Apr", "demand": 80, "competitorAvg": 110},
        {"month": "May", "demand": 95, "competitorAvg": 105},
        {"month": "Jun", "demand": 110, "competitorAvg": 100},
    ]
    return jsonify({'trends': trends}), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({'history': history}), 200

@app.route('/api/track-behavior', methods=['POST'])
def track_behavior():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No behavior data provided'}), 400

        result = pricing_service.track_behavior(data)
        return jsonify({'result': result}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/product-insights', methods=['GET'])
def product_insights():
    try:
        product_name = request.args.get('product_name')
        product_id = request.args.get('product_id')
        insights = pricing_service.get_product_insights(product_name=product_name, product_id=product_id)
        if insights is None:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify({'insights': insights}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = list_products(limit=100)
        return jsonify({'products': products}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrain-model', methods=['POST'])
def retrain_model():
    try:
        payload = request.json or {}
        model_type = payload.get('model_type', 'random_forest')
        force = bool(payload.get('force', False))
        bootstrap_data = bool(payload.get('bootstrap_data', False))

        if bootstrap_data:
            generate_sample_training_data()

        if model_type == 'all':
            train_result = retraining_pipeline.retrain_all_models(force=force)
            retrained = any(result is True for result in train_result.values())
            return jsonify({'retrained': retrained, 'results': train_result}), 200

        should_train = force or retraining_pipeline.should_retrain(model_type=model_type)
        if should_train:
            train_result = retraining_pipeline.retrain_model(model_type=model_type)
            return jsonify({'retrained': train_result}), 200
        return jsonify({'retrained': False, 'message': 'No retraining required at this time'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/model-performance', methods=['GET'])
def model_performance():
    try:
        report = retraining_pipeline.get_model_performance_report()
        return jsonify({'model_performance': report}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-recommendation', methods=['POST'])
def get_ai_recommendation():
    try:
        data = request.json
        recommendation = groq_service.get_recommendation(data.get('items', []))
        return jsonify({'recommendation': recommendation}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/init-db', methods=['GET'])
def init_db():
    try:
        create_tables()
        return jsonify({'message': 'Database tables created or already exist'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'message': 'AI Based Profit Optimization Engine API',
        'endpoints': {
            'predict-price': 'POST /api/predict-price',
            'upload-excel': 'POST /api/upload-excel',
            'market-trend': 'GET /api/market-trend',
            'history': 'GET /api/history',
            'track-behavior': 'POST /api/track-behavior',
            'product-insights': 'GET /api/product-insights',
            'products': 'GET /api/products',
            'retrain-model': 'POST /api/retrain-model',
            'model-performance': 'GET /api/model-performance',
            'ai-recommendation': 'POST /api/ai-recommendation',
            'init-db': 'GET /api/init-db',
            'health': 'GET /api/health'
        }
    }), 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if FRONTEND_DIST.exists():
        if path != '' and (FRONTEND_DIST / path).exists():
            return send_from_directory(str(FRONTEND_DIST), path)
        return send_from_directory(str(FRONTEND_DIST), 'index.html')

    return jsonify({'status': 'api-running', 'message': 'Frontend build not found. Run npm build in frontend first.'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
