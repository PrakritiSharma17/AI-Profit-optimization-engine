import pandas as pd
import io

def validate_and_process_file(file):
    """
    Reads an uploaded .xlsx or .csv file and validates required columns.
    Returns a list of dictionaries for each row.
    """
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file format. Please upload .csv or .xlsx")
            
    except Exception as e:
        raise Exception(f"Failed to read file: {str(e)}")

    # Standardize column names for ease of use (e.g., lowercased, stripped, spaces replaced by underscores)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Required columns map to our logic
    required_cols = [
        'product_name', 
        'cost_price', 
        'competitor_price', 
        'demand_level', 
        'stock', 
        'customer_interest', 
        'seasonal_factor'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
        
    # Fill NA values with sensible defaults
    df['competitor_price'] = df['competitor_price'].fillna(0)
    df['demand_level'] = df['demand_level'].fillna('Medium')
    df['stock'] = df['stock'].fillna(0)
    df['customer_interest'] = df['customer_interest'].fillna(50)
    df['seasonal_factor'] = df['seasonal_factor'].fillna(1.0)
    
    # Convert to list of dicts
    return df.to_dict('records')
