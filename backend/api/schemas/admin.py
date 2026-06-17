from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

DEPARTMENT_VALUES = Literal[
    "engineering", "sales", "marketing", "hr", "finance", "operations", "other"
]
ROLE_VALUES = Literal["employee", "hr_admin"]
LEAVE_TYPE_VALUES = Literal["vacation", "sick", "pto"]


class BalanceInput(BaseModel):
    """One leave-type balance HR sets at pre-create or updates via PATCH.

    leave_type is constrained to the three known types (unknown -> 422) and
    total_days must be non-negative (negative -> 422). used_days is never
    accepted from the client — it is seeded to 0 and only moves via the
    approve/reject flow.
    """

    leave_type: LEAVE_TYPE_VALUES
    total_days: float = Field(ge=0)


def _no_duplicate_leave_types(
    v: list[BalanceInput] | None,
) -> list[BalanceInput] | None:
    """Reject a balances payload that names the same leave_type twice.

    Without this the second row would collide on the
    (employee_id, year, leave_type) unique index and surface as a 500
    instead of a clean 422.
    """
    if v is not None:
        seen: set[str] = set()
        for b in v:
            if b.leave_type in seen:
                raise ValueError(f"duplicate leave_type: {b.leave_type}")
            seen.add(b.leave_type)
    return v


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
    balances: list[BalanceSnapshot]  # reuses existing schema
    request_history: list[RequestHistorySnapshot]


class PreCreateEmployeeBody(BaseModel):
    name: str
    email: str
    department: DEPARTMENT_VALUES
    joined_date: date
    benefits_year_reset: date
    # Optional. Omitted leave types fall back to the 15 / 10 / 5 defaults; a
    # partial list is merged over those defaults (see the router).
    balances: list[BalanceInput] | None = None

    _no_dupes = field_validator("balances")(_no_duplicate_leave_types)


class PreCreateEmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str
    joined_date: date
    benefits_year_reset: date
    linked: bool  # always False on pre-create
    balances: list[BalanceSnapshot]  # seeded balances, echoed back


class PatchEmployeeBody(BaseModel):
    department: DEPARTMENT_VALUES | None = None
    role: ROLE_VALUES | None = None
    # Updates current-year total_days for the named leave types. The row must
    # already exist (employees are pre-created with a full set) -> 404 if not.
    balances: list[BalanceInput] | None = None

    _no_dupes = field_validator("balances")(_no_duplicate_leave_types)


class PatchEmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    department: str
    role: str
    joined_date: date
    benefits_year_reset: date
    linked: bool
    balances: list[BalanceSnapshot]  # current-year balances after the update


class RequestListItem(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    type: str
    status: str
    created_at: datetime
    body: str | None


class PaginatedRequests(BaseModel):
    items: list[RequestListItem]
    total: int
    page: int
    size: int
    pages: int
