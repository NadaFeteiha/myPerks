# backend/api/schemas/admin.py

from datetime import date, datetime
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


class RequestHistorySnapshot(BaseModel):
    id: int
    type: str
    status: str
    created_at: datetime
    body: str | None


class EmployeeListItem(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str
    joined_date: date
    linked: bool  # True when clerk_user_id is set


class PaginatedEmployees(BaseModel):
    items: list[EmployeeListItem]
    total: int
    page: int
    size: int
    pages: int


class EmployeeDetail(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str
    joined_date: date
    benefits_year_reset: date
    linked: bool
    balances: list[BalanceSnapshot]          # reuses existing schema
    request_history: list[RequestHistorySnapshot]
