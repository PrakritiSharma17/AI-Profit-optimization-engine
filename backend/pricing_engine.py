class PricingEngine:
    def __init__(self):
        # Example constants / weights
        self.PROFIT_MARGIN_BASE = 0.20 # 20% base margin

    def calculate_prediction(self, data: dict) -> dict:
        """
        Input keys typically:
        product_name, cost_price, competitor_price, demand_level, stock, customer_interest, seasonal_factor
        """
        try:
            name = data.get('product_name', 'Unknown')
            cost = float(data.get('cost_price', 0))
            comp_price = float(data.get('competitor_price', 0)) if data.get('competitor_price') else 0
            demand_level = str(data.get('demand_level', 'Medium')).lower()
            stock = int(data.get('stock', 0))
            customer_interest = float(data.get('customer_interest', 50)) # 0 to 100
            seasonal_factor = float(data.get('seasonal_factor', 1.0)) # 1.0 is neutral

            # Base calculation
            base_price = cost * (1 + self.PROFIT_MARGIN_BASE)

            # Adjustments
            adjustment = 1.0
            
            # Demand effect
            if demand_level == 'high':
                adjustment += 0.15
            elif demand_level == 'low':
                adjustment -= 0.10

            # Interest effect
            if customer_interest > 80:
                adjustment += 0.05
            elif customer_interest < 30:
                adjustment -= 0.05

            # Seasonality
            adjustment *= seasonal_factor

            # Preliminary calculated price
            calculated_price = base_price * adjustment

            # Competitive Adjustment
            if comp_price > 0:
                if calculated_price > comp_price * 1.1:
                    calculated_price = comp_price * 1.05 # Cap it slightly above competitor if demand is very high, else match
                elif calculated_price < comp_price * 0.9:
                    calculated_price = comp_price * 0.95 # Don't underprice too much

            # Ensure we don't sell below cost
            if calculated_price <= cost:
                calculated_price = cost * 1.05 # 5% absolute minimum margin

            optimized_price = round(calculated_price, 2)
            estimated_profit = round(optimized_price - cost, 2)
            profit_margin = round((estimated_profit / optimized_price) * 100, 2) if optimized_price > 0 else 0

            # Demand Score
            base_demand_score = 50
            if demand_level == 'high': base_demand_score += 30
            elif demand_level == 'low': base_demand_score -= 20
            
            demand_score = min(100, int(base_demand_score + (customer_interest * 0.2) + (seasonal_factor * 10 - 10)))

            # Risk Score
            # High risk if stock is very high and demand is low, or margin is too thin
            risk_score = 10
            if stock > 500 and demand_level == 'low':
                risk_score += 40
            if profit_margin < 10:
                risk_score += 30
            elif profit_margin > 40:
                risk_score += 10 # Pricing too high can be risky
                
            risk_score = min(100, risk_score)
            
            # Pricing Category
            category = "Competitive"
            if optimized_price > comp_price * 1.05 and comp_price > 0:
                category = "Premium"
            elif optimized_price < comp_price * 0.95 and comp_price > 0:
                category = "Discount"
            
            if comp_price == 0:
                category = "Standard"

            return {
                "product_name": name,
                "optimized_price": optimized_price,
                "estimated_profit": estimated_profit,
                "profit_margin_percent": profit_margin,
                "demand_score": demand_score,
                "risk_score": risk_score,
                "pricing_category": category,
                "stock": stock
            }
        except ValueError as e:
            raise ValueError(f"Error parsing numerical values: {str(e)}")
