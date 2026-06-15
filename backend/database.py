"""
Database connection and schema management for AI Pricing Engine
"""
import os
import sqlite3
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'pricing_engine'),
    'raise_on_warnings': True,
    'use_unicode': True,
    'charset': 'utf8mb4'
}
SQLITE_DB_PATH = Path(os.getenv('SQLITE_DB_PATH', Path(__file__).resolve().parent / 'pricing_engine_fallback.db'))
USE_SQLITE_FALLBACK = os.getenv('DB_FALLBACK_SQLITE', '1').lower() in ('1', 'true', 'yes')

# Combined exception types for MySQL and SQLite
Error = (MySQLError, sqlite3.Error)

connection_pool = None
use_sqlite = False


def _open_sqlite_connection():
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _format_query(query):
    return query.replace('%s', '?') if use_sqlite else query

# Try MySQL first, then fall back to SQLite if MySQL is unavailable.
try:
    print("Attempting MySQL connection pool with user:", DB_CONFIG['user'])
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="pricing_pool",
        pool_size=5,
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("[OK] Connected to MySQL using", DB_CONFIG['user'])
except MySQLError as mysql_error:
    print(f"Error creating MySQL connection pool: {mysql_error}")
    if USE_SQLITE_FALLBACK:
        try:
            print("Falling back to SQLite because MySQL access is unavailable.")
            conn = _open_sqlite_connection()
            conn.close()
            use_sqlite = True
            print("[OK] SQLite fallback database initialized at", SQLITE_DB_PATH)
        except sqlite3.Error as sqlite_error:
            print("Error creating SQLite fallback database:", sqlite_error)
            connection_pool = None
    else:
        connection_pool = None


def get_connection():
    """Get a connection from the pool or SQLite fallback."""
    if use_sqlite:
        return _open_sqlite_connection()

    if connection_pool is None:
        raise Exception("Database connection pool not initialized")
    return connection_pool.get_connection()


