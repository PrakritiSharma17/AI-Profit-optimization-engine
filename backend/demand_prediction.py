"""
AI Demand Prediction Engine
Uses Random Forest and XGBoost models to predict product demand
"""
import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
from database import execute_query, insert_transaction


class DemandPredictionEngine:
    """ML-based demand prediction using Random Forest and XGBoost"""
    
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'cost_price', 'competitor_price', 'selling_price', 'inventory_level',
            'customer_interest_score', 'price_sensitivity_score',
            'day_of_week', 'month', 'is_weekend',
            'previous_sales', 'historical_sales', 'competitor_count',
            'seasonal_factor', 'market_trend'
        ]
        self.model_path = f"models/demand_{model_type}_model.pkl"
        self.scaler_path = f"models/demand_scaler.pkl"
        
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        
        # Try to load existing model
        self.load_model()
    
    def prepare_training_data(self):
        """Fetch historical data and prepare for training"""
        try:
            # Get historical transactions with product data
            one_year_ago = datetime.now() - timedelta(days=365)
            query = """
            SELECT 
                p.cost_price,
                AVG(cp.competitor_price) as avg_competitor_price,
                t.selling_price as selling_price,
                p.stock_quantity as inventory_level,
                COALESCE(cb.interest_score, 50) as customer_interest_score,
                COALESCE(cb.price_sensitivity_score, 50) as price_sensitivity_score,
                t.transaction_date as transaction_date,
                t.quantity as previous_sales,
                t.quantity as historical_sales,
                COUNT(DISTINCT cp.competitor_name) as competitor_count,
                1.0 as seasonal_factor,
                1.0 as market_trend,
                t.quantity as demand_actual
            FROM transactions t
            JOIN products p ON t.product_id = p.product_id
            LEFT JOIN competitor_prices cp ON p.product_id = cp.product_id
            LEFT JOIN customer_behavior cb ON p.product_id = cb.product_id 
                AND DATE(cb.recorded_date) = DATE(t.transaction_date)
            WHERE t.transaction_date >= %s
            GROUP BY p.product_id, t.transaction_date
            HAVING COUNT(*) > 0
            LIMIT 10000
            """
            
            data = execute_query(query, (one_year_ago.isoformat(),), fetch_all=True)
            
            if not data or len(data) < 50:
                print("Warning: Insufficient historical data for training (< 50 records)")
                return None
            
            df = pd.DataFrame(data)
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['day_of_week'] = df['transaction_date'].dt.weekday + 1
            df['month'] = df['transaction_date'].dt.month
            df['is_weekend'] = (df['transaction_date'].dt.weekday >= 5).astype(int)
            df['historical_sales'] = df['previous_sales']
            df['market_trend'] = 1.0
            
            # Handle missing values
            df = df.fillna(df.mean(numeric_only=True))
            
            # Features and target
            X = df[[col for col in self.feature_names if col in df.columns]].astype(float)
            y = df['demand_actual'].astype(float)
            
            # Ensure all features are present
            for feature in self.feature_names:
                if feature not in X.columns:
                    X[feature] = 0.0
            
            X = X[self.feature_names]  # Reorder columns
            
            return X, y
        
        except Exception as e:
            print(f"Error preparing training data: {e}")
            return None
    
    def train(self):
        """Train the demand prediction model"""
        try:
            data = self.prepare_training_data()
            
            if data is None:
                print("Cannot train: Insufficient data")
                return False
            
            X, y = data
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            if self.model_type == 'random_forest':
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
                self.model.fit(X_train_scaled, y_train)
            
            elif self.model_type == 'xgboost':
                self.model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                )
                self.model.fit(X_train_scaled, y_train)
            
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            
            # Save model and scaler
            self.save_model()
            
            # Save metrics to database
            self._save_metrics(mae, mse, rmse, r2, len(X_train))
            
            print(f"✓ {self.model_type.upper()} Model trained successfully")
            print(f"  MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
            
            return True
        
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def predict(self, features_dict):
        """
        Predict demand for given features
        Returns predicted demand and confidence score
        """
        try:
            if self.model is None:
                print("Warning: Model not trained. Using fallback prediction.")
                return self._fallback_prediction(features_dict)
            
            # Create feature vector
            feature_vector = []
            for feature in self.feature_names:
                feature_vector.append(features_dict.get(feature, 0.0))
            
            X = np.array(feature_vector).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            
            # Calculate confidence score (0-100) based on model
            if self.model_type == 'random_forest':
                # Use standard deviation of tree predictions
                predictions = np.array([
                    tree.predict(X_scaled)[0] 
                    for tree in self.model.estimators_
                ])
                std = np.std(predictions)
                # Lower std = higher confidence
                confidence = max(0, 100 - (std / prediction * 100)) if prediction > 0 else 50
            else:
                # For XGBoost, use a simpler confidence metric
                confidence = 75
            
            confidence = round(min(100, max(0, confidence)), 2)
            
            return {
                'predicted_demand': max(0, int(prediction)),
                'confidence_score': confidence,
                'model_type': self.model_type
            }
        
        except Exception as e:
            print(f"Error in prediction: {e}")
            return self._fallback_prediction(features_dict)
    
    def _fallback_prediction(self, features_dict):
        """Fallback prediction logic when model is not available"""
        base_demand = 50

        customer_interest = features_dict.get('customer_interest_score', 50)
        if customer_interest > 75:
            base_demand += 20
        elif customer_interest < 25:
            base_demand -= 20

        competitor_price = features_dict.get('competitor_price', 0)
        cost = features_dict.get('cost_price', 100)
        selling_price = features_dict.get('selling_price', cost)
        historical_sales = features_dict.get('historical_sales', 0)
        market_trend = features_dict.get('market_trend', 1.0)
        inventory_level = features_dict.get('inventory_level', 0)
        price_sensitivity = features_dict.get('price_sensitivity_score', 50)

        if competitor_price > 0:
            if selling_price < competitor_price * 0.95:
                base_demand += 10
            elif selling_price > competitor_price * 1.05:
                base_demand -= 10

        if selling_price > cost * 1.2:
            base_demand -= 10
        elif selling_price < cost * 1.05:
            base_demand += 5

        if historical_sales and historical_sales > 0:
            base_demand += min(20, historical_sales / 25)

        if inventory_level > 200 and customer_interest < 40:
            base_demand -= 10

        if market_trend > 1.0:
            base_demand += min(15, (market_trend - 1.0) * 20)
        elif market_trend < 1.0:
            base_demand -= min(15, (1.0 - market_trend) * 20)

        if features_dict.get('is_weekend', 0) == 1:
            base_demand += 5

        if price_sensitivity > 70 and selling_price > cost * 1.1:
            base_demand -= 5
        elif price_sensitivity < 30 and selling_price < competitor_price:
            base_demand += 5

        return {
            'predicted_demand': max(10, int(base_demand)),
            'confidence_score': 50.0,
            'model_type': 'fallback'
        }
    
    def save_model(self):
        """Save trained model and scaler"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print(f"✓ Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load previously trained model and scaler"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                print(f"✓ Model loaded from {self.model_path}")
                return True
        except Exception as e:
            print(f"Warning: Could not load model: {e}")
        
        return False
    
    def _save_metrics(self, mae, mse, rmse, r2, samples):
        """Save model metrics to database"""
        try:
            execute_query(
                """INSERT INTO model_metrics 
                   (model_type, accuracy, mse, rmse, mean_absolute_error, samples_used, model_version)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (self.model_type, r2, mse, rmse, mae, samples, '1.0')
            )
        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")
    
    def predict_for_price_point(self, product_id, test_price, cost_price, competitor_price=None):
        """
        Predict demand for a specific price point
        Used for optimization
        """
        try:
            # Get current product behavior
            behavior = execute_query(
                """SELECT * FROM customer_behavior WHERE product_id = %s 
                   ORDER BY recorded_date DESC LIMIT 1""",
                (product_id,),
                fetch_one=True
            )
            
            features = {
                'cost_price': float(cost_price),
                'competitor_price': float(competitor_price) if competitor_price else 0,
                'selling_price': float(test_price),
                'inventory_level': 100,  # Placeholder
                'customer_interest_score': float(behavior['interest_score']) if behavior else 50,
                'price_sensitivity_score': float(behavior['price_sensitivity_score']) if behavior else 50,
                'day_of_week': datetime.now().weekday() + 1,
                'month': datetime.now().month,
                'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
                'previous_sales': 50,  # Placeholder
                'competitor_count': 3,  # Placeholder
                'seasonal_factor': 1.0
            }
            
            return self.predict(features)
        
        except Exception as e:
            print(f"Error predicting for price point: {e}")
            return self._fallback_prediction({})
