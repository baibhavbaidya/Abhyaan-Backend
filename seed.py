import random
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import Customer, Order
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# Realistic Indian names
FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Rohit", "Anjali", "Vikas", "Pooja",
    "Arjun", "Divya", "Karan", "Neha", "Siddharth", "Megha", "Aditya",
    "Shreya", "Nikhil", "Riya", "Vivek", "Ananya", "Rajesh", "Sunita",
    "Manoj", "Kavya", "Suresh", "Deepika", "Prakash", "Swati", "Ramesh",
    "Kritika", "Harish", "Tanvi", "Girish", "Pallavi", "Sunil", "Nisha",
    "Vinay", "Shweta", "Ajay", "Meera", "Baibhav", "Ishana", "Ravi", "Simran",
    "Dinesh", "Komal", "Pankaj", "Sakshi", "Ashok", "Radha"
]

LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Gupta", "Patel", "Kumar", "Joshi", "Mehta",
    "Agarwal", "Yadav", "Mishra", "Tiwari", "Pandey", "Chauhan", "Malhotra",
    "Kapoor", "Bose", "Nair", "Iyer", "Reddy", "Rao", "Pillai", "Menon",
    "Chopra", "Khanna", "Bajaj", "Shah", "Desai", "Jain", "Sinha"
]

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"]

COFFEE_ITEMS = [
    {"name": "Espresso", "price": 120},
    {"name": "Cappuccino", "price": 180},
    {"name": "Latte", "price": 200},
    {"name": "Cold Brew", "price": 220},
    {"name": "Americano", "price": 150},
    {"name": "Mocha", "price": 230},
    {"name": "Flat White", "price": 190},
    {"name": "Pour Over", "price": 250},
    {"name": "Croissant", "price": 120},
    {"name": "Muffin", "price": 90},
    {"name": "Sandwich", "price": 180},
    {"name": "Coffee Bag 250g", "price": 450},
    {"name": "Coffee Bag 500g", "price": 850},
    {"name": "Brewing Kit", "price": 1200},
    {"name": "Travel Mug", "price": 699},
]

def random_date(days_ago_min, days_ago_max):
    days_ago = random.randint(days_ago_min, days_ago_max)
    return datetime.now() - timedelta(days=days_ago)

def generate_order_items():
    num_items = random.randint(1, 4)
    selected = random.sample(COFFEE_ITEMS, num_items)
    items = []
    total = 0
    for item in selected:
        qty = random.randint(1, 3)
        items.append({
            "name": item["name"],
            "price": item["price"],
            "quantity": qty
        })
        total += item["price"] * qty
    return items, total

