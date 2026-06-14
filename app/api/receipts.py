from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import update
from pydantic import BaseModel
from datetime import datetime
from app.db import get_db
from app.models import Communication, Campaign, CommunicationStatus

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

VALID_TRANSITIONS = {
    CommunicationStatus.sent: [CommunicationStatus.delivered, CommunicationStatus.failed],
    CommunicationStatus.delivered: [CommunicationStatus.opened, CommunicationStatus.failed],
    CommunicationStatus.opened: [CommunicationStatus.clicked],
    CommunicationStatus.clicked: [],
    CommunicationStatus.failed: [],
}


class Receipt(BaseModel):
    communication_id: str
    status: str


@router.post("")
def receive_receipt(body: Receipt, db: Session = Depends(get_db)):
    # Step 1 — find the communication
    comm = db.query(Communication).filter(
        Communication.id == body.communication_id
    ).with_for_update().first()  # lock the row

    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    # Step 2 — validate state transition
    try:
        new_status = CommunicationStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    allowed = VALID_TRANSITIONS.get(comm.status, [])

    if new_status not in allowed:
        return {"accepted": False, "reason": f"Invalid transition {comm.status} → {new_status}"}

    # Step 3 — update communication status and timestamp
    comm.status = new_status
    now = datetime.now()

    if new_status == CommunicationStatus.delivered:
        comm.delivered_at = now
    elif new_status == CommunicationStatus.opened:
        comm.opened_at = now
    elif new_status == CommunicationStatus.clicked:
        comm.clicked_at = now
    elif new_status == CommunicationStatus.failed:
        comm.failed_at = now

    # Step 4 — atomic increment on campaign stats (fixes race condition)
    if new_status == CommunicationStatus.delivered:
        db.execute(
            update(Campaign)
            .where(Campaign.id == comm.campaign_id)
            .values(delivered=Campaign.delivered + 1)
        )
    elif new_status == CommunicationStatus.failed:
        db.execute(
            update(Campaign)
            .where(Campaign.id == comm.campaign_id)
            .values(failed=Campaign.failed + 1)
        )
    elif new_status == CommunicationStatus.opened:
        db.execute(
            update(Campaign)
            .where(Campaign.id == comm.campaign_id)
            .values(opened=Campaign.opened + 1)
        )
    elif new_status == CommunicationStatus.clicked:
        db.execute(
            update(Campaign)
            .where(Campaign.id == comm.campaign_id)
            .values(clicked=Campaign.clicked + 1)
        )

    db.commit()

    return {"accepted": True, "communication_id": body.communication_id, "status": body.status}