from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base, wait_for_db
import app.models
from app.api import customers, segments, opportunities, chat, campaigns, receipts, analytics

app = FastAPI(title="XenoCRM", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wait for Neon to wake up then create tables
if wait_for_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")
else:
    print("Warning: Could not connect to database on startup")

# Routes
app.include_router(customers.router)
app.include_router(segments.router)
app.include_router(opportunities.router)
app.include_router(chat.router)
app.include_router(campaigns.router)
app.include_router(receipts.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"status": "XenoCRM running"}