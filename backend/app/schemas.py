from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time, datetime

class SampleBase(BaseModel):
    sample_name: str
    quantity: int

    class Config:
        orm_mode = True

class MaterialBase(BaseModel):
    material_name: str
    file_url: Optional[str] = None

    class Config:
        orm_mode = True

class InteractionBase(BaseModel):
    hcp_name: str
    interaction_type: str = "Meeting"
    interaction_date: date
    interaction_time: time
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: str = "Neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    email_draft: Optional[str] = None

class InteractionCreate(InteractionBase):
    samples: List[SampleBase] = []
    materials: List[MaterialBase] = []

class InteractionResponse(InteractionBase):
    id: int
    pdf_path: Optional[str] = None
    created_at: datetime
    samples: List[SampleBase] = []
    materials: List[MaterialBase] = []

    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda v: v.isoformat(),
            time: lambda v: v.strftime("%H:%M"),
            datetime: lambda v: v.isoformat()
        }

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[MessageItem] = []
    current_form: dict

class ChatResponse(BaseModel):
    message: str
    updated_form: dict
