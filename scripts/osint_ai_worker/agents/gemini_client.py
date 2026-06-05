import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-pro" # or gemini-2.0-flash

    def generate_json(self, prompt: str) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {}

def extract_signals(news_content: str) -> dict:
    prompt = f"""
    You are a Quant Researcher and Macro-Economic Analyst.
    Analyze the following news text and extract key macroeconomic signals.
    Categories: [Policy, Liquidity, Inflation, Growth, Market Sentiment]

    News Text: {news_content}

    Respond in JSON format with a list of signals. Example:
    {{
        "signals": [
            {{
                "category": "Policy",
                "signal": "Hawkish",
                "confidence": 0.85,
                "reason": "The Fed chair explicitly mentioned higher for longer rates."
            }}
        ]
    }}
    """
    client = GeminiClient()
    return client.generate_json(prompt)
