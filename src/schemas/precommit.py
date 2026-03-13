"""
Wire format schemas for integration with the Pre-Commit Engine (SecretLens).
These must remain compatible with the Rust engine's expectations.
"""
from typing import Any, Dict, List

from pydantic import BaseModel


class FileChange(BaseModel):
    file_path: str
    content: str


class ValidateRequest(BaseModel):
    files: List[FileChange]
    ai_provider_config: Dict[str, Any] = {}


class Finding(BaseModel):
    rule_id: str
    severity: str
    line_number: int
    message: str
    remediation: str


class ValidateResponse(BaseModel):
    findings: List[Finding]
