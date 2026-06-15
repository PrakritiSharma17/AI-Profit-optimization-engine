# AI-Based Dynamic Pricing Backend

## Overview
This backend implements a fully automated AI-driven pricing engine for dynamic pricing and profit optimization.

### Key features
- MySQL-backed data storage and normalized schema for products, transactions, customer behavior, competitor prices, forecasts, pricing decisions, and model metrics.
- AI demand prediction using Random Forest (with XGBoost support).
- Dynamic pricing optimization with revenue/profit evaluation over candidate price scenarios.
- Price smoothing / shock guard to prevent abrupt price swings.
- Customer behavior analytics and scoring.
- Automated model retraining pipeline and performance reporting.
- AI recommendation engine to generate pricing, inventory, competitor, and risk recommendations.
- Flask API endpoints for prediction, analytics, behavior tracking, model retraining, and database initialization.

## Setup
1. Copy `.env.example` to `.env` and set your MySQL credentials.
2. Create the MySQL database named in `DB_NAME` or run the `/init-db` endpoint to create tables.
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend:
   ```bash
   python app.py
   ```

## Endpoints
- `GET /init-db` - Create required MySQL tables.
- `POST /predict-price` - Run AI-driven price optimization for a single product.
- `POST /upload-excel` - Process Excel/CSV with multiple products.
- `POST /track-behavior` - Record customer behavior metrics.
- `GET /product-insights` - Fetch product analytics by `product_name` or `product_id`.
- `GET /products` - List stored products.
- `POST /retrain-model` - Trigger model retraining.
- `GET /model-performance` - Get model performance metrics.
- `POST /ai-recommendation` - Get an AI recommendation from product data.

## Notes
- The demand model can be retrained automatically as new transaction data arrives.
- If the Groq API key is not configured, the system uses local fallback recommendations.
- The service currently uses placeholder trend data in `/market-trend`; this can be replaced with real market data feeds.