def seed():
    db = SessionLocal()

    # Clear existing data
    db.query(Order).delete()
    db.query(Customer).delete()
    db.commit()

    print("Seeding customers and orders for Brew & Co...")

    customers = []

    # Pattern 1 — High value inactive (100 customers)
    # Spent > ₹5000, last purchase 50-90 days ago
    for _ in range(100):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customer = Customer(
            id=generate_uuid(),
            name=name,
            phone=f"9{random.randint(100000000, 999999999)}",
            email=f"{name.lower().replace(' ', '.')}{random.randint(1,99)}@gmail.com",
            city=random.choice(CITIES),
            total_orders=0,
            total_spent=0.0,
            last_purchase_date=random_date(50, 90)
        )
        customers.append(("high_value_inactive", customer))

    # Pattern 2 — First time buyers (150 customers)
    # Only 1 order, purchased 7-25 days ago
    for _ in range(150):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customer = Customer(
            id=generate_uuid(),
            name=name,
            phone=f"9{random.randint(100000000, 999999999)}",
            email=f"{name.lower().replace(' ', '.')}{random.randint(1,99)}@gmail.com",
            city=random.choice(CITIES),
            total_orders=0,
            total_spent=0.0,
            last_purchase_date=random_date(7, 25)
        )
        customers.append(("first_time_buyer", customer))

    # Pattern 3 — VIP gone quiet (80 customers)
    # Spent > ₹10000, last purchase 30-60 days ago
    for _ in range(80):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customer = Customer(
            id=generate_uuid(),
            name=name,
            phone=f"9{random.randint(100000000, 999999999)}",
            email=f"{name.lower().replace(' ', '.')}{random.randint(1,99)}@gmail.com",
            city=random.choice(CITIES),
            total_orders=0,
            total_spent=0.0,
            last_purchase_date=random_date(30, 60)
        )
        customers.append(("vip_quiet", customer))

    # Pattern 4 — Regular active customers (170 customers)
    # Mix of activity, last purchase 1-30 days ago
    for _ in range(170):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customer = Customer(
            id=generate_uuid(),
            name=name,
            phone=f"9{random.randint(100000000, 999999999)}",
            email=f"{name.lower().replace(' ', '.')}{random.randint(1,99)}@gmail.com",
            city=random.choice(CITIES),
            total_orders=0,
            total_spent=0.0,
            last_purchase_date=random_date(1, 30)
        )
        customers.append(("regular", customer))

    # Insert all customers
    for _, customer in customers:
        db.add(customer)
    db.commit()

    # Now generate orders per customer
    for pattern, customer in customers:
        orders = []

        if pattern == "high_value_inactive":
            # 3-8 orders, high amounts, last order 50-90 days ago
            num_orders = random.randint(3, 8)
            for i in range(num_orders):
                items, amount = generate_order_items()
                # Inflate amounts to ensure high value
                amount = max(amount, random.randint(600, 1500))
                order_date = customer.last_purchase_date - timedelta(
                    days=random.randint(0, 200)
                )
                orders.append(Order(
                    id=generate_uuid(),
                    customer_id=customer.id,
                    amount=float(amount),
                    items=items,
                    created_at=order_date
                ))

        elif pattern == "first_time_buyer":
            # Exactly 1 order
            items, amount = generate_order_items()
            orders.append(Order(
                id=generate_uuid(),
                customer_id=customer.id,
                amount=float(amount),
                items=items,
                created_at=customer.last_purchase_date
            ))

        elif pattern == "vip_quiet":
            # 8-15 orders, very high amounts
            num_orders = random.randint(8, 15)
            for i in range(num_orders):
                items, amount = generate_order_items()
                amount = max(amount, random.randint(800, 2000))
                order_date = customer.last_purchase_date - timedelta(
                    days=random.randint(0, 400)
                )
                orders.append(Order(
                    id=generate_uuid(),
                    customer_id=customer.id,
                    amount=float(amount),
                    items=items,
                    created_at=order_date
                ))

        elif pattern == "regular":
            # 2-5 orders, moderate amounts
            num_orders = random.randint(2, 5)
            for i in range(num_orders):
                items, amount = generate_order_items()
                order_date = customer.last_purchase_date - timedelta(
                    days=random.randint(0, 150)
                )
                orders.append(Order(
                    id=generate_uuid(),
                    customer_id=customer.id,
                    amount=float(amount),
                    items=items,
                    created_at=order_date
                ))

        # Insert orders
        total_spent = 0
        for order in orders:
            db.add(order)
            total_spent += order.amount

        # Update customer stats
        customer.total_orders = len(orders)
        customer.total_spent = round(total_spent, 2)

    db.commit()

    # Print summary
    total_customers = db.query(Customer).count()
    total_orders = db.query(Order).count()
    print(f"Done. {total_customers} customers and {total_orders} orders seeded.")
    print("\nBreakdown:")
    print(f"  High value inactive : 100 customers")
    print(f"  First time buyers   : 150 customers")
    print(f"  VIP gone quiet      : 80 customers")
    print(f"  Regular active      : 170 customers")

    db.close()

if __name__ == "__main__":
    seed()