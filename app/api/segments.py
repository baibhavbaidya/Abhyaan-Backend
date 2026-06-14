from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from app.models import Segment, Customer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/segments", tags=["segments"])


class SegmentCreate(BaseModel):
    name: str
    criteria: dict


def build_query_from_criteria(criteria: dict, db: Session):
    """
    Converts filter criteria JSON into actual customer IDs.
    This is the function AI's filter output plugs into.
    """
    query = db.query(Customer)
    now = datetime.now()

    if "min_total_spent" in criteria:
        query = query.filter(Customer.total_spent >= criteria["min_total_spent"])

    if "max_total_spent" in criteria:
        query = query.filter(Customer.total_spent <= criteria["max_total_spent"])

    if "inactive_days" in criteria:
        query = query.filter(
            Customer.last_purchase_date < now - timedelta(days=criteria["inactive_days"])
        )

    if "active_days" in criteria:
        query = query.filter(
            Customer.last_purchase_date >= now - timedelta(days=criteria["active_days"])
        )

    if "min_total_orders" in criteria:
        query = query.filter(Customer.total_orders >= criteria["min_total_orders"])

    if "max_total_orders" in criteria:
        query = query.filter(Customer.total_orders <= criteria["max_total_orders"])

    if "city" in criteria:
        query = query.filter(Customer.city == criteria["city"])

    if criteria.get("first_time_buyer"):
        query = query.filter(Customer.total_orders == 1)

    return query


@router.post("/preview")
def preview_segment(body: SegmentCreate, db: Session = Depends(get_db)):
    """
    Preview how many customers match the criteria before saving.
    """
    query = build_query_from_criteria(body.criteria, db)
    customers = query.limit(5).all()
    count = query.count()

    return {
        "count": count,
        "criteria": body.criteria,
        "sample_customers": [
            {
                "id": c.id,
                "name": c.name,
                "city": c.city,
                "total_spent": c.total_spent,
                "total_orders": c.total_orders,
                "last_purchase_date": c.last_purchase_date,
            }
            for c in customers
        ],
    }


@router.post("/")
def create_segment(body: SegmentCreate, db: Session = Depends(get_db)):
    """
    Save a segment with its criteria.
    """
    query = build_query_from_criteria(body.criteria, db)
    count = query.count()

    if count == 0:
        raise HTTPException(
            status_code=400,
            detail="No customers match this criteria. Adjust your filters."
        )

    segment = Segment(
        id=str(uuid.uuid4()),
        name=body.name,
        criteria=body.criteria,
        customer_count=count,
    )

    db.add(segment)
    db.commit()
    db.refresh(segment)

    return {
        "id": segment.id,
        "name": segment.name,
        "criteria": segment.criteria,
        "customer_count": segment.customer_count,
        "created_at": segment.created_at,
    }


@router.get("/")
def get_segments(db: Session = Depends(get_db)):
    segments = db.query(Segment).order_by(Segment.created_at.desc()).all()
    return {
        "segments": [
            {
                "id": s.id,
                "name": s.name,
                "criteria": s.criteria,
                "customer_count": s.customer_count,
                "created_at": s.created_at,
            }
            for s in segments
        ]
    }


@router.get("/{segment_id}/customers")
def get_segment_customers(segment_id: str, db: Session = Depends(get_db)):
    """
    Get all customer IDs for a segment — used when launching a campaign.
    """
    segment = db.query(Segment).filter(Segment.id == segment_id).first()

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    query = build_query_from_criteria(segment.criteria, db)
    customers = query.all()

    return {
        "segment_id": segment_id,
        "customer_count": len(customers),
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
            }
            for c in customers
        ],
    }