def create_tables():
    """Create all required database tables"""
    if connection_pool is None and not use_sqlite:
        print("Warning: Database not available. Skipping table creation.")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if use_sqlite:
            table_statements = [
                """
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL UNIQUE,
                    cost_price REAL NOT NULL,
                    current_price REAL,
                    stock_quantity INTEGER DEFAULT 0,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    selling_price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_revenue REAL NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS customer_behavior (
                    behavior_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    views INTEGER DEFAULT 0,
                    click_through_rate REAL DEFAULT 0,
                    cart_additions INTEGER DEFAULT 0,
                    purchase_frequency INTEGER DEFAULT 0,
                    session_duration INTEGER DEFAULT 0,
                    conversion_rate REAL DEFAULT 0,
                    interest_score REAL DEFAULT 0,
                    price_sensitivity_score REAL DEFAULT 0,
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS competitor_prices (
                    competitor_price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    competitor_name TEXT,
                    competitor_price REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS demand_forecasts (
                    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    predicted_demand INTEGER NOT NULL,
                    confidence_score REAL,
                    forecast_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    forecast_period TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS pricing_decisions (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    previous_price REAL,
                    recommended_price REAL NOT NULL,
                    applied_price REAL,
                    predicted_demand INTEGER,
                    predicted_profit REAL,
                    risk_score INTEGER,
                    pricing_category TEXT,
                    decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied INTEGER DEFAULT 0,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS model_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_type TEXT,
                    accuracy REAL,
                    mse REAL,
                    rmse REAL,
                    mean_absolute_error REAL,
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_retrained TIMESTAMP,
                    samples_used INTEGER,
                    model_version TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    previous_price REAL,
                    new_price REAL,
                    change_percent REAL,
                    price_change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS ai_recommendations (
                    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    recommendation_type TEXT,
                    recommendation_text TEXT,
                    priority TEXT,
                    action_required INTEGER DEFAULT 1,
                    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS pricing_scenarios (
                    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    candidate_price REAL NOT NULL,
                    predicted_demand INTEGER NOT NULL,
                    predicted_profit REAL NOT NULL,
                    predicted_revenue REAL NOT NULL,
                    competitor_gap REAL,
                    demand_change REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
                """
            ]
        else:
            table_statements = [
                """
                CREATE TABLE IF NOT EXISTS products (
                    product_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_name VARCHAR(255) NOT NULL UNIQUE,
                    cost_price DECIMAL(10, 2) NOT NULL,
                    current_price DECIMAL(10, 2),
                    stock_quantity INT DEFAULT 0,
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_product_name (product_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    selling_price DECIMAL(10, 2) NOT NULL,
                    quantity INT NOT NULL,
                    total_revenue DECIMAL(12, 2) NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_transaction (product_id),
                    INDEX idx_date (transaction_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS customer_behavior (
                    behavior_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    views INT DEFAULT 0,
                    click_through_rate DECIMAL(5, 2) DEFAULT 0,
                    cart_additions INT DEFAULT 0,
                    purchase_frequency INT DEFAULT 0,
                    session_duration INT DEFAULT 0,
                    conversion_rate DECIMAL(5, 2) DEFAULT 0,
                    interest_score DECIMAL(5, 2) DEFAULT 0,
                    price_sensitivity_score DECIMAL(5, 2) DEFAULT 0,
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_behavior (product_id),
                    INDEX idx_date (recorded_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS competitor_prices (
                    competitor_price_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    competitor_name VARCHAR(255),
                    competitor_price DECIMAL(10, 2) NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_competitor (product_id),
                    INDEX idx_date (last_updated)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS demand_forecasts (
                    forecast_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    predicted_demand INT NOT NULL,
                    confidence_score DECIMAL(5, 2),
                    forecast_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    forecast_period VARCHAR(50),
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_forecast (product_id),
                    INDEX idx_date (forecast_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS pricing_decisions (
                    decision_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    previous_price DECIMAL(10, 2),
                    recommended_price DECIMAL(10, 2) NOT NULL,
                    applied_price DECIMAL(10, 2),
                    predicted_demand INT,
                    predicted_profit DECIMAL(12, 2),
                    risk_score INT,
                    pricing_category VARCHAR(50),
                    decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_decision (product_id),
                    INDEX idx_date (decision_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS model_metrics (
                    metric_id INT AUTO_INCREMENT PRIMARY KEY,
                    model_type VARCHAR(50),
                    accuracy DECIMAL(5, 3),
                    mse DECIMAL(10, 4),
                    rmse DECIMAL(10, 4),
                    mean_absolute_error DECIMAL(10, 4),
                    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_retrained TIMESTAMP,
                    samples_used INT,
                    model_version VARCHAR(50),
                    INDEX idx_type_date (model_type, training_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    history_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    previous_price DECIMAL(10, 2),
                    new_price DECIMAL(10, 2),
                    change_percent DECIMAL(5, 2),
                    price_change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_history (product_id),
                    INDEX idx_date (price_change_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS ai_recommendations (
                    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    recommendation_type VARCHAR(100),
                    recommendation_text TEXT,
                    priority VARCHAR(20),
                    action_required BOOLEAN DEFAULT TRUE,
                    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_rec (product_id),
                    INDEX idx_date (generated_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,
                """
                CREATE TABLE IF NOT EXISTS pricing_scenarios (
                    scenario_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    candidate_price DECIMAL(10,2) NOT NULL,
                    predicted_demand INT NOT NULL,
                    predicted_profit DECIMAL(12,2) NOT NULL,
                    predicted_revenue DECIMAL(12,2) NOT NULL,
                    competitor_gap DECIMAL(6,2),
                    demand_change DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_product_scenario (product_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            ]

        for statement in table_statements:
            cursor.execute(statement)

        # Create SQLite indexes for fallback if needed
        if use_sqlite:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_name ON products(product_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_transaction ON transactions(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_transaction ON transactions(transaction_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_behavior ON customer_behavior(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_behavior ON customer_behavior(recorded_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_competitor ON competitor_prices(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_competitor ON competitor_prices(last_updated)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_forecast ON demand_forecasts(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_forecast ON demand_forecasts(forecast_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_decision ON pricing_decisions(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_decision ON pricing_decisions(decision_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_date_metrics ON model_metrics(model_type, training_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_history ON price_history(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_history ON price_history(price_change_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_rec ON ai_recommendations(product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_rec ON ai_recommendations(generated_date)")

        conn.commit()
        print("✓ All database tables created successfully")

    except Error as e:
        print(f"Error creating tables: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a SQL query"""
    conn = None
    try:
        conn = get_connection()
        if use_sqlite:
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(dictionary=True)

        formatted_query = _format_query(query)
        if params:
            cursor.execute(formatted_query, params)
        else:
            cursor.execute(formatted_query)

        if fetch_one:
            row = cursor.fetchone()
            result = dict(row) if row is not None else None
            conn.commit()
            return result
        elif fetch_all:
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            conn.commit()
            return result
        else:
            conn.commit()
            return cursor.lastrowid

    except Error as e:
        if conn:
            conn.rollback()
        print(f"Database Error: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()


def insert_or_update_product(product_name, cost_price, current_price=None, stock=0, category=None):
    """Insert or update a product"""
    try:
        # Check if product exists
        existing = execute_query(
            "SELECT product_id FROM products WHERE product_name = %s",
            (product_name,),
            fetch_one=True
        )
        
        if existing:
            # Update
            update_query = """UPDATE products SET cost_price = %s, current_price = %s, 
                   stock_quantity = %s, category = %s, updated_at = NOW() 
                   WHERE product_id = %s"""
            params = (cost_price, current_price, stock, category, existing['product_id'])
            if use_sqlite:
                update_query = update_query.replace("updated_at = NOW()", "updated_at = ?")
                params = (cost_price, current_price, stock, category, datetime.now(), existing['product_id'])
            execute_query(update_query, params)
            return existing['product_id']
        else:
            # Insert
            product_id = execute_query(
                """INSERT INTO products (product_name, cost_price, current_price, stock_quantity, category) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (product_name, cost_price, current_price, stock, category)
            )
            return product_id
    except Error as e:
        print(f"Error in insert_or_update_product: {e}")
        raise


def insert_transaction(product_id, selling_price, quantity, total_revenue):
    """Record a transaction"""
    try:
        return execute_query(
            """INSERT INTO transactions (product_id, selling_price, quantity, total_revenue) 
               VALUES (%s, %s, %s, %s)""",
            (product_id, selling_price, quantity, total_revenue)
        )
    except Error as e:
        print(f"Error inserting transaction: {e}")
        raise


def update_customer_behavior(product_id, views=0, clicks=0, cart_adds=0, purchases=0, 
                            session_dur=0, conversion=0, interest_score=0, sensitivity=0):
    """Update or insert customer behavior data"""
    try:
        # Check if behavior record exists for today
        query = """SELECT behavior_id FROM customer_behavior 
               WHERE product_id = %s AND DATE(recorded_date) = CURDATE()"""
        if use_sqlite:
            query = """SELECT behavior_id FROM customer_behavior 
               WHERE product_id = %s AND DATE(recorded_date) = DATE('now')"""
        existing = execute_query(query, (product_id,), fetch_one=True)
        
        if existing:
            execute_query(
                """UPDATE customer_behavior SET views = %s, click_through_rate = %s, 
                   cart_additions = %s, purchase_frequency = %s, session_duration = %s,
                   conversion_rate = %s, interest_score = %s, price_sensitivity_score = %s
                   WHERE behavior_id = %s""",
                (views, clicks, cart_adds, purchases, session_dur, conversion, 
                 interest_score, sensitivity, existing['behavior_id'])
            )
        else:
            execute_query(
                """INSERT INTO customer_behavior 
                   (product_id, views, click_through_rate, cart_additions, purchase_frequency, 
                    session_duration, conversion_rate, interest_score, price_sensitivity_score)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (product_id, views, clicks, cart_adds, purchases, session_dur, conversion, 
                 interest_score, sensitivity)
            )
    except Error as e:
        print(f"Error updating customer behavior: {e}")
        raise


def get_product_analytics(product_id):
    """Get comprehensive analytics for a product"""
    try:
        analytics = {}
        
        # Product info
        product = execute_query(
            "SELECT * FROM products WHERE product_id = %s",
            (product_id,),
            fetch_one=True
        )
        analytics['product'] = product
        
        # Recent transactions
        transactions = execute_query(
            """SELECT * FROM transactions WHERE product_id = %s 
               ORDER BY transaction_date DESC LIMIT 10""",
            (product_id,),
            fetch_all=True
        )
        analytics['recent_transactions'] = transactions
        
        # Latest behavior
        behavior = execute_query(
            """SELECT * FROM customer_behavior WHERE product_id = %s 
               ORDER BY recorded_date DESC LIMIT 1""",
            (product_id,),
            fetch_one=True
        )
        analytics['behavior'] = behavior
        
        # Latest competitor prices
        competitors = execute_query(
            """SELECT * FROM competitor_prices WHERE product_id = %s 
               ORDER BY last_updated DESC LIMIT 5""",
            (product_id,),
            fetch_all=True
        )
        analytics['competitors'] = competitors
        
        # Latest demand forecast
        forecast = execute_query(
            """SELECT * FROM demand_forecasts WHERE product_id = %s 
               ORDER BY forecast_date DESC LIMIT 1""",
            (product_id,),
            fetch_one=True
        )
        analytics['demand_forecast'] = forecast
        
        # Latest pricing decision
        decision = execute_query(
            """SELECT * FROM pricing_decisions WHERE product_id = %s 
               ORDER BY decision_date DESC LIMIT 1""",
            (product_id,),
            fetch_one=True
        )
        analytics['pricing_decision'] = decision

        # Recent price changes for stability tracking
        price_history = execute_query(
            """SELECT price_change_date, previous_price, new_price, change_percent 
               FROM price_history WHERE product_id = %s 
               ORDER BY price_change_date DESC LIMIT 15""",
            (product_id,),
            fetch_all=True
        )
        analytics['price_history'] = price_history or []
        analytics['volatility_score'] = 0.0
        if analytics['price_history']:
            abs_changes = [abs(item.get('change_percent', 0)) for item in analytics['price_history']]
            analytics['volatility_score'] = round(sum(abs_changes) / len(abs_changes), 2)
        
        return analytics
    
    except Error as e:
        print(f"Error getting product analytics: {e}")
        raise


def get_product_by_name(product_name):
    try:
        return execute_query(
            "SELECT * FROM products WHERE product_name = %s",
            (product_name,),
            fetch_one=True
        )
    except Error as e:
        print(f"Error getting product by name: {e}")
        raise


def get_product_by_id(product_id):
    try:
        return execute_query(
            "SELECT * FROM products WHERE product_id = %s",
            (product_id,),
            fetch_one=True
        )
    except Error as e:
        print(f"Error getting product by id: {e}")
        raise


def list_products(limit=100):
    try:
        return execute_query(
            "SELECT * FROM products ORDER BY updated_at DESC LIMIT %s",
            (limit,),
            fetch_all=True
        )
    except Error as e:
        print(f"Error listing products: {e}")
        raise


def insert_competitor_price(product_id, competitor_name, competitor_price):
    try:
        return execute_query(
            """INSERT INTO competitor_prices 
               (product_id, competitor_name, competitor_price) VALUES (%s, %s, %s)""",
            (product_id, competitor_name, competitor_price)
        )
    except Error as e:
        print(f"Error inserting competitor price: {e}")
        raise


def insert_pricing_decision(product_id, previous_price, recommended_price, applied_price,
                            predicted_demand, predicted_profit, risk_score,
                            pricing_category, applied=False):
    try:
        return execute_query(
            """INSERT INTO pricing_decisions 
               (product_id, previous_price, recommended_price, applied_price, 
                predicted_demand, predicted_profit, risk_score, pricing_category, applied) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (product_id, previous_price, recommended_price, applied_price,
             predicted_demand, predicted_profit, risk_score, pricing_category, applied)
        )
    except Error as e:
        print(f"Error inserting pricing decision: {e}")
        raise


def insert_demand_forecast(product_id, predicted_demand, confidence_score, forecast_period='next_7_days'):
    try:
        return execute_query(
            """INSERT INTO demand_forecasts 
               (product_id, predicted_demand, confidence_score, forecast_period) 
               VALUES (%s, %s, %s, %s)""",
            (product_id, predicted_demand, confidence_score, forecast_period)
        )
    except Error as e:
        print(f"Error inserting demand forecast: {e}")
        raise


def insert_price_history(product_id, previous_price, new_price, change_percent):
    try:
        return execute_query(
            """INSERT INTO price_history 
               (product_id, previous_price, new_price, change_percent) 
               VALUES (%s, %s, %s, %s)""",
            (product_id, previous_price, new_price, change_percent)
        )
    except Error as e:
        print(f"Error inserting price history: {e}")
        raise


def insert_ai_recommendation(product_id, recommendation_type, recommendation_text, priority='medium', action_required=True):
    try:
        return execute_query(
            """INSERT INTO ai_recommendations 
               (product_id, recommendation_type, recommendation_text, priority, action_required) 
               VALUES (%s, %s, %s, %s, %s)""",
            (product_id, recommendation_type, recommendation_text, priority, action_required)
        )
    except Error as e:
        print(f"Error inserting AI recommendation: {e}")
        raise


def insert_pricing_scenario(product_id, candidate_price, predicted_demand, predicted_profit, predicted_revenue, competitor_gap=None, demand_change=None):
    try:
        return execute_query(
            """INSERT INTO pricing_scenarios 
               (product_id, candidate_price, predicted_demand, predicted_profit, predicted_revenue, competitor_gap, demand_change) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (product_id, candidate_price, predicted_demand, predicted_profit, predicted_revenue, competitor_gap, demand_change)
        )
    except Error as e:
        print(f"Error inserting pricing scenario: {e}")
        raise


if __name__ == "__main__":
    create_tables()
