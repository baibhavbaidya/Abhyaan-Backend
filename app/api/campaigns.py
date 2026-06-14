from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.db import get_db
from app.models import Campaign, Communication, Segment, Customer, CampaignStatus, CommunicationStatus, ChannelEnum
from app.api.segments import build_query_from_criteria
import httpx
import uuid
import os

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

CHANNEL_STUB_URL = os.getenv("CHANNEL_STUB_URL", "http://localhost:8001")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "http://localhost:8000")


class CampaignCreate(BaseModel):
    name: str
    message: str
    channel: str
    criteria: dict
    segment_name: Optional[str] = None


def send_to_channel_stub(communications: list, message: str, channel: str):
    """
    Fire and forget — sends all communications to channel stub.
    Runs in background so launch API returns immediately.
    """
    with httpx.Client() as client:
        for comm in communications:
            try:
                client.post(
                    f"{CHANNEL_STUB_URL}/send",
                    json={
                        "communication_id": comm["id"],
                        "recipient": comm["contact"],
                        "message": comm["message"],
                        "channel": channel,
                        "callback_url": f"{CRM_BASE_URL}/api/receipts"
                    },
                    timeout=5.0
                )
            except Exception as e:
                print(f"Failed to send communication {comm['id']}: {e}")


@router.post("/")
def create_and_launch_campaign(
    body: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a segment, create a campaign, create communications,
    and fire them to the channel stub — all in one step.
    """

    # Step 1 — build segment from criteria
    query = build_query_from_criteria(body.criteria, db)
    customers = query.all()

    if not customers:
        raise HTTPException(
            status_code=400,
            detail="No customers match this criteria."
        )

    # Step 2 — save segment
    segment = Segment(
        id=str(uuid.uuid4()),
        name=body.segment_name or body.name,
        criteria=body.criteria,
        customer_count=len(customers),
    )
    db.add(segment)
    db.flush()

    # Step 3 — save campaign
    campaign = Campaign(
        id=str(uuid.uuid4()),
        name=body.name,
        segment_id=segment.id,
        message=body.message,
        channel=ChannelEnum(body.channel),
        status=CampaignStatus.running,
        total_sent=len(customers),
        launched_at=datetime.now(),
    )
    db.add(campaign)
    db.flush()

    # Step 4 — create one communication per customer
    communications_to_send = []

    for customer in customers:
        comm_id = str(uuid.uuid4())

        # Personalise message with customer name
        personalised_message = body.message.replace("{name}", customer.name)

        # Pick contact based on channel
        if body.channel == "whatsapp" or body.channel == "sms":
            contact = customer.phone
        else:
            contact = customer.email

        comm = Communication(
            id=comm_id,
            campaign_id=campaign.id,
            customer_id=customer.id,
            status=CommunicationStatus.sent,
            sent_at=datetime.now(),
        )
        db.add(comm)

        communications_to_send.append({
            "id": comm_id,
            "contact": contact,
            "message": personalised_message,
        })

    db.commit()

    # Step 5 — send to channel stub in background
    background_tasks.add_task(
        send_to_channel_stub,
        communications_to_send,
        body.message,
        body.channel
    )

    return {
        "success": True,
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "total_sent": len(customers),
        "channel": body.channel,
        "status": "running",
        "message": f"Campaign launched to {len(customers)} customers."
    }


@router.get("/")
def get_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    return {
        "campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "channel": c.channel,
                "status": c.status,
                "total_sent": c.total_sent,
                "delivered": c.delivered,
                "failed": c.failed,
                "opened": c.opened,
                "clicked": c.clicked,
                "launched_at": c.launched_at,
                "created_at": c.created_at,
            }
            for c in campaigns
        ]
    }


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {
        "id": campaign.id,
        "name": campaign.name,
        "channel": campaign.channel,
        "message": campaign.message,
        "status": campaign.status,
        "total_sent": campaign.total_sent,
        "delivered": campaign.delivered,
        "failed": campaign.failed,
        "opened": campaign.opened,
        "clicked": campaign.clicked,
        "launched_at": campaign.launched_at,
        "created_at": campaign.created_at,
    }

@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Delete communications first
    db.query(Communication).filter(Communication.campaign_id == campaign_id).delete()
    
    # Delete campaign
    db.delete(campaign)
    db.commit()
    
    return {"success": True, "message": "Campaign deleted"}