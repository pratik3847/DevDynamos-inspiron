from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import rules_collection
from app.services.rules.store import get_or_create_user_rules, save_user_rules, reset_user_rules
from app.utils.auth import get_current_user

router = APIRouter(prefix="/rules", tags=["rules"])


class RuleDefinition(BaseModel):
    id: str
    name: str
    category: Literal["Structural", "Business", "External"]
    severity: Literal["Critical", "Error", "Warning", "Info"]
    description: str
    scope: List[str]
    source: str
    tags: List[str]
    enabled: bool
    defaultEnabled: bool
    runtime: Literal["Realtime", "Batch", "External"]
    lastUpdated: str
    matchCodes: List[str] = Field(default_factory=list)


class RuleSetPayload(BaseModel):
    rules: List[RuleDefinition]


@router.get("")
def get_rules(current_user: dict = Depends(get_current_user)):
    if rules_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    rules, updated_at = get_or_create_user_rules(current_user["userId"])
    return {"rules": rules, "updatedAt": updated_at}


@router.put("")
def update_rules(payload: RuleSetPayload, current_user: dict = Depends(get_current_user)):
    if rules_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    rules = [rule.dict() for rule in payload.rules]
    saved, updated_at = save_user_rules(current_user["userId"], rules)
    return {"rules": saved, "updatedAt": updated_at}


@router.post("/reset")
def reset_rules(current_user: dict = Depends(get_current_user)):
    if rules_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    rules, updated_at = reset_user_rules(current_user["userId"])
    return {"rules": rules, "updatedAt": updated_at}
