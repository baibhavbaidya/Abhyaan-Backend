# Abhyaan — Backend

FastAPI backend (CRM service) for Abhyaan, an AI-native mini CRM for retail and D2C brands.

**Live API:** [abhyaan-backend.onrender.com](https://abhyaan-backend.onrender.com)

**API Docs:** [abhyaan-backend.onrender.com/docs](https://abhyaan-backend.onrender.com/docs)

**Frontend:** [github.com/baibhavbaidya/Abhyaan-Frontend](https://github.com/baibhavbaidya/Abhyaan-Frontend)

**Channel Stub:** [github.com/baibhavbaidya/Abhyaan-Channel-Stub](https://github.com/baibhavbaidya/Abhyaan-Channel-Stub)

---

## What is Abhyaan

Abhyaan (Hindi for "campaign") is an AI-native CRM that helps retail brands decide who to talk to, what to say, and reach them through messaging channels. This is the core CRM service — it handles customer data, segmentation, AI integration, campaign management, and callback ingestion.

---

## Architecture

![Abhyaan Architecture](./Abhyaan%20Architecture%20Diagram.jpg)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/customers/stats` | Customer base overview stats |
| GET | `/api/opportunities` | AI-generated campaign opportunities |
| POST | `/api/chat` | Natural language → campaign |
| POST | `/api/segments/preview` | Preview segment size from criteria |
| POST | `/api/segments` | Save a segment |
| POST | `/api/campaigns` | Launch a campaign |
| GET | `/api/campaigns` | List all campaigns |
| DELETE | `/api/campaigns/:id` | Delete campaign and communications |
| POST | `/api/receipts` | Receive delivery callbacks from channel stub |
| GET | `/api/analytics/campaigns/:id` | Campaign funnel stats + AI insight |
| GET | `/api/analytics/overview` | Overall stats across all campaigns |

---

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL (Neon)
- Groq API (llama-3.3-70b-versatile)
- Deployed on Render

---

## Project Structure

```
crm-backend/
├── app/
│   ├── api/
│   │   ├── customers.py     # Customer stats endpoints
│   │   ├── segments.py      # Segment creation + filter builder
│   │   ├── opportunities.py # AI opportunity discovery
│   │   ├── chat.py          # Natural language → campaign
│   │   ├── campaigns.py     # Campaign launch + management
│   │   ├── receipts.py      # Callback ingestion + state machine
│   │   └── analytics.py     # Campaign analytics + AI insight
│   ├── models/
│   │   └── __init__.py      # SQLAlchemy models
│   ├── services/
│   │   └── ai_service.py    # Groq AI integration
│   └── db/
│       └── __init__.py      # Database connection
├── main.py                  # FastAPI app entry point
├── seed.py                  # Seed 500 customers + 2000+ orders
└── requirements.txt
```

---

## Key Design Decisions

**AI does reasoning, not querying.** The backend runs SQL queries to get customer group stats, packages them as plain text context, and sends to Groq. The AI never touches the database — it only sees a summary and returns structured JSON with segment criteria, message drafts, and channel recommendations.

**Filter-based segmentation.** Natural language input is converted to a predefined filter schema by the AI. The backend then builds SQL from those filters. This keeps the AI in its lane and the SQL predictable and safe.

**Async callback loop.** Campaign launch fires messages to the channel stub and returns immediately. The stub asynchronously fires callbacks back to `/api/receipts`. This mirrors how real providers like Twilio work.

**State machine on receipts.** Valid transitions: `sent → delivered → opened → clicked`. Invalid transitions are silently rejected. This prevents data corruption from out-of-order callbacks.

**Atomic stat updates.** Campaign aggregate stats use SQL `UPDATE ... SET delivered = delivered + 1` instead of read-then-write to prevent race conditions when many callbacks arrive simultaneously.

---

## Local Setup

```bash
git clone https://github.com/baibhavbaidya/Abhyaan-Backend
cd Abhyaan-Backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file:
```
DATABASE_URL=your_neon_postgresql_connection_string
GROQ_API_KEY=your_groq_api_key
CHANNEL_STUB_URL=http://localhost:8001
CRM_BASE_URL=http://localhost:8000
```

Seed the database:
```bash
python seed.py
```

Run:
```bash
uvicorn main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

---

## Seed Data

The seed script generates a realistic coffee brand dataset — Brew & Co. — with 500 customers and 2000+ orders across Mumbai, Delhi, Bangalore, Hyderabad and Chennai. Customer patterns are baked in so AI opportunities are meaningful:

- 100 high value customers gone inactive (spent >₹3000, inactive 50-90 days)
- 150 first time buyers (1 order, last 7-25 days)
- 80 VIP customers gone quiet (spent >₹10000, inactive 30-60 days)
- 170 regular active customers
