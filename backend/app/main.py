import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import init_db, get_db
from app.models import Interaction, Sample, Material
from app.schemas import ChatRequest, ChatResponse, InteractionCreate, InteractionResponse
from app.agent import run_agent_workflow
from app.utils import PDF_DIR

app = FastAPI(title="AI-First CRM HCP Module API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Automatically initialize tables in Postgres/SQLite
    await init_db()

@app.get("/")
def read_root():
    return {"message": "AI-First CRM HCP Module API is running"}

@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest):
    """
    Receives chat messages, executes the LangGraph workflow,
    updates form state, and returns the response message and updated form.
    """
    try:
        # Run agent logic
        history_list = [{"role": msg.role, "content": msg.content} for msg in req.history]
        ai_message, updated_form = await run_agent_workflow(
            message=req.message,
            history=history_list,
            current_form=req.current_form
        )
        return ChatResponse(message=ai_message, updated_form=updated_form)
    except Exception as e:
        print(f"Agent workflow failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while communicating with the AI Agent: {str(e)}"
        )

@app.post("/api/interactions/log", response_model=InteractionResponse)
async def log_interaction(payload: InteractionCreate, db: AsyncSession = Depends(get_db)):
    """
    Saves the final interaction details along with materials/samples to the database.
    """
    try:
        # Extract schema properties
        db_interaction = Interaction(
            hcp_name=payload.hcp_name,
            interaction_type=payload.interaction_type,
            interaction_date=payload.interaction_date,
            interaction_time=payload.interaction_time,
            attendees=payload.attendees,
            topics_discussed=payload.topics_discussed,
            sentiment=payload.sentiment,
            outcomes=payload.outcomes,
            follow_up_actions=payload.follow_up_actions,
            email_draft=payload.email_draft,
            pdf_path=payload.dict().get("pdf_path") or None
        )
        
        db.add(db_interaction)
        await db.commit()
        await db.refresh(db_interaction)

        # Log child sample records
        for s in payload.samples:
            db_sample = Sample(
                interaction_id=db_interaction.id,
                sample_name=s.sample_name,
                quantity=s.quantity
            )
            db.add(db_sample)

        # Log child material records
        for m in payload.materials:
            db_material = Material(
                interaction_id=db_interaction.id,
                material_name=m.material_name,
                file_url=m.file_url
            )
            db.add(db_material)

        await db.commit()
        await db.refresh(db_interaction)
        
        # Build the response manually to avoid SQLAlchemy async relationship lazy-loading errors (MissingGreenlet)
        return InteractionResponse(
            id=db_interaction.id,
            hcp_name=db_interaction.hcp_name,
            interaction_type=db_interaction.interaction_type,
            interaction_date=db_interaction.interaction_date,
            interaction_time=db_interaction.interaction_time,
            attendees=db_interaction.attendees,
            topics_discussed=db_interaction.topics_discussed,
            sentiment=db_interaction.sentiment,
            outcomes=db_interaction.outcomes,
            follow_up_actions=db_interaction.follow_up_actions,
            email_draft=db_interaction.email_draft,
            pdf_path=db_interaction.pdf_path,
            created_at=db_interaction.created_at,
            samples=payload.samples,
            materials=payload.materials
        )
    except Exception as e:
        await db.rollback()
        print(f"Failed to log interaction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save interaction to database: {str(e)}"
        )

@app.get("/api/interactions/download-pdf/{filename}")
def download_pdf(filename: str):
    """
    Serves the dynamically generated clinical brief PDF file.
    """
    file_path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested Clinical Brief PDF was not found."
        )
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename
    )
