# backend/api/schemas/dashboard.py

from pydantic import BaseModel, Field


class LeaveBalanceSchema(BaseModel):
    """
    Represents a single leave type balance for an employee.
    """

    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float

    model_config = {
        "from_attributes": True,
    }


class VacationBalanceResponse(BaseModel):
    """
    Response schema for GET /me/vacation.
    Returns all leave type balances for the current year.
    """

    year: int
    balances: list[LeaveBalanceSchema]


class RequestHistoryItemSchema(BaseModel):
    """
    Represents a single request history item.
    """

    id: int
    type: str
    status: str
    created_at: str
    body: str | None

    model_config = {"from_attributes": True}


class RequestHistoryResponse(BaseModel):
    """
    Response schema for GET /me/requests.
    Paginated list of request history items.
    """

    total: int
    page: int = Field(ge=1, description="Current page number, 1-indexed")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    items: list[RequestHistoryItemSchema]


class BenefitSummaryItemSchema(BaseModel):
    """
    Represents a single leave type in the benefits summary.
    Includes percent_used for frontend charts.
    """

    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float
    percent_used: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of total days used, for chart rendering",
    )


class BenefitsSummaryResponse(BaseModel):
    """Response schema for GET /me/benefits-summary."""

    year: int
    summary: list[BenefitSummaryItemSchema]
