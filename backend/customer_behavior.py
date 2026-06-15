"""
Customer Behavior Analytics Module
Tracks and analyzes customer interactions to calculate interest and price sensitivity scores
"""
import math
from datetime import datetime
from database import update_customer_behavior, execute_query


class CustomerBehaviorAnalytics:
    """Analyzes customer behavior and calculates engagement metrics"""
    
    def __init__(self):
        self.weights = {
            'views': 0.15,
            'clicks': 0.20,
            'cart': 0.25,
            'purchase': 0.40,
            'session': 0.10
        }
    
    def calculate_interest_score(self, views, clicks, cart_adds, purchases, session_duration):
        """
        Calculate Customer Interest Score (0-100)
        Based on engagement metrics
        """
        # Normalize metrics (assuming reasonable ranges)
        view_norm = min(views / 100, 1.0)  # Normalize to 100 views
        click_norm = min(clicks / 50, 1.0)  # Normalize to 50 clicks
        cart_norm = min(cart_adds / 20, 1.0)  # Normalize to 20 cart additions
        purchase_norm = min(purchases / 5, 1.0)  # Normalize to 5 purchases
        session_norm = min(session_duration / 3600, 1.0)  # Normalize to 1 hour in seconds
        
        # Weighted calculation
        interest_score = (
            self.weights['views'] * view_norm * 100 +
            self.weights['clicks'] * click_norm * 100 +
            self.weights['cart'] * cart_norm * 100 +
            self.weights['purchase'] * purchase_norm * 100 +
            self.weights['session'] * session_norm * 100
        )
        
        return round(min(interest_score, 100), 2)
    
    def calculate_price_sensitivity(self, historical_purchases, price_changes, purchase_changes):
        """
        Calculate Customer Price Sensitivity Score (0-100)
        High score = highly price sensitive (elastic demand)
        Low score = price insensitive (inelastic demand)
        
        Uses elasticity concept: % change in quantity / % change in price
        """
        if not historical_purchases or len(price_changes) == 0:
            return 50.0  # Default neutral score
        
        try:
            elasticities = []
            
            for i in range(len(price_changes)):
                if price_changes[i] != 0 and historical_purchases[i] != 0:
                    elasticity = abs(purchase_changes[i] / price_changes[i])
                    elasticities.append(elasticity)
            
            if not elasticities:
                return 50.0
            
            avg_elasticity = sum(elasticities) / len(elasticities)
            
            # Convert elasticity to 0-100 scale
            # Higher elasticity -> higher sensitivity score
            sensitivity = min((avg_elasticity / 2) * 100, 100)
            
            return round(sensitivity, 2)
        
        except Exception as e:
            print(f"Error calculating price sensitivity: {e}")
            return 50.0  # Default neutral score
    
    def calculate_click_through_rate(self, impressions, clicks):
        """Calculate CTR as a percentage"""
        if impressions == 0:
            return 0.0
        return round((clicks / impressions) * 100, 2)
    
    def calculate_conversion_rate(self, visitors, purchases):
        """Calculate conversion rate as a percentage"""
        if visitors == 0:
            return 0.0
        return round((purchases / visitors) * 100, 2)
    
    def calculate_average_session_duration(self, total_session_time, sessions):
        """Calculate average session duration in minutes"""
        if sessions == 0:
            return 0.0
        return round((total_session_time / sessions) / 60, 2)  # Convert to minutes
    
    def track_customer_behavior(self, product_id, views, clicks, cart_adds, 
                                purchases, session_time_seconds):
        """
        Track customer behavior for a product
        Updates database with calculated metrics
        """
        try:
            # Calculate derived metrics
            click_through_rate = self.calculate_click_through_rate(views, clicks)
            conversion_rate = self.calculate_conversion_rate(views, purchases)
            interest_score = self.calculate_interest_score(
                views, clicks, cart_adds, purchases, session_time_seconds
            )
            
            # For price sensitivity, we need historical data
            # This is a simplified calculation based on current metrics
            price_sensitivity = 50 + (interest_score / 2) - 25  # Simplified relationship
            price_sensitivity = round(max(0, min(100, price_sensitivity)), 2)
            
            # Update database
            update_customer_behavior(
                product_id=product_id,
                views=views,
                clicks=click_through_rate,
                cart_adds=cart_adds,
                purchases=purchases,
                session_dur=session_time_seconds,
                conversion=conversion_rate,
                interest_score=interest_score,
                sensitivity=price_sensitivity
            )
            
            return {
                'product_id': product_id,
                'views': views,
                'click_through_rate': click_through_rate,
                'cart_additions': cart_adds,
                'purchase_frequency': purchases,
                'session_duration_seconds': session_time_seconds,
                'conversion_rate': conversion_rate,
                'interest_score': interest_score,
                'price_sensitivity_score': price_sensitivity,
                'tracked_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error tracking customer behavior: {e}")
            raise
    
    def get_behavior_insights(self, product_id):
        """Get insights from customer behavior data"""
        try:
            behavior = execute_query(
                """SELECT * FROM customer_behavior WHERE product_id = %s 
                   ORDER BY recorded_date DESC LIMIT 5""",
                (product_id,),
                fetch_all=True
            )
            
            if not behavior:
                return None
            
            latest = behavior[0]
            
            insights = {
                'product_id': product_id,
                'latest_interest_score': latest['interest_score'],
                'latest_price_sensitivity': latest['price_sensitivity_score'],
                'conversion_rate_trend': self._calculate_trend([b['conversion_rate'] for b in behavior]),
                'click_rate_trend': self._calculate_trend([b['click_through_rate'] for b in behavior]),
                'avg_interest_score': sum(b['interest_score'] for b in behavior) / len(behavior),
                'recommendation': self._generate_behavior_recommendation(latest)
            }
            
            return insights
        
        except Exception as e:
            print(f"Error getting behavior insights: {e}")
            return None
    
    def _calculate_trend(self, values):
        """Calculate trend direction: 'increasing', 'decreasing', or 'stable'"""
        if len(values) < 2:
            return 'stable'
        
        recent = values[0]
        previous = values[-1]
        change = ((recent - previous) / previous) * 100 if previous != 0 else 0
        
        if change > 5:
            return 'increasing'
        elif change < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_behavior_recommendation(self, behavior_data):
        """Generate recommendation based on behavior"""
        interest = behavior_data['interest_score']
        sensitivity = behavior_data['price_sensitivity_score']
        conversion = behavior_data['conversion_rate']
        
        if interest > 75 and conversion > 5:
            return "High engagement product - Consider premium pricing strategy"
        elif interest > 75 and conversion < 2:
            return "High interest but low conversion - Optimize product presentation or pricing"
        elif sensitivity > 75:
            return "Price sensitive customers - Use competitive pricing strategy"
        elif interest < 30:
            return "Low engagement - Review marketing or product positioning"
        else:
            return "Moderate engagement - Maintain current strategy with minor optimizations"
