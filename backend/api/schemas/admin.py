# backend/api/schemas/admin.py

from typing import Literal

from pydantic import BaseModel


class ApproveRejectBody(BaseModel):
    status: Literal["approved", "rejected"]
    rejection_reason: str | None = None


class BalanceSnapshot(BaseModel):
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float


class ApproveRejectResponse(BaseModel):
    request_id: int
    employee_name: str
    employee_email: str
    request_type: str
    new_status: str
    rejection_reason: str | None
    updated_balances: list[BalanceSnapshot]
