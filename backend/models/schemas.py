from datetime import datetime
from typing import Any, Dict, List, Union

from pydantic import BaseModel, ConfigDict, field_validator


class EmailMetadata(BaseModel):
    model_config = ConfigDict(ser_json_timedelta="float")

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

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return datetime.fromisoformat(v)
        return v

