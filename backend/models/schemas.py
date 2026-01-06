from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Union
from datetime import datetime


class EmailMetadata(BaseModel):
    subject: str
    from_email: str
    from_domain: str
    to: List[str]
    cc: List[str] = []
    date: Union[datetime, str]
    body_text: str
    body_html: str
    attachments: List[Dict[str, Any]] = []
    inline_images: List[Dict[str, Any]] = []
    
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                return datetime.fromisoformat(v)
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

