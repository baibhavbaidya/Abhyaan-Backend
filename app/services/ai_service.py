import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def get_opportunities(stats: dict) -> list:
    """
    Given customer stats, ask AI to surface top campaign opportunities.
    """

    prompt = f"""
You are an AI assistant for Brew & Co, a D2C coffee brand in India.
You help the marketing team find the best campaign opportunities.

Here is the current state of the customer base:
- Total customers: {stats['total_customers']}
- Total revenue so far: ₹{stats['total_revenue']}
- Active customers (bought in last 30 days): {stats['active_customers']}
- High value customers inactive 45+ days (spent > ₹3000): {stats['inactive_high_value']}
- First time buyers in last 30 days: {stats['first_time_buyers']}
- VIP customers gone quiet (spent > ₹10000, inactive 30+ days): {stats['vip_gone_quiet']}
- Average order value: ₹{stats['avg_order_value']}

Identify the top 3 campaign opportunities right now.
For each opportunity return:
- title: short name
- reasoning: 1-2 sentences explaining why this is an opportunity right now
- estimated_revenue: realistic rupee estimate of recoverable revenue (integer)
- criteria: filter object using ONLY these keys:
    min_total_spent, max_total_spent, inactive_days, active_days,
    min_total_orders, max_total_orders, city, first_time_buyer
- suggested_message: personalised message draft using {{name}} as placeholder
- suggested_channel: one of whatsapp, sms, email
- urgency: one of high, medium, low

Return ONLY a valid JSON array. No explanation, no markdown, no backticks.
Example format:
[
  {{
    "title": "...",
    "reasoning": "...",
    "estimated_revenue": 150000,
    "criteria": {{"inactive_days": 45, "min_total_spent": 3000}},
    "suggested_message": "Hey {{name}}, ...",
    "suggested_channel": "whatsapp",
    "urgency": "high"
  }}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code blocks if AI wraps in them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    opportunities = json.loads(raw)
    return opportunities


def parse_chat_intent(user_message: str, stats: dict) -> dict:
    """
    Convert natural language campaign intent into structured filter criteria.
    """

    prompt = f"""
You are an AI assistant for Brew & Co, a D2C coffee brand in India.
A marketer wants to create a campaign. Convert their intent into structured filters.

Marketer says: "{user_message}"

Current customer base context:
- Total customers: {stats['total_customers']}
- Avg order value: ₹{stats['avg_order_value']}
- Total revenue: ₹{stats['total_revenue']}

Available filter keys you can use:
- min_total_spent: minimum lifetime spend in rupees (integer)
- max_total_spent: maximum lifetime spend in rupees (integer)
- inactive_days: hasn't purchased in X days (integer)
- active_days: has purchased within last X days (integer)
- min_total_orders: minimum number of orders (integer)
- max_total_orders: maximum number of orders (integer)
- city: one of Mumbai, Delhi, Bangalore, Hyderabad, Chennai (string)
- first_time_buyer: true if only bought once (boolean)

Return ONLY a valid JSON object with these fields. No markdown, no backticks:
{{
  "criteria": {{...filters to apply...}},
  "campaign_name": "short descriptive name",
  "reasoning": "1 sentence explaining the segment chosen",
  "suggested_message": "personalised message using {{name}} as placeholder",
  "suggested_channel": "whatsapp or sms or email",
  "error": null
}}

If the request is unclear or impossible to map to filters, set error to a helpful message
and return empty criteria.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    return result


def get_campaign_insight(stats: dict, channel: str) -> str:
    """
    After campaign runs, generate AI insight on performance.
    """

    prompt = f"""
You are a CRM analyst for Brew & Co, a D2C coffee brand in India.
Analyse this campaign performance and give a short actionable insight.

Campaign stats:
- Channel: {channel}
- Total sent: {stats['total_sent']}
- Delivered: {stats['delivered']} ({stats.get('delivery_rate', 0)}%)
- Failed: {stats['failed']}
- Opened: {stats['opened']} ({stats.get('open_rate', 0)}%)
- Clicked: {stats['clicked']} ({stats.get('click_rate', 0)}%)

Give a 2-3 sentence insight:
1. How did this campaign perform?
2. What worked or didn't work?
3. One specific recommendation for the next campaign to this segment.

Be direct and specific. No fluff. Use rupee and Indian context where relevant.
Return plain text only, no markdown.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    return response.choices[0].message.content.strip()