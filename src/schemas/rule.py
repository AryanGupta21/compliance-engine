from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


class RuleResponse(BaseModel):
    id: int
    document_id: int
    rule_title: str
    description: str
    category: str
    severity: str
    regex_patterns: List[str]
    languages: List[str]
    remediation: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RuleUpdate(BaseModel):
    rule_title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    regex_patterns: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    remediation: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"critical", "high", "medium", "low"}:
            raise ValueError("severity must be one of: critical, high, medium, low")
        return v
