from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import get_db
from app.api.customers import get_customer_stats
from app.api.segments import build_query_from_criteria
from app.services.ai_service import parse_chat_intent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str


@router.post("/")
def chat(body: ChatMessage, db: Session = Depends(get_db)):
    """
    Convert natural language campaign intent into a pre-filled campaign.
    """

    # Step 1 — get current customer stats for context
    stats = get_customer_stats(db)

    # Step 2 — send message + stats to AI
    result = parse_chat_intent(body.message, stats)

    # Step 3 — if AI returned an error
    if result.get("error"):
        return {
            "success": False,
            "error": result["error"]
        }

    # Step 4 — build actual segment from AI criteria
    criteria = result.get("criteria", {})

    if not criteria:
        return {
            "success": False,
            "error": "I could not identify a clear segment from your request. Try being more specific, for example: 'customers who spent over ₹2000 but haven't bought in 30 days'."
        }

    query = build_query_from_criteria(criteria, db)
    customer_count = query.count()

    if customer_count == 0:
        return {
            "success": False,
            "error": "No customers match this criteria. Try adjusting your filters."
        }

    # Step 5 — return pre-filled campaign details
    return {
        "success": True,
        "campaign_name": result.get("campaign_name", "New Campaign"),
        "reasoning": result.get("reasoning", ""),
        "criteria": criteria,
        "customer_count": customer_count,
        "suggested_message": result.get("suggested_message", ""),
        "suggested_channel": result.get("suggested_channel", "whatsapp"),
    }