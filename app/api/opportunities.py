from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.api.customers import get_customer_stats
from app.api.segments import build_query_from_criteria
from app.services.ai_service import get_opportunities
from app.models import Customer

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("/")
def fetch_opportunities(db: Session = Depends(get_db)):
    """
    Fetch AI-generated campaign opportunities based on current customer data.
    """

    # Step 1 — get customer stats from DB
    stats = get_customer_stats(db)

    # Step 2 — pass stats to AI, get opportunities back
    opportunities = get_opportunities(stats)

    # Step 3 — for each opportunity, get the actual customer count
    # using the criteria AI returned
    enriched = []
    for opp in opportunities:
        try:
            criteria = opp.get("criteria", {})
            query = build_query_from_criteria(criteria, db)
            actual_count = query.count()

            enriched.append({
                **opp,
                "customer_count": actual_count,
            })
        except Exception:
            enriched.append({
                **opp,
                "customer_count": 0,
            })

    return {"opportunities": enriched}