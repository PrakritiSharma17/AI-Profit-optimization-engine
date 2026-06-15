"""
Advanced AI Recommendation Engine
Generates intelligent business recommendations based on model outputs
"""
from datetime import datetime
from database import execute_query, use_sqlite


class AdvancedRecommendationEngine:
    """Generates intelligent business recommendations"""
    
    def __init__(self):
        self.recommendation_types = {
            'pricing_strategy',
            'inventory_management',
            'competitor_analysis',
            'demand_forecast',
            'risk_alert',
            'customer_engagement',
            'promotional_opportunity'
        }
    
    def generate_comprehensive_recommendations(self, product_id, pricing_decision, 
                                              demand_prediction, behavior_insights,
                                              volatility_assessment):
        """
        Generate comprehensive business recommendations
        """
        recommendations = []
        
        # Pricing strategy recommendations
        pricing_rec = self._generate_pricing_recommendations(
            product_id, pricing_decision, demand_prediction
        )
        recommendations.extend(pricing_rec)
        
        # Inventory recommendations
        inventory_rec = self._generate_inventory_recommendations(
            product_id, demand_prediction
        )
        recommendations.extend(inventory_rec)
        
        # Competitor analysis
        competitor_rec = self._generate_competitor_recommendations(product_id)
        recommendations.extend(competitor_rec)
        
        # Customer engagement
        engagement_rec = self._generate_engagement_recommendations(
            product_id, behavior_insights
        )
        recommendations.extend(engagement_rec)
        
        # Risk alerts
        risk_rec = self._generate_risk_alerts(
            product_id, pricing_decision, volatility_assessment
        )
        recommendations.extend(risk_rec)
        
        # Promotional opportunities
        promo_rec = self._generate_promotional_opportunities(
            product_id, demand_prediction, behavior_insights
        )
        recommendations.extend(promo_rec)
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations
    
    def _generate_pricing_recommendations(self, product_id, pricing_decision, demand_prediction):
        """Generate pricing strategy recommendations"""
        recommendations = []
        
        predicted_demand = demand_prediction.get('predicted_demand', 0)
        confidence = demand_prediction.get('confidence_score', 0)
        recommended_price = pricing_decision.get('optimized_price', 0)
        estimated_profit = pricing_decision.get('estimated_profit', 0)
        profit_margin = pricing_decision.get('profit_margin_percent', 0)
        category = pricing_decision.get('pricing_category', 'Competitive')
        
        # High demand + low margin
        if predicted_demand > 100 and profit_margin < 15:
            recommendations.append({
                'product_id': product_id,
                'type': 'pricing_strategy',
                'priority': 'high',
                'title': 'Increase Price for High Demand',
                'recommendation': f'Product has high predicted demand ({predicted_demand} units) with low margin ({profit_margin}%). Consider increasing price to ₹{recommended_price * 1.05:.2f} to improve profitability.',
                'expected_impact': 'Profit increase of 15-25%',
                'confidence': confidence,
                'action_required': True
            })
        
        # Low demand + high margin
        elif predicted_demand < 30 and profit_margin > 30:
            recommendations.append({
                'product_id': product_id,
                'type': 'pricing_strategy',
                'priority': 'high',
                'title': 'Reduce Price to Boost Volume',
                'recommendation': f'Demand is low ({predicted_demand} units) but margin is high ({profit_margin}%). Consider price reduction to ₹{recommended_price * 0.95:.2f} to increase sales volume.',
                'expected_impact': 'Sales volume increase of 20-40%',
                'confidence': confidence,
                'action_required': True
            })
        
        # Premium positioning
        elif category == 'Premium':
            recommendations.append({
                'product_id': product_id,
                'type': 'pricing_strategy',
                'priority': 'medium',
                'title': 'Premium Pricing Strategy Active',
                'recommendation': f'Product is positioned as premium (₹{recommended_price}). Ensure quality and brand value justify the price premium.',
                'expected_impact': 'Higher profit margins',
                'confidence': confidence,
                'action_required': False
            })
        
        # Discount positioning
        elif category == 'Discount':
            recommendations.append({
                'product_id': product_id,
                'type': 'pricing_strategy',
                'priority': 'medium',
                'title': 'Discount Strategy in Place',
                'recommendation': f'Product uses competitive pricing (₹{recommended_price}). Monitor competitor prices closely to maintain market share.',
                'expected_impact': 'Volume-driven revenue',
                'confidence': confidence,
                'action_required': False
            })
        
        return recommendations
    
    def _generate_inventory_recommendations(self, product_id, demand_prediction):
        """Generate inventory management recommendations"""
        recommendations = []
        
        try:
            # Get current inventory
            product = execute_query(
                "SELECT stock_quantity FROM products WHERE product_id = %s",
                (product_id,),
                fetch_one=True
            )
            
            if not product:
                return recommendations
            
            current_stock = product['stock_quantity']
            predicted_demand = demand_prediction.get('predicted_demand', 50)
            
            # Recommendations based on stock levels
            if current_stock < predicted_demand * 0.5:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'inventory_management',
                    'priority': 'critical',
                    'title': 'Low Stock Alert - Reorder Urgently',
                    'recommendation': f'Current stock ({current_stock} units) is below 50% of predicted demand ({predicted_demand} units). Risk of stockouts. Reorder immediately.',
                    'expected_impact': 'Avoid lost sales from stockouts',
                    'action_required': True
                })
            
            elif current_stock < predicted_demand:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'inventory_management',
                    'priority': 'high',
                    'title': 'Reorder Stock Soon',
                    'recommendation': f'Stock level ({current_stock}) is below predicted demand ({predicted_demand}). Plan reorder for next 7 days.',
                    'expected_impact': 'Maintain availability',
                    'action_required': True
                })
            
            elif current_stock > predicted_demand * 3:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'inventory_management',
                    'priority': 'medium',
                    'title': 'Excess Stock - Consider Promotions',
                    'recommendation': f'Stock level ({current_stock}) exceeds 3x predicted demand ({predicted_demand}). Consider promotions or discounts to reduce inventory.',
                    'expected_impact': 'Free up working capital',
                    'action_required': True
                })
            
            else:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'inventory_management',
                    'priority': 'low',
                    'title': 'Inventory Levels Optimal',
                    'recommendation': f'Stock level ({current_stock}) aligns well with predicted demand ({predicted_demand}). Maintain current reorder schedule.',
                    'expected_impact': 'Optimal cash flow',
                    'action_required': False
                })
        
        except Exception as e:
            print(f"Error generating inventory recommendations: {e}")
        
        return recommendations
    
    def _generate_competitor_recommendations(self, product_id):
        """Generate competitor analysis recommendations"""
        recommendations = []
        
        try:
            # Get competitor prices
            competitors = execute_query(
                """SELECT competitor_name, competitor_price FROM competitor_prices 
                   WHERE product_id = %s ORDER BY last_updated DESC LIMIT 5""",
                (product_id,),
                fetch_all=True
            )
            
            if not competitors:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'competitor_analysis',
                    'priority': 'medium',
                    'title': 'Set Up Competitor Monitoring',
                    'recommendation': 'No competitor data found. Set up automated competitor price monitoring to make informed pricing decisions.',
                    'expected_impact': 'Better competitive positioning',
                    'action_required': True
                })
                return recommendations
            
            # Get current product price
            product = execute_query(
                "SELECT current_price FROM products WHERE product_id = %s",
                (product_id,),
                fetch_one=True
            )
            
            if not product:
                return recommendations
            
            current_price = product['current_price']
            competitor_prices = [c['competitor_price'] for c in competitors]
            avg_competitor = sum(competitor_prices) / len(competitor_prices)
            min_competitor = min(competitor_prices)
            max_competitor = max(competitor_prices)
            
            if current_price < min_competitor:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'competitor_analysis',
                    'priority': 'high',
                    'title': 'Price Below Market - Verify Quality',
                    'recommendation': f'Your price (₹{current_price}) is below all competitors (₹{min_competitor}-₹{max_competitor}). Verify product quality/differentiation justifies this.',
                    'expected_impact': 'Market share gains or margin concerns',
                    'action_required': True
                })
            
            elif current_price > max_competitor * 1.15:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'competitor_analysis',
                    'priority': 'high',
                    'title': 'Price Premium Over Competitors',
                    'recommendation': f'Your price (₹{current_price}) is significantly above competitors (avg ₹{avg_competitor:.2f}). Ensure brand justifies 15%+ premium.',
                    'expected_impact': 'May lose price-sensitive customers',
                    'action_required': True
                })
            
            else:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'competitor_analysis',
                    'priority': 'low',
                    'title': 'Competitive Pricing Maintained',
                    'recommendation': f'Your price (₹{current_price}) is competitive within market range (₹{min_competitor}-₹{max_competitor}, avg ₹{avg_competitor:.2f}).',
                    'expected_impact': 'Balanced market position',
                    'action_required': False
                })
        
        except Exception as e:
            print(f"Error generating competitor recommendations: {e}")
        
        return recommendations
    
    def _generate_engagement_recommendations(self, product_id, behavior_insights):
        """Generate customer engagement recommendations"""
        recommendations = []
        
        if not behavior_insights:
            return recommendations
        
        interest = behavior_insights.get('latest_interest_score', 50)
        sensitivity = behavior_insights.get('latest_price_sensitivity', 50)
        conversion = behavior_insights.get('conversion_rate_trend', 'stable')
        
        if interest > 80 and conversion == 'increasing':
            recommendations.append({
                'product_id': product_id,
                'type': 'customer_engagement',
                'priority': 'medium',
                'title': 'Capitalize on High Engagement',
                'recommendation': 'Customer interest and conversion rates are strong. Create premium content/features to deepen engagement and justify premium pricing.',
                'expected_impact': 'Higher customer lifetime value',
                'action_required': True
            })
        
        elif interest < 30:
            recommendations.append({
                'product_id': product_id,
                'type': 'customer_engagement',
                'priority': 'high',
                'title': 'Low Engagement - Content Refresh Needed',
                'recommendation': 'Customer engagement is low. Revamp product descriptions, images, and marketing content to increase interest.',
                'expected_impact': 'Increased views and conversions',
                'action_required': True
            })
        
        elif sensitivity > 75:
            recommendations.append({
                'product_id': product_id,
                'type': 'customer_engagement',
                'priority': 'medium',
                'title': 'Price-Sensitive Customers - Use Transparency',
                'recommendation': 'Customers are price-sensitive. Emphasize value proposition and provide clear price justification.',
                'expected_impact': 'Reduced price resistance',
                'action_required': True
            })
        
        return recommendations
    
    def _generate_risk_alerts(self, product_id, pricing_decision, volatility_assessment):
        """Generate risk alerts"""
        recommendations = []
        
        risk_score = pricing_decision.get('risk_score', 0)
        profit_margin = pricing_decision.get('profit_margin_percent', 0)
        volatility = volatility_assessment.get('volatility_score', 0)
        volatility_status = volatility_assessment.get('status', 'stable')
        
        # High risk score
        if risk_score > 70:
            recommendations.append({
                'product_id': product_id,
                'type': 'risk_alert',
                'priority': 'critical',
                'title': 'High Risk Alert',
                'recommendation': f'Risk score is high ({risk_score}). Review inventory levels, margins, and competitive positioning.',
                'expected_impact': 'Prevent losses',
                'action_required': True
            })
        
        # Low profit margin
        if profit_margin < 5:
            recommendations.append({
                'product_id': product_id,
                'type': 'risk_alert',
                'priority': 'critical',
                'title': 'Dangerously Low Profit Margin',
                'recommendation': f'Profit margin is {profit_margin}% - below sustainable levels. Increase price or reduce costs immediately.',
                'expected_impact': 'Avoid losses',
                'action_required': True
            })
        
        # Market volatility
        if volatility_status == 'critical':
            recommendations.append({
                'product_id': product_id,
                'type': 'risk_alert',
                'priority': 'critical',
                'title': 'Extreme Market Volatility Detected',
                'recommendation': 'Extreme price volatility detected in market. Apply shock guard and avoid aggressive price changes.',
                'expected_impact': 'Protect customer trust and brand stability',
                'action_required': True
            })
        
        elif volatility_status == 'high':
            recommendations.append({
                'product_id': product_id,
                'type': 'risk_alert',
                'priority': 'high',
                'title': 'High Market Volatility',
                'recommendation': 'Elevated market volatility. Use gradual price transitions to avoid customer shock.',
                'expected_impact': 'Maintain customer satisfaction',
                'action_required': True
            })
        
        return recommendations
    
    def _generate_promotional_opportunities(self, product_id, demand_prediction, behavior_insights):
        """Generate promotional opportunities"""
        recommendations = []
        
        try:
            # Get transaction history
            if use_sqlite:
                recent_sales_query = """SELECT COUNT(*) as count, AVG(quantity) as avg_qty 
                   FROM transactions 
                   WHERE product_id = ? 
                   AND transaction_date >= datetime('now', '-' || ? || ' days')"""
                recent_sales_params = (product_id, 30)
            else:
                recent_sales_query = """SELECT COUNT(*) as count, AVG(quantity) as avg_qty 
                   FROM transactions 
                   WHERE product_id = %s 
                   AND transaction_date >= DATE_SUB(NOW(), INTERVAL %s DAY)"""
                recent_sales_params = (product_id, 30)

            recent_sales = execute_query(recent_sales_query, recent_sales_params, fetch_one=True)
            
            if not recent_sales:
                return recommendations
            
            predicted_demand = demand_prediction.get('predicted_demand', 50)
            recent_count = recent_sales['count'] if recent_sales['count'] else 0
            
            # Low recent sales + high predicted demand
            if recent_count < 5 and predicted_demand > 50:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'promotional_opportunity',
                    'priority': 'high',
                    'title': 'Flash Sale Opportunity',
                    'recommendation': f'Low recent sales ({recent_count} transactions) but high predicted demand. Run a limited-time promotion to capture market interest.',
                    'expected_impact': '30-50% sales increase',
                    'action_required': True
                })
            
            # High predicted demand
            if predicted_demand > 150:
                recommendations.append({
                    'product_id': product_id,
                    'type': 'promotional_opportunity',
                    'priority': 'medium',
                    'title': 'Bundle Deal Opportunity',
                    'recommendation': f'Very high predicted demand ({predicted_demand} units). Create bundle deals with complementary products.',
                    'expected_impact': 'Increase average transaction value',
                    'action_required': True
                })
        
        except Exception as e:
            print(f"Error generating promotional opportunities: {e}")
        
        return recommendations
