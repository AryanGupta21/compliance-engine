from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    source_hash: str
    ingested_at: datetime
    rules_extracted: bool
    extraction_error: Optional[str]
    rule_count: int

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    document_id: int
    filename: str
    rules_extracted: int
    message: str
