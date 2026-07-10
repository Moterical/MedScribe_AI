from pydantic import BaseModel, model_validator
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
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: str = "Neutral"
    outcomes: Optional[str] = None
    follow_up_date: Optional[date] = None
    follow_up_time: Optional[time] = None
    email_draft: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def clean_empty_strings(cls, data):
        if isinstance(data, dict):
            for field in ["interaction_date", "interaction_time", "follow_up_date", "follow_up_time"]:
                if data.get(field) == "":
                    data[field] = None
        return data

class InteractionCreate(InteractionBase):
    samples: List[SampleBase] = []
    materials: List[MaterialBase] = []
    session_id: Optional[str] = None

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
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    updated_form: dict


class DraftSessionSave(BaseModel):
    session_id: str
    form_data: dict
    chat_history: List[dict] = []


class DraftSessionResponse(BaseModel):
    session_id: str
    form_data: dict
    chat_history: List[dict] = []
    updated_at: datetime

    class Config:
        orm_mode = True

