"""
This module define the mock API endpoint that is supposed to be called by the agent on lead capture.
It utilizes FastAPI and the custom db class for lead management.(which only includes the post and get endpoints for leads, easily expandable for other endpoints and greater functionalities).
"""

from fastapi import FastAPI
from pydantic import BaseModel
from demo.config import settings
from demo.core.database import LeadDB

app = FastAPI(title="Mock API Endpoints", version="1.0.0")
lead_db = LeadDB(settings.db_path)

class LeadRequest(BaseModel):
    name: str
    email: str
    platform: str

@app.get("/")
async def health_check():
    """Health check endpoint for the API"""
    return {
        "status": "online",
        "message": "Mock API Endpoint active"
    }

@app.post("/leads")
async def add_lead(lead: LeadRequest):
    """Endpoint to add a new lead to the database, called by the agent on lead capture."""
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
    """Endpoint to retrieve all leads from the database, used for debugging or verification purposes"""
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
    