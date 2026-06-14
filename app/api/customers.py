from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Customer, Order
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/")
def get_customers(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return {
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
                "city": c.city,
                "total_orders": c.total_orders,
                "total_spent": c.total_spent,
                "last_purchase_date": c.last_purchase_date,
                "created_at": c.created_at,
            }
            for c in customers
        ],
        "total": db.query(Customer).count(),
    }


@router.get("/stats")
def get_customer_stats(db: Session = Depends(get_db)):
    now = datetime.now()

    total_customers = db.query(Customer).count()

    total_revenue = db.query(func.sum(Customer.total_spent)).scalar() or 0

    active_customers = (
        db.query(Customer)
        .filter(Customer.last_purchase_date >= now - timedelta(days=30))
        .count()
    )

    inactive_high_value = (
        db.query(Customer)
        .filter(
            Customer.last_purchase_date < now - timedelta(days=45),
            Customer.total_spent > 3000,
        )
        .count()
    )

    first_time_buyers = (
        db.query(Customer)
        .filter(
            Customer.total_orders == 1,
            Customer.last_purchase_date >= now - timedelta(days=30),
        )
        .count()
    )

    vip_gone_quiet = (
        db.query(Customer)
        .filter(
            Customer.total_spent > 10000,
            Customer.last_purchase_date < now - timedelta(days=30),
        )
        .count()
    )

    avg_order_value = db.query(func.avg(Order.amount)).scalar() or 0

    return {
        "total_customers": total_customers,
        "total_revenue": round(total_revenue, 2),
        "active_customers": active_customers,
        "inactive_high_value": inactive_high_value,
        "first_time_buyers": first_time_buyers,
        "vip_gone_quiet": vip_gone_quiet,
        "avg_order_value": round(avg_order_value, 2),
    }