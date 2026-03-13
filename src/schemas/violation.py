from datetime import datetime

from pydantic import BaseModel


class ViolationResponse(BaseModel):
    id: int
    rule_id: int
    file_path: str
    language: str
    line_number: int
    matched_pattern: str
    matched_text: str
    severity: str
    detected_at: datetime

    model_config = {"from_attributes": True}
