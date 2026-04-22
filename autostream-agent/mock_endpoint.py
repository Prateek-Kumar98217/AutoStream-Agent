from fastapi import FastAPI
from pydantic import BaseModel
from config import settings
from core.database import LeadDB

app = FastAPI(title="Mock API Endpoints", version="1.0.0")
lead_db = LeadDB(settings.db_path)

class LeadRequest(BaseModel):
    name: str
    email: str
    platform: str

@app.get("/")
async def health_check():
    return {
        "status": "online",
        "message": "Mock API Endpoint active"
    }

@app.post("/leads")
async def add_lead(lead: LeadRequest):
    success = lead_db.add_lead(lead.name, lead.email, lead.platform)

    if success:
        return {
            "status": "success",
            "message": "Lead added to database."
        }
    else:
        return {
            "status" : "error",
            "message": "Error or duplicate entry."
        }

@app.get("/leads")
def get_leads():
    leads = lead_db.get_leads()
    if leads:
        return {
            "status": "success",
            "data": leads
        }
    else:
        return {
            "status": "error",
            "message": "Error while fetching leads"
        }
    