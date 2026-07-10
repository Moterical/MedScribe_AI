import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import init_db, get_db
from app.models import Interaction, Sample, Material, InteractionDraft
from app.schemas import (
    ChatRequest,
    ChatResponse,
    InteractionCreate,
    InteractionResponse,
    DraftSessionSave,
    DraftSessionResponse
)
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

@app.get("/api/agent/session/{session_id}", response_model=DraftSessionResponse)
async def get_draft_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the conversational chat logs and form state draft for the session.
    """
    try:
        result = await db.execute(select(InteractionDraft).where(InteractionDraft.session_id == session_id))
        draft = result.scalars().first()
        if not draft:
            raise HTTPException(
                status_code=404,
                detail="No draft session found for this session ID."
            )
        return draft
    except HTTPException:
        raise
    except Exception as e:
        print(f"Failed to fetch draft session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading draft session: {str(e)}"
        )

@app.post("/api/agent/session", response_model=DraftSessionResponse)
async def save_draft_session(payload: DraftSessionSave, db: AsyncSession = Depends(get_db)):
    """
    Saves or updates the active draft session state.
    """
    try:
        result = await db.execute(select(InteractionDraft).where(InteractionDraft.session_id == payload.session_id))
        draft = result.scalars().first()
        
        # Strip temporary UI flags like open_calendar_picker from draft persistence
        draft_form = dict(payload.form_data)
        draft_form["open_calendar_picker"] = False

        if draft:
            draft.form_data = draft_form
            draft.chat_history = payload.chat_history
        else:
            draft = InteractionDraft(
                session_id=payload.session_id,
                form_data=draft_form,
                chat_history=payload.chat_history
            )
            db.add(draft)
            
        await db.commit()
        await db.refresh(draft)
        return draft
    except Exception as e:
        await db.rollback()
        print(f"Failed to save draft session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error saving draft session: {str(e)}"
        )

@app.delete("/api/agent/session/{session_id}")
async def delete_draft_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes the draft session (usually on Reset Form).
    """
    try:
        result = await db.execute(select(InteractionDraft).where(InteractionDraft.session_id == session_id))
        draft = result.scalars().first()
        if draft:
            await db.delete(draft)
            await db.commit()
        return {"status": "success", "message": "Draft session deleted successfully."}
    except Exception as e:
        await db.rollback()
        print(f"Failed to delete draft session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting draft session: {str(e)}"
        )

@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest, db: AsyncSession = Depends(get_db)):
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
        
        # Auto-update draft session if session_id is provided
        if req.session_id:
            try:
                full_history = history_list + [
                    {"role": "user", "content": req.message},
                    {"role": "assistant", "content": ai_message}
                ]
                
                # Strip temporary UI flags like open_calendar_picker from draft persistence
                draft_form = dict(updated_form)
                draft_form["open_calendar_picker"] = False

                result = await db.execute(select(InteractionDraft).where(InteractionDraft.session_id == req.session_id))
                draft = result.scalars().first()
                if draft:
                    draft.form_data = draft_form
                    draft.chat_history = full_history
                else:
                    draft = InteractionDraft(
                        session_id=req.session_id,
                        form_data=draft_form,
                        chat_history=full_history
                    )
                    db.add(draft)
                await db.commit()
            except Exception as se:
                print(f"Error auto-saving draft: {se}")
                
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
        from datetime import date as dt_date, datetime as dt_datetime
        db_interaction = Interaction(
            hcp_name=payload.hcp_name,
            interaction_type=payload.interaction_type,
            interaction_date=payload.interaction_date or dt_date.today(),
            interaction_time=payload.interaction_time or dt_datetime.now().time(),
            attendees=payload.attendees,
            topics_discussed=payload.topics_discussed,
            sentiment=payload.sentiment,
            outcomes=payload.outcomes,
            follow_up_date=payload.follow_up_date,
            follow_up_time=payload.follow_up_time,
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

        # Clean up draft session if session_id is provided
        if payload.session_id:
            try:
                res = await db.execute(select(InteractionDraft).where(InteractionDraft.session_id == payload.session_id))
                draft = res.scalars().first()
                if draft:
                    await db.delete(draft)
            except Exception as de:
                print(f"Error auto-deleting draft on log: {de}")

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
            follow_up_date=db_interaction.follow_up_date,
            follow_up_time=db_interaction.follow_up_time,
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
