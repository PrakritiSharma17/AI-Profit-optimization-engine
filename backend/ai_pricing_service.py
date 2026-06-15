"""
AI Pricing Service
Combines demand prediction, pricing optimization, smoothing, and recommendations
"""
from datetime import datetime
from database import (
    get_product_by_name, get_product_by_id, list_products,
    insert_or_update_product, insert_competitor_price,
    insert_pricing_decision, insert_demand_forecast,
    insert_price_history, insert_ai_recommendation,
    insert_pricing_scenario, get_product_analytics,
    execute_query, use_sqlite
)
from pricing_engine import PricingEngine
from demand_prediction import DemandPredictionEngine
from customer_behavior import CustomerBehaviorAnalytics
from price_smoothing import PriceSmoothingEngine
from recommendations_engine import AdvancedRecommendationEngine


class AIPricingService:
    def __init__(self):
        self.pricing_engine = PricingEngine()
        self.demand_engine = DemandPredictionEngine(model_type='random_forest')
        self.behavior_analytics = CustomerBehaviorAnalytics()
        self.shock_guard = PriceSmoothingEngine(max_daily_change_percent=5.0, max_weekly_change_percent=15.0)
        self.recommendation_engine = AdvancedRecommendationEngine()
        self.default_competitor_name = 'market_average'

    def _build_features(self, product_id, data):
        # Get latest behavior and competitor details
        behavior = execute_query(
            "SELECT * FROM customer_behavior WHERE product_id = %s ORDER BY recorded_date DESC LIMIT 1",
            (product_id,), fetch_one=True
        )
        competitor = execute_query(
            "SELECT AVG(competitor_price) as avg_price, COUNT(*) as competitor_count \
               FROM competitor_prices WHERE product_id = %s",
            (product_id,), fetch_one=True
        )
        if use_sqlite:
            transaction_query = "SELECT AVG(quantity) as avg_sales, SUM(quantity) as total_sales \
               FROM transactions WHERE product_id = ? AND transaction_date >= datetime('now', '-' || ? || ' days')"
            transaction_params = (product_id, 30)
        else:
            transaction_query = "SELECT AVG(quantity) as avg_sales, SUM(quantity) as total_sales \
               FROM transactions WHERE product_id = %s AND transaction_date >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            transaction_params = (product_id, 30)

        transaction_stats = execute_query(transaction_query, transaction_params, fetch_one=True)

        current_datetime = datetime.now()
        features = {
            'cost_price': float(data.get('cost_price', 0)),
            'competitor_price': float(data.get('competitor_price', competitor['avg_price'] or 0)),
            'selling_price': float(data.get('current_price', data.get('competitor_price', 0))),
            'inventory_level': int(data.get('stock', 0)),
            'customer_interest_score': float(behavior['interest_score']) if behavior else float(data.get('customer_interest', 50)),
            'price_sensitivity_score': float(behavior['price_sensitivity_score']) if behavior else float(data.get('price_sensitivity', 50)),
            'day_of_week': current_datetime.weekday() + 1,
            'month': current_datetime.month,
            'is_weekend': 1 if current_datetime.weekday() >= 5 else 0,
            'previous_sales': float(transaction_stats['avg_sales'] or 0),
            'historical_sales': float(data.get('historical_sales', transaction_stats['avg_sales'] or 0)),
            'competitor_count': int(competitor['competitor_count'] or 0),
            'seasonal_factor': float(data.get('seasonal_factor', 1.0)),
            'market_trend': float(data.get('market_trend', 1.0))
        }
        return features

    def optimize_price(self, data):
        product_name = data.get('product_name', 'Unnamed Product')
        cost_price = float(data.get('cost_price', 0))
        competitor_price = float(data.get('competitor_price', 0))
        current_price = float(data.get('current_price', competitor_price or cost_price * 1.1))
        stock = int(data.get('stock', 0))
        customer_interest = float(data.get('customer_interest', 50))
        seasonal_factor = float(data.get('seasonal_factor', 1.0))
        historical_sales = int(data.get('historical_sales', 0))
        market_trend = float(data.get('market_trend', 1.0))
        category = data.get('category', None)

        # Persist product record with current pricing context
        product_id = insert_or_update_product(
            product_name=product_name,
            cost_price=cost_price,
            current_price=current_price,
            stock=stock,
            category=category
        )

        # Persist competitor price if provided
        if competitor_price > 0:
            insert_competitor_price(product_id, self.default_competitor_name, competitor_price)

        # Build prediction features
        features = self._build_features(product_id, data)

        demand_prediction = self.demand_engine.predict(features)
        predicted_demand = demand_prediction['predicted_demand']
        confidence_score = demand_prediction['confidence_score']

        # Baseline current performance for comparison
        base_demand_prediction = self.demand_engine.predict(features)
        current_profit = round((current_price - cost_price) * base_demand_prediction['predicted_demand'], 2)
        current_revenue = round(current_price * base_demand_prediction['predicted_demand'], 2)

        # Legacy prediction as guidance for candidate generation only
        legacy_prediction = self.pricing_engine.calculate_prediction({
            'product_name': product_name,
            'cost_price': cost_price,
            'competitor_price': competitor_price,
            'stock': stock,
            'customer_interest': customer_interest,
            'seasonal_factor': seasonal_factor,
            'demand_level': 'Medium'
        })

        candidate_prices = self._generate_candidate_prices(
            cost_price, competitor_price, current_price, legacy_prediction['optimized_price']
        )

        candidate_scenarios, best_price, best_profit, best_revenue, best_demand = self._choose_best_price(
            product_id, candidate_prices, cost_price, competitor_price, current_price, features
        )

        # Apply shock guard smoothing and protection
        stored_product = get_product_by_id(product_id)
        current_price = float(stored_product.get('current_price') or current_price)
        smoothing = self.shock_guard.apply_shock_guard(product_id, current_price, best_price)
        applied_price = smoothing.get('applied_price', smoothing.get('final_price', best_price))

        expected_profit = round((best_price - cost_price) * best_demand, 2)
        expected_revenue = round(best_price * best_demand, 2)
        profit_margin = round(((best_price - cost_price) / best_price) * 100, 2) if best_price else 0

        profit_increase = round(best_profit - current_profit, 2)
        profit_increase_pct = round((profit_increase / current_profit) * 100, 2) if current_profit != 0 else 0
        demand_change = best_demand - base_demand_prediction['predicted_demand']

        if competitor_price > 0:
            if best_price > competitor_price * 1.05:
                competitor_comparison = 'Premium to competitor pricing'
            elif best_price < competitor_price * 0.95:
                competitor_comparison = 'Discount to competitor pricing'
            else:
                competitor_comparison = 'Competitive with market pricing'
        else:
            competitor_comparison = 'No competitor reference available'

        explanation = {
            'reason': 'Selected price that maximizes projected profit from evaluated candidate scenarios.',
            'profit_increase': profit_increase,
            'profit_increase_pct': profit_increase_pct,
            'competitor_comparison': competitor_comparison,
            'demand_impact': demand_change,
            'current_profit': current_profit,
            'current_revenue': current_revenue,
            'baseline_demand': base_demand_prediction['predicted_demand']
        }

        pricing_category = legacy_prediction.get('pricing_category', 'Standard')
        if competitor_price > 0:
            if best_price > competitor_price * 1.05:
                pricing_category = 'Premium'
            elif best_price < competitor_price * 0.95:
                pricing_category = 'Discount'
            else:
                pricing_category = 'Competitive'

        risk_score = legacy_prediction.get('risk_score', 0)
        estimated_profit = round(expected_profit, 2)

        # Persist forecast and decision
        insert_demand_forecast(product_id, predicted_demand, confidence_score)
        insert_pricing_decision(
            product_id=product_id,
            previous_price=current_price,
            recommended_price=best_price,
            applied_price=applied_price,
            predicted_demand=best_demand,
            predicted_profit=estimated_profit,
            risk_score=risk_score,
            pricing_category=pricing_category,
            applied=1 if applied_price != current_price else 0
        )
        insert_price_history(
            product_id=product_id,
            previous_price=current_price,
            new_price=applied_price,
            change_percent=smoothing.get('change_percent', 0)
        )

        # Update current product price after smoothing
        insert_or_update_product(
            product_name=product_name,
            cost_price=cost_price,
            current_price=round(applied_price, 2),
            stock=stock,
            category=category
        )

        ai_recommendations = self.recommendation_engine.generate_comprehensive_recommendations(
            product_id=product_id,
            pricing_decision={
                'optimized_price': best_price,
                'estimated_profit': estimated_profit,
                'profit_margin_percent': profit_margin,
                'risk_score': risk_score,
                'pricing_category': pricing_category
            },
            demand_prediction=demand_prediction,
            behavior_insights=self.behavior_analytics.get_behavior_insights(product_id),
            volatility_assessment=smoothing['volatility_assessment']
        )

        for rec in ai_recommendations:
            insert_ai_recommendation(
                product_id=product_id,
                recommendation_type=rec['type'],
                recommendation_text=rec['recommendation'],
                priority=rec['priority'],
                action_required=rec['action_required']
            )

        for scenario in candidate_scenarios:
            insert_pricing_scenario(
                product_id=product_id,
                candidate_price=scenario['candidate_price'],
                predicted_demand=scenario['predicted_demand'],
                predicted_profit=scenario['predicted_profit'],
                predicted_revenue=scenario['predicted_revenue'],
                competitor_gap=scenario['competitor_gap'],
                demand_change=scenario['demand_change']
            )

        return {
            'product_id': product_id,
            'product_name': product_name,
            'cost_price': cost_price,
            'competitor_price': competitor_price,
            'current_price': current_price,
            'stock': stock,
            'customer_interest_score': customer_interest,
            'seasonal_factor': seasonal_factor,
            'historical_sales': historical_sales,
            'market_trend': market_trend,
            'predicted_demand': predicted_demand,
            'demand_confidence': confidence_score,
            'optimized_price': round(best_price, 2),
            'final_price': round(applied_price, 2),
            'price_schedule': smoothing['price_schedule'],
            'expected_profit': estimated_profit,
            'expected_revenue': round(expected_revenue, 2),
            'profit_margin_percent': profit_margin,
            'pricing_category': pricing_category,
            'risk_score': risk_score,
            'smoothing': smoothing,
            'candidate_scenarios': candidate_scenarios,
            'explanation': explanation,
            'ai_recommendations': ai_recommendations,
            'forecast': {
                'confidence': confidence_score,
                'demand': predicted_demand
            }
        }

    def _generate_candidate_prices(self, cost_price, competitor_price, current_price, legacy_price):
        candidate_prices = set()
        anchors = [current_price, legacy_price, cost_price * 1.05, cost_price * 1.1]
        if competitor_price > 0:
            anchors += [competitor_price * 0.9, competitor_price, competitor_price * 1.05, competitor_price * 1.1]

        for anchor in anchors:
            for pct in [-0.2, -0.15, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2]:
                candidate_prices.add(round(max(cost_price * 1.01, anchor * (1 + pct)), 2))

        # Ensure we include the current price itself and competitor anchor if valid
        candidate_prices.add(round(current_price, 2))
        if competitor_price > 0:
            candidate_prices.add(round(competitor_price, 2))

        candidates = sorted([p for p in candidate_prices if p >= cost_price * 1.01])
        return candidates[:25]

    def _choose_best_price(self, product_id, candidate_prices, cost_price, competitor_price, current_price, features):
        best_price = current_price
        best_profit = -float('inf')
        best_demand = 0
        best_revenue = 0
        candidate_scenarios = []

        baseline_features = features.copy()
        baseline_features['selling_price'] = current_price
        baseline_prediction = self.demand_engine.predict(baseline_features)
        baseline_demand = baseline_prediction['predicted_demand']
        baseline_profit = round((current_price - cost_price) * baseline_demand, 2)

        for price in candidate_prices:
            features_copy = features.copy()
            features_copy['selling_price'] = float(price)
            predicted = self.demand_engine.predict(features_copy)
            predicted_demand = predicted['predicted_demand']
            revenue = round(price * predicted_demand, 2)
            profit = round((price - cost_price) * predicted_demand, 2)
            competitor_gap = round(price - competitor_price, 2) if competitor_price > 0 else None
            demand_change = predicted_demand - baseline_demand

            scenario = {
                'candidate_price': round(price, 2),
                'predicted_demand': predicted_demand,
                'predicted_revenue': revenue,
                'predicted_profit': profit,
                'competitor_gap': competitor_gap,
                'demand_change': demand_change,
                'price_change_pct': round(((price - current_price) / current_price) * 100, 2) if current_price > 0 else 0,
                'confidence_score': predicted.get('confidence_score', 0),
                'model_type': predicted.get('model_type', 'unknown')
            }
            candidate_scenarios.append(scenario)

            if profit > best_profit:
                best_profit = profit
                best_price = price
                best_demand = predicted_demand
                best_revenue = revenue

        candidate_scenarios = sorted(candidate_scenarios, key=lambda item: item['predicted_profit'], reverse=True)
        return candidate_scenarios, best_price, best_profit, best_revenue, best_demand

    def get_product_insights(self, product_name=None, product_id=None):
        if product_name:
            product = get_product_by_name(product_name)
            if not product:
                return None
            product_id = product['product_id']
        if product_id:
            return get_product_analytics(product_id)
        return None

    def track_behavior(self, payload):
        product_id = payload.get('product_id')
        if not product_id:
            product_name = payload.get('product_name')
            if not product_name:
                raise ValueError('product_id or product_name required')
            product = get_product_by_name(product_name)
            if product:
                product_id = product['product_id']
            else:
                raise ValueError('Product not found')

        return self.behavior_analytics.track_customer_behavior(
            product_id=product_id,
            views=int(payload.get('views', 0)),
            clicks=int(payload.get('clicks', 0)),
            cart_adds=int(payload.get('cart_additions', 0)),
            purchases=int(payload.get('purchases', 0)),
            session_time_seconds=int(payload.get('session_duration_seconds', 0))
        )
