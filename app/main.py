import secrets
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.config import settings
from app.db import get_supabase

app = FastAPI(title=f"{settings.brand_name} Support Console API", version="1.0.0")
security = HTTPBasic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    valid_user = secrets.compare_digest(credentials.username, settings.dashboard_username)
    valid_pass = secrets.compare_digest(credentials.password, settings.dashboard_password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class PolicyUpdate(BaseModel):
    title: str
    content: str


@app.get("/health")
def health():
    return {"status": "ok", "brand": settings.brand_name}


@app.get("/api/events", dependencies=[Depends(verify_admin)])
def list_events():
    res = get_supabase().table("support_events").select("*").order("created_at", desc=True).limit(50).execute()
    return res.data


@app.get("/api/tickets", dependencies=[Depends(verify_admin)])
def list_tickets():
    res = get_supabase().table("support_tickets").select("*").order("updated_at", desc=True).limit(50).execute()
    return res.data


@app.get("/api/tickets/{ticket_id}/messages", dependencies=[Depends(verify_admin)])
def ticket_messages(ticket_id: int):
    res = (
        get_supabase()
        .table("ticket_messages")
        .select("*")
        .eq("ticket_id", ticket_id)
        .order("created_at")
        .execute()
    )
    return res.data


@app.post("/api/tickets/{ticket_id}/resolve", dependencies=[Depends(verify_admin)])
def resolve_ticket(ticket_id: int):
    get_supabase().table("support_tickets").update({"status": "resolved"}).eq("id", ticket_id).execute()
    return {"ok": True}


@app.get("/api/policies", dependencies=[Depends(verify_admin)])
def list_policies():
    res = get_supabase().table("policy_docs").select("*").order("id").execute()
    return res.data


@app.put("/api/policies/{slug}", dependencies=[Depends(verify_admin)])
def update_policy(slug: str, payload: PolicyUpdate):
    (
        get_supabase()
        .table("policy_docs")
        .update({"title": payload.title, "content": payload.content})
        .eq("slug", slug)
        .execute()
    )
    return {"ok": True}


dist_dir = Path("dashboard/dist")
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="dashboard")
