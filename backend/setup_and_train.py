"""
Comprehensive Setup and Training Script
Initializes database, generates sample data, and trains all models
"""
import random
from datetime import datetime, timedelta
from database import (
    create_tables, execute_query, insert_or_update_product,
    insert_competitor_price, insert_transaction, update_customer_behavior,
    use_sqlite
)
from model_retraining import ModelRetrainingPipeline


def generate_sample_training_data():
    """Generate realistic sample training data for model training"""
    print("\n[DATA] Generating sample training data...")
    
    products = [
        {'name': 'Wireless Headphones', 'cost': 30, 'category': 'Electronics'},
        {'name': 'USB-C Cable', 'cost': 5, 'category': 'Electronics'},
        {'name': 'Phone Case', 'cost': 8, 'category': 'Accessories'},
        {'name': 'Screen Protector', 'cost': 3, 'category': 'Accessories'},
        {'name': 'Portable Charger', 'cost': 20, 'category': 'Electronics'},
        {'name': 'Laptop Stand', 'cost': 15, 'category': 'Office'},
        {'name': 'Mouse Pad', 'cost': 6, 'category': 'Office'},
        {'name': 'Webcam', 'cost': 35, 'category': 'Electronics'},
        {'name': 'Keyboard', 'cost': 50, 'category': 'Electronics'},
        {'name': 'Monitor Arm', 'cost': 40, 'category': 'Office'},
    ]
    
    product_ids = {}
    
    for product in products:
        try:
            prod_id = insert_or_update_product(
                product_name=product['name'],
                cost_price=product['cost'],
                current_price=product['cost'] * 2.5,
                stock=random.randint(50, 500),
                category=product['category']
            )
            product_ids[product['name']] = prod_id
            print(f"  [OK] Created product: {product['name']} (ID: {prod_id})")
        except Exception as e:
            print(f"  [ERROR] Error creating product {product['name']}: {e}")
    
    # Generate competitor prices
    print("\n[DATA] Adding competitor prices...")
    competitor_count = 0
    for product_name, prod_id in product_ids.items():
        try:
            cost = next(p['cost'] for p in products if p['name'] == product_name)
            insert_competitor_price(prod_id, 'competitor_a', cost * random.uniform(2.0, 3.0))
            insert_competitor_price(prod_id, 'competitor_b', cost * random.uniform(2.0, 3.0))
            insert_competitor_price(prod_id, 'market_avg', cost * random.uniform(2.0, 3.0))
            competitor_count += 3
        except Exception as e:
            print(f"  [ERROR] Error adding competitor prices: {e}")
    
    print(f"  [OK] Added {competitor_count} competitor prices")
    
    # Generate transaction history (training data)
    print("\n[DATA] Generating 365 days of transaction data...")
    transaction_count = 0
    
    for product_name, prod_id in product_ids.items():
        cost = next(p['cost'] for p in products if p['name'] == product_name)
        for days_back in range(365):
            try:
                # Simulate different volumes across days
                base_demand = random.randint(10, 50)
                day_factor = 1.0
                
                # Higher demand on weekends/holidays
                today = datetime.now() - timedelta(days=days_back)
                if today.weekday() >= 4:  # Weekend
                    day_factor = 1.3
                
                quantity = max(1, int(base_demand * day_factor * random.uniform(0.8, 1.2)))
                price = cost * random.uniform(2.0, 3.5)
                revenue = price * quantity
                
                insert_transaction(
                    product_id=prod_id,
                    selling_price=price,
                    quantity=quantity,
                    total_revenue=revenue
                )
                transaction_count += 1
            except Exception as e:
                pass
    
    print(f"  [OK] Generated {transaction_count} transactions")
    
    # Generate customer behavior data
    print("\n[DATA] Generating customer behavior data...")
    behavior_count = 0
    
    for product_name, prod_id in product_ids.items():
        try:
            update_customer_behavior(
                product_id=prod_id,
                views=random.randint(100, 500),
                clicks=random.randint(10, 100),
                cart_adds=random.randint(5, 50),
                purchases=random.randint(2, 30),
                session_dur=random.randint(10, 600),
                conversion=random.uniform(0.01, 0.15),
                interest_score=random.randint(30, 90),
                sensitivity=random.randint(20, 100)
            )
            behavior_count += 1
        except Exception as e:
            pass
    
    print(f"  [OK] Generated {behavior_count} behavior records")
    
    return len(product_ids)


def train_all_models():
    """Train all demand prediction models"""
    print("\n[ML] Training ML models...")
    
    try:
        pipeline = ModelRetrainingPipeline(check_interval_hours=24)
        result = pipeline.retrain_all_models(force=True)
        print(f"  [OK] Model training completed: {result}")
        return True
    except Exception as e:
        print(f"  [ERROR] Error during model training: {e}")
        return False


def verify_setup():
    """Verify that all components are working"""
    print("\n[VERIFY] Verifying system setup...")
    
    checks = {
        'Database Connected': False,
        'Tables Created': False,
        'Sample Data Generated': False,
        'Models Trained': False
    }
    
    try:
        # Check database connection
        result = execute_query("SELECT COUNT(*) as count FROM products", (), fetch_one=True)
        if result:
            checks['Database Connected'] = True
            checks['Tables Created'] = True
            
            product_count = result.get('count', 0)
            if product_count > 0:
                checks['Sample Data Generated'] = True
        
        # Check if models are trained
        result = execute_query(
            "SELECT COUNT(*) as count FROM model_metrics WHERE model_type = %s",
            ('random_forest',),
            fetch_one=True
        )
        if result and result.get('count', 0) > 0:
            checks['Models Trained'] = True
    except Exception as e:
        print(f"  [ERROR] Error during verification: {e}")
    
    print("\n  Status Report:")
    for check, passed in checks.items():
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"    {symbol} {check}")
    
    return all(checks.values())


def main():
    """Main setup routine"""
    print("=" * 60)
    print("[SETUP] AI Pricing Engine - Setup & Training")
    print("=" * 60)
    
    # Step 1: Create database tables
    print("\n[INIT] Step 1: Initializing database...")
    try:
        create_tables()
        print("  [OK] Database tables created")
    except Exception as e:
        print(f"  [ERROR] Error creating tables: {e}")
        return False
    
    # Step 2: Generate sample data
    print("\n[DATA] Step 2: Generating sample data...")
    try:
        product_count = generate_sample_training_data()
        print(f"  [OK] Sample data generated ({product_count} products)")
    except Exception as e:
        print(f"  [ERROR] Error generating data: {e}")
        return False
    
    # Step 3: Train models
    print("\n[ML] Step 3: Training ML models...")
    try:
        if train_all_models():
            print("  [OK] All models trained successfully")
        else:
            print("  [WARN] Model training had issues but continuing")
    except Exception as e:
        print(f"  [ERROR] Error training models: {e}")
        return False
    
    # Step 4: Verify setup
    print("\n[VERIFY] Step 4: Verifying setup...")
    if verify_setup():
        print("  [OK] All systems operational")
    else:
        print("  [WARN] Some systems may not be fully operational")
    
    print("\n" + "=" * 60)
    print("[DONE] Setup complete! Ready to use the pricing engine.")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
