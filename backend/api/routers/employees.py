from __future__ import annotations

import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from api.auth import get_current_user, get_current_user_payload
from db.models import Employee, VacationBalance
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/employees", tags=["employees"])


class RegisterRequest(BaseModel):
    name: str
    department: str | None = None


class EmployeeResponse(BaseModel):
    id: int
    clerk_user_id: str
    name: str
    email: str
    department: str | None


@router.get(
    "/me",
    response_model=EmployeeResponse,
    summary="Get the current employee record",
)
async def get_me(
    clerk_user_id: str = Depends(get_current_user),  # noqa: B008
) -> EmployeeResponse:
    """
    Returns the Employee record for the authenticated Clerk user.
    Raises 404 if no record exists — frontend uses this to decide
    whether to redirect to /onboarding.
    """
    async with AsyncSessionLocal() as session:
        employee = await session.scalar(
            select(Employee).where(Employee.clerk_user_id == clerk_user_id)
        )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return EmployeeResponse(
        id=cast(int, employee.id),
        clerk_user_id=cast(str, employee.clerk_user_id),
        name=cast(str, employee.name),
        email=cast(str, employee.email),
        department=cast("str | None", employee.department),
    )


@router.post(
    "/me",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register the current employee",
)
async def register_me(
    body: RegisterRequest,
    payload: dict[str, Any] = Depends(get_current_user_payload),  # noqa: B008
) -> EmployeeResponse:
    """
    Creates a new Employee row for the authenticated Clerk user.
    Email is pulled from the verified JWT — not the request body.
    Also seeds default vacation balances for the current year.
    Returns 409 if the employee already exists.
    """

    clerk_user_id: str = str(payload["sub"])
    email: str | None = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email claim missing from token. Check Clerk JWT template.",
        )

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(Employee).where(Employee.clerk_user_id == clerk_user_id)
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee already exists",
            )

        employee = Employee(
            clerk_user_id=clerk_user_id,
            name=body.name,
            email=email,
            department=body.department,
        )
        session.add(employee)
        await session.flush()

        current_year = datetime.datetime.now().year
        eid = employee.id
        session.add_all(
            [
                VacationBalance(
                    employee_id=eid,
                    leave_type="vacation",
                    total_days=15.0,
                    used_days=0.0,
                    year=current_year,
                ),
                VacationBalance(
                    employee_id=eid,
                    leave_type="sick",
                    total_days=10.0,
                    used_days=0.0,
                    year=current_year,
                ),
                VacationBalance(
                    employee_id=eid,
                    leave_type="pto",
                    total_days=5.0,
                    used_days=0.0,
                    year=current_year,
                ),
            ]
        )
        await session.commit()
        await session.refresh(employee)

    return EmployeeResponse(
        id=cast(int, employee.id),
        clerk_user_id=cast(str, employee.clerk_user_id),
        name=cast(str, employee.name),
        email=cast(str, employee.email),
        department=cast("str | None", employee.department),
    )
