"""
Price Smoothing & Shock Guard Layer
Prevents sudden price spikes and drops, applies gradual transitions
Detects abnormal market volatility and protects customer trust
"""
from datetime import datetime, timedelta
from database import execute_query, insert_or_update_product, use_sqlite


class PriceSmoothingEngine:
    """Manages price transitions and prevents shock pricing"""
    
    def __init__(self, max_daily_change_percent=5.0, max_weekly_change_percent=15.0):
        """
        Initialize shock guard with configurable thresholds
        
        Args:
            max_daily_change_percent: Max price change allowed per day (default 5%)
            max_weekly_change_percent: Max price change allowed per week (default 15%)
        """
        self.max_daily_change = max_daily_change_percent
        self.max_weekly_change = max_weekly_change_percent
        self.smoothing_steps = 4  # Number of steps to gradually transition price
    
    def get_current_price(self, product_id):
        """Get current price of product"""
        try:
            product = execute_query(
                "SELECT current_price FROM products WHERE product_id = %s",
                (product_id,),
                fetch_one=True
            )
            return float(product['current_price']) if product else None
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
    
    def get_price_history(self, product_id, days=30):
        """Get price history for the last N days"""
        try:
            if use_sqlite:
                history_query = """SELECT previous_price, new_price, change_percent, price_change_date 
                   FROM price_history 
                   WHERE product_id = ? 
                   AND price_change_date >= datetime('now', '-' || ? || ' days')
                   ORDER BY price_change_date DESC"""
                history_params = (product_id, days)
            else:
                history_query = """SELECT previous_price, new_price, change_percent, price_change_date 
                   FROM price_history 
                   WHERE product_id = %s 
                   AND price_change_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                   ORDER BY price_change_date DESC"""
                history_params = (product_id, days)

            history = execute_query(history_query, history_params, fetch_all=True)
            return history if history else []
        except Exception as e:
            print(f"Error getting price history: {e}")
            return []
    
    def detect_volatility(self, product_id):
        """
        Detect abnormal market volatility
        Returns volatility score (0-100) and recommendation
        """
        try:
            history = self.get_price_history(product_id, days=7)
            
            if len(history) < 2:
                return {'volatility_score': 0, 'status': 'stable', 'action': 'none'}
            
            price_changes = [abs(h['change_percent']) for h in history]
            avg_change = sum(price_changes) / len(price_changes)
            max_change = max(price_changes)
            
            # Calculate volatility score
            volatility_score = min(100, (avg_change / self.max_daily_change) * 100)
            
            # Determine status
            if max_change > self.max_daily_change * 2:
                status = 'critical'
                action = 'apply_emergency_smoothing'
            elif avg_change > self.max_daily_change * 1.5:
                status = 'high'
                action = 'increase_smoothing_steps'
            elif avg_change > self.max_daily_change * 0.7:
                status = 'moderate'
                action = 'apply_normal_smoothing'
            else:
                status = 'stable'
                action = 'allow_direct_change'
            
            return {
                'volatility_score': round(volatility_score, 2),
                'average_daily_change': round(avg_change, 2),
                'max_recent_change': round(max_change, 2),
                'status': status,
                'action': action
            }
        
        except Exception as e:
            print(f"Error detecting volatility: {e}")
            return {'volatility_score': 0, 'status': 'unknown', 'action': 'none'}
    
    def apply_shock_guard(self, product_id, current_price, recommended_price):
        """
        Apply shock guard logic to recommended price
        Returns smoothed price transition plan
        """
        try:
            # Get volatility assessment
            volatility = self.detect_volatility(product_id)
            
            # Calculate allowed change percentage
            change_percent = ((recommended_price - current_price) / current_price * 100) if current_price > 0 else 0
            
            # Check if change exceeds daily limit
            if abs(change_percent) <= self.max_daily_change:
                # Direct change is allowed
                return {
                    'current_price': current_price,
                    'recommended_price': recommended_price,
                    'final_price': recommended_price,
                    'applied_price': recommended_price,
                    'change_percent': round(change_percent, 2),
                    'applied_smoothing': False,
                    'smoothing_steps': 1,
                    'price_schedule': [recommended_price],
                    'daily_limit': self.max_daily_change,
                    'volatility_assessment': volatility,
                    'message': 'Price change within safe limits - direct application approved'
                }
            
            # If change exceeds limit, apply smoothing
            if volatility['status'] == 'critical':
                steps = self.smoothing_steps * 2  # Double steps for critical volatility
            elif volatility['status'] == 'high':
                steps = self.smoothing_steps + 1
            else:
                steps = self.smoothing_steps
            
            # Generate smooth price transition
            price_schedule = self._generate_smooth_transition(
                current_price, recommended_price, steps
            )
            
            return {
                'current_price': current_price,
                'recommended_price': recommended_price,
                'final_price': recommended_price,
                'applied_price': price_schedule[0] if price_schedule else current_price,
                'change_percent': round(change_percent, 2),
                'applied_smoothing': True,
                'smoothing_steps': steps,
                'price_schedule': price_schedule,
                'daily_limit': self.max_daily_change,
                'change_applied_daily': round(change_percent / steps, 2),
                'volatility_assessment': volatility,
                'message': f'Price change scheduled over {steps} days to prevent shock'
            }
        
        except Exception as e:
            print(f"Error applying shock guard: {e}")
            return {
                'current_price': current_price,
                'recommended_price': recommended_price,
                'final_price': recommended_price,
                'applied_smoothing': False,
                'error': str(e)
            }
    
    def _generate_smooth_transition(self, start_price, end_price, steps):
        """Generate smooth price transition schedule"""
        if steps <= 1:
            return [end_price]
        
        price_schedule = []
        for i in range(1, steps + 1):
            # Linear interpolation
            progress = i / steps
            price = start_price + (end_price - start_price) * progress
            price_schedule.append(round(price, 2))
        
        return price_schedule
    
    def apply_daily_price_update(self, product_id, current_price, target_price):
        """
        Apply daily price update following shock guard rules
        Returns the price to apply today
        """
        try:
            shock_guard = self.apply_shock_guard(product_id, current_price, target_price)
            
            if not shock_guard.get('applied_smoothing'):
                # Direct change approved
                apply_price = shock_guard['final_price']
            else:
                # Get smoothing schedule
                schedule = shock_guard['price_schedule']
                # Apply the first step
                apply_price = schedule[0] if schedule else current_price
            
            return {
                'apply_price': apply_price,
                'shock_guard': shock_guard,
                'change_percent': round(((apply_price - current_price) / current_price * 100), 2)
            }
        
        except Exception as e:
            print(f"Error applying daily update: {e}")
            return {
                'apply_price': current_price,
                'error': str(e)
            }
    
    def analyze_price_elasticity(self, product_id):
        """
        Analyze price elasticity based on historical data
        Returns elasticity coefficient and recommendations
        """
        try:
            # Get transactions and prices
            if use_sqlite:
                query = """
                SELECT 
                    DATE(t.transaction_date) as date,
                    t.selling_price,
                    t.quantity,
                    p.cost_price
                FROM transactions t
                JOIN products p ON t.product_id = p.product_id
                WHERE t.product_id = ?
                AND t.transaction_date >= datetime('now', '-' || ? || ' days')
                ORDER BY t.transaction_date
                """
                params = (product_id, 90)
            else:
                query = """
                SELECT 
                    DATE(t.transaction_date) as date,
                    t.selling_price,
                    t.quantity,
                    p.cost_price
                FROM transactions t
                JOIN products p ON t.product_id = p.product_id
                WHERE t.product_id = %s
                AND t.transaction_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY t.transaction_date
                """
                params = (product_id, 90)

            data = execute_query(query, params, fetch_all=True)
            
            if len(data) < 10:
                return {
                    'elasticity': 0,
                    'status': 'insufficient_data',
                    'recommendation': 'Need more historical data for elasticity analysis'
                }
            
            # Group by date
            daily_data = {}
            for record in data:
                date = record['date'].isoformat()
                if date not in daily_data:
                    daily_data[date] = {'price': 0, 'quantity': 0, 'count': 0}
                daily_data[date]['price'] += record['selling_price']
                daily_data[date]['quantity'] += record['quantity']
                daily_data[date]['count'] += 1
            
            # Calculate daily averages
            dates = sorted(daily_data.keys())
            prices = []
            quantities = []
            
            for date in dates:
                prices.append(daily_data[date]['price'] / daily_data[date]['count'])
                quantities.append(daily_data[date]['quantity'])
            
            # Calculate elasticity (simplified)
            price_changes = []
            quantity_changes = []
            
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    pct_change_price = (prices[i] - prices[i-1]) / prices[i-1] * 100
                    if quantities[i-1] > 0:
                        pct_change_qty = (quantities[i] - quantities[i-1]) / quantities[i-1] * 100
                        if pct_change_price != 0:
                            elasticity = pct_change_qty / pct_change_price
                            price_changes.append(pct_change_price)
                            quantity_changes.append(elasticity)
            
            if not quantity_changes:
                avg_elasticity = 0
            else:
                avg_elasticity = sum(quantity_changes) / len(quantity_changes)
            
            # Classify elasticity
            if avg_elasticity > 1:
                elasticity_type = 'elastic'
                recommendation = 'Product is price elastic - customers are sensitive to price changes. Use smaller price adjustments.'
            elif avg_elasticity < -1:
                elasticity_type = 'inelastic'
                recommendation = 'Product is price inelastic - demand is stable despite price changes. Can apply larger price adjustments.'
            else:
                elasticity_type = 'unit_elastic'
                recommendation = 'Product has unit elasticity - price and demand are proportionally related.'
            
            return {
                'elasticity_coefficient': round(avg_elasticity, 3),
                'elasticity_type': elasticity_type,
                'samples': len(quantity_changes),
                'recommendation': recommendation
            }
        
        except Exception as e:
            print(f"Error analyzing elasticity: {e}")
            return {
                'elasticity': 0,
                'status': 'error',
                'recommendation': f'Error: {str(e)}'
            }
