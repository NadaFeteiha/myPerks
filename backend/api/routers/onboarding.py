from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.schemas.onboarding import OnboardRequest, OnboardResponse
from db.models import Employee
from db.session import get_session

router = APIRouter(prefix="/me", tags=["onboarding"])


@router.get(
    "",
    response_model=OnboardResponse,
    summary="Check if the current Clerk user has an Employee record",
)
async def get_me(
    db: AsyncSession = Depends(get_session),  # noqa: B008
    clerk_user_id: str = Depends(get_current_user),  # noqa: B008
) -> OnboardResponse:
    """
    Returns the Employee record for the authenticated Clerk user.
    Raises 404 if no record exists — frontend uses this to decide
    whether to redirect to /onboarding.
    """
    result = await db.execute(
        select(Employee).where(Employee.clerk_user_id == clerk_user_id)
    )
    employee = result.scalars().first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return OnboardResponse(
        id=employee.id,
        clerk_user_id=employee.clerk_user_id,
        name=employee.name,
        email=employee.email,
        department=employee.department,
    )


@router.post(
    "/onboard",
    response_model=OnboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Employee record for the current Clerk user",
)
async def onboard(
    body: OnboardRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    clerk_user_id: str = Depends(get_current_user),  # noqa: B008
) -> OnboardResponse:
    """
    Creates a new Employee row for the authenticated Clerk user.
    Raises 409 if the employee already exists — this endpoint is
    create-only; use GET /me to check existence first.
    """
    result = await db.execute(
        select(Employee).where(Employee.clerk_user_id == clerk_user_id)
    )
    existing = result.scalars().first()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee already exists",
        )

    employee = Employee(
        clerk_user_id=clerk_user_id,
        name=body.name,
        email=body.email,
        department=body.department,
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)

    return OnboardResponse(
        id=employee.id,
        clerk_user_id=employee.clerk_user_id,
        name=employee.name,
        email=employee.email,
        department=employee.department,
    )
