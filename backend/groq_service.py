import os
import json
from groq import Groq

class GroqService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
                self.client = None
        else:
            print("Warning: GROQ_API_KEY not found in environment. Using local fallback recommendations.")

    def get_recommendation(self, products_data: list) -> dict:
        """
        Calls Groq API to analyze the given product data.
        Returns a structured recommendation dictionary.
        """
        if not self.client:
            return self._fallback_recommendation(products_data)

        # Build prompt
        prompt = self._build_prompt(products_data)

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI Pricing Analyst and Business Consultant. Provide concise, actionable JSON format recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-8b-8192",
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            response_text = chat_completion.choices[0].message.content
            # Ensure it is parsed as JSON
            return json.loads(response_text)

        except Exception as e:
            print(f"Groq API Error: {e}")
            return self._fallback_recommendation(products_data)

    def _build_prompt(self, products_data: list) -> str:
        data_str = json.dumps(products_data, indent=2)
        return f"""
Analyze the following product pricing and demand data:
{data_str}

Please generate a business recommendation that includes:
1. pricing_suggestion (A brief sentence on overall pricing health)
2. market_insight (Observation on competitiveness and demand)
3. demand_explanation (Why the demand score affects the price)
4. profit_advice (Actionable tip to increase profit margins without losing sales)

Return ONLY a strictly valid JSON object with the exact keys: 'pricing_suggestion', 'market_insight', 'demand_explanation', 'profit_advice'.
"""

    def _fallback_recommendation(self, products_data: list) -> dict:
        """Fallback logic if API key is missing or call fails."""
        if not products_data:
            return {
                "pricing_suggestion": "No data to evaluate.",
                "market_insight": "Insufficient market data.",
                "demand_explanation": "Need product information for demand analysis.",
                "profit_advice": "Check your data inputs."
            }

        # Simple localized logic for the first item
        item = products_data[0]
        demand = item.get('demand_level', 'Medium')
        
        suggestion = "Maintain current calculated pricing, margins are solid."
        if demand == 'High':
            suggestion = "Capitalize on high demand by holding prices firm or slightly increasing."
        elif demand == 'Low':
            suggestion = "Consider bundle deals or slight discounts to move stale stock."

        return {
            "pricing_suggestion": suggestion,
            "market_insight": "Local Fallback: Assuming stable competitive environment due to missing AI data.",
            "demand_explanation": f"Demand is currently {demand}, adjusting stock levels is advised.",
            "profit_advice": "Monitor competitor pricing closely and maintain a minimum 15% margin where possible."
        }
