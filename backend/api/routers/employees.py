from __future__ import annotations

import datetime
from typing import cast

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from api.auth import get_current_user
from db.models import Employee, VacationBalance
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/employees", tags=["employees"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    department: str | None = None


class EmployeeResponse(BaseModel):
    id: int
    clerk_user_id: str
    name: str
    email: str
    department: str | None


@router.post(
    "/me",
    response_model=EmployeeResponse,
    summary="Register or fetch the current employee",
)
async def register_me(
    body: RegisterRequest,
    clerk_user_id: str = Depends(get_current_user),  # noqa: B008
) -> EmployeeResponse:
    """
    Upsert an Employee row for the authenticated Clerk user.

    - First call: creates the row and returns 200 with the new profile.
    - Subsequent calls: returns the existing profile unchanged.
    """
    async with AsyncSessionLocal() as session:
        employee = await session.scalar(
            select(Employee).where(Employee.clerk_user_id == clerk_user_id)
        )

        if employee is None:
            employee = Employee(
                clerk_user_id=clerk_user_id,
                name=body.name,
                email=body.email,
                department=body.department,
            )
            session.add(employee)
            await session.flush()  # get employee.id before creating balances

            current_year = datetime.datetime.now().year
            eid = employee.id
            session.add_all([
                VacationBalance(
                    employee_id=eid, leave_type="vacation",
                    total_days=15.0, used_days=0.0, year=current_year,
                ),
                VacationBalance(
                    employee_id=eid, leave_type="sick",
                    total_days=10.0, used_days=0.0, year=current_year,
                ),
                VacationBalance(
                    employee_id=eid, leave_type="pto",
                    total_days=5.0, used_days=0.0, year=current_year,
                ),
            ])
            await session.commit()
            await session.refresh(employee)

    return EmployeeResponse(
        id=cast(int, employee.id),
        clerk_user_id=cast(str, employee.clerk_user_id),
        name=cast(str, employee.name),
        email=cast(str, employee.email),
        department=cast("str | None", employee.department),
    )
