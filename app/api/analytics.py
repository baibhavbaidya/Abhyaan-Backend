from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Campaign, Communication, CommunicationStatus
from app.services.ai_service import get_campaign_insight

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/campaigns/{campaign_id}")
def get_campaign_analytics(campaign_id: str, db: Session = Depends(get_db)):
    # Step 1 — get campaign
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Step 2 — calculate rates
    total_sent = campaign.total_sent or 1  # avoid division by zero

    delivery_rate = round((campaign.delivered / total_sent) * 100, 1)
    failure_rate = round((campaign.failed / total_sent) * 100, 1)
    open_rate = round(
        (campaign.opened / campaign.delivered * 100) if campaign.delivered > 0 else 0, 1
    )
    click_rate = round(
        (campaign.clicked / campaign.opened * 100) if campaign.opened > 0 else 0, 1
    )

    stats = {
        "total_sent": campaign.total_sent,
        "delivered": campaign.delivered,
        "failed": campaign.failed,
        "opened": campaign.opened,
        "clicked": campaign.clicked,
        "delivery_rate": delivery_rate,
        "failure_rate": failure_rate,
        "open_rate": open_rate,
        "click_rate": click_rate,
    }

    # Step 3 — get AI insight
    insight = get_campaign_insight(stats, campaign.channel)

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "channel": campaign.channel,
        "status": campaign.status,
        "launched_at": campaign.launched_at,
        "stats": stats,
        "ai_insight": insight,
    }


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """
    Overall stats across all campaigns — for dashboard summary.
    """
    campaigns = db.query(Campaign).all()

    total_campaigns = len(campaigns)
    total_sent = sum(c.total_sent or 0 for c in campaigns)
    total_delivered = sum(c.delivered or 0 for c in campaigns)
    total_opened = sum(c.opened or 0 for c in campaigns)
    total_clicked = sum(c.clicked or 0 for c in campaigns)

    return {
        "total_campaigns": total_campaigns,
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
        "overall_delivery_rate": round(
            (total_delivered / total_sent * 100) if total_sent > 0 else 0, 1
        ),
        "overall_open_rate": round(
            (total_opened / total_delivered * 100) if total_delivered > 0 else 0, 1
        ),
        "overall_click_rate": round(
            (total_clicked / total_opened * 100) if total_opened > 0 else 0, 1
        ),
    }