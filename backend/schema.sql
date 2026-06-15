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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS competitor_prices (
    competitor_price_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    competitor_name VARCHAR(255),
    competitor_price DECIMAL(10, 2) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_product_competitor (product_id),
    INDEX idx_date (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
