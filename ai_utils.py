import os
import json
from dotenv import load_dotenv
from google import genai

# Load .env variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print("DEBUG GEMINI KEY:", api_key[:8] if api_key else None)

client = genai.Client(api_key=api_key) if api_key else None

# Fast model suitable for this use case
MODEL_NAME = "gemini-2.5-flash"  # see Gemini quickstart docs [web:153][web:159]


def parse_expense_text(text: str):
    """Use Gemini to extract amount, category, description from free text."""
    if not client:
        return {
            "amount": 0,
            "category": "Misc",
            "description": text.strip() or "No description",
        }

    prompt = f"""
You are an assistant that extracts expense information for a small Indian shop.

User text: "{text}"

Respond with ONLY valid JSON, nothing else.
JSON format:
{{
  "amount": <number>,           // in INR
  "category": "Stock purchase" | "Electricity" | "Rent" | "Salary" | "Misc",
  "description": "<short cleaned-up description>"
}}
"""

    try:
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        content = resp.text.strip()

        # If model added extra text, try to isolate the JSON object
        if not content.startswith("{"):
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end + 1]

        return json.loads(content)

    except Exception as e:
        # Log error and fall back so UI still works
        print("Gemini parse_expense_text error:", e)
        return {
            "amount": 0,
            "category": "Misc",
            "description": text.strip() or "No description",
        }


def generate_insights(expenses_text: str) -> str:
    """Use Gemini to read last 30 days of expenses and give bullet insights."""
    if not client:
        lines = expenses_text.splitlines() if expenses_text else []
        return (
            "Insights are not yet powered by real AI.\n"
            f"Total records considered:\n{len(lines)} expense rows."
        )

    prompt = f"""
You are a friendly financial advisor for a small local shop.

Here are the last 30 days of expenses (one per line):
{expenses_text}

In 3–5 short bullet points, explain:
- Main spending pattern.
- Any categories that look high.
- 1–2 simple tips to save money.

Keep language very simple so a shop owner can understand.
"""

    try:
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return resp.text

    except Exception as e:
        print("Gemini generate_insights error:", e)
        lines = expenses_text.splitlines() if expenses_text else []
        return (
            "AI insights are temporarily unavailable (model error).\n"
            f"Total records considered:\n{len(lines)} expense rows."
        )

