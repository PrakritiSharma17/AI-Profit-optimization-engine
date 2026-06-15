-- Create the database and dedicated application user for the AI pricing engine
CREATE DATABASE IF NOT EXISTS pricing_engine CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'pricing_app'@'localhost' IDENTIFIED BY 'PricingEngine@2026';
CREATE USER IF NOT EXISTS 'pricing_app'@'%' IDENTIFIED BY 'PricingEngine@2026';
GRANT ALL PRIVILEGES ON pricing_engine.* TO 'pricing_app'@'localhost';
GRANT ALL PRIVILEGES ON pricing_engine.* TO 'pricing_app'@'%';
FLUSH PRIVILEGES;
