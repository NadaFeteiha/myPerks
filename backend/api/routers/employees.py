from __future__ import annotations

import datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from api.auth import get_current_user
from db.models import Employee
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/employees", tags=["employees"])


class RegisterRequest(BaseModel):
    email: str


class EmployeeResponse(BaseModel):
    id: int
    clerk_user_id: str
    name: str
    email: str
    department: str | None
    role: str
    joined_date: datetime.date
    benefits_year_reset: datetime.date


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
        role=employee.role,
        joined_date=employee.joined_date,
        benefits_year_reset=employee.benefits_year_reset,
    )


@router.post(
    "/me",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link the current Clerk user to a pre-created employee record",
)
async def register_me(
    body: RegisterRequest,
    clerk_user_id: str = Depends(get_current_user),  # noqa: B008
) -> EmployeeResponse:
    """
    Links the authenticated Clerk user to an Employee row that HR pre-created
    (clerk_user_id still null), matched by email. Employees are never created
    here — HR provisions them via POST /admin/employees or the seed, and the
    T42 trigger seeds their balances on insert.

    Returns 409 if this Clerk user is already linked, or if the email is
    already linked to a different account. Returns 403 if no pre-created
    record exists for the email.
    """
    async with AsyncSessionLocal() as session:
        # Already linked to this Clerk user?
        existing = await session.scalar(
            select(Employee).where(Employee.clerk_user_id == clerk_user_id)
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee already exists",
            )

        # Match a row HR pre-created, by email.
        existing = await session.scalar(
            select(Employee).where(Employee.email == body.email)
        )
        if existing is None:
            # No HR-provisioned record for this email. Do not self-create —
            # the employee must be added by HR first.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No employee record found for this email. "
                    "Contact your HR admin to be added."
                ),
            )
        if existing.clerk_user_id is not None:
            # Email already claimed by a different Clerk account. Refuse rather
            # than re-point the row (no hijack).
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email is already linked to another account",
            )

        # Link the pre-created row to the current Clerk user.
        existing.clerk_user_id = clerk_user_id
        await session.commit()
        await session.refresh(existing)
        return EmployeeResponse(
            id=cast(int, existing.id),
            clerk_user_id=clerk_user_id,
            name=cast(str, existing.name),
            email=cast(str, existing.email),
            department=cast("str | None", existing.department),
            role=existing.role,
            joined_date=existing.joined_date,
            benefits_year_reset=existing.benefits_year_reset,
        )
