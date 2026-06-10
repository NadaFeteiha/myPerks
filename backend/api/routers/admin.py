# backend/api/routers/admin.py
"""
Single admin endpoint: approve or reject an employee HR request.
Behind require_admin — only HR admins may call this.
Approving a leave request updates VacationBalance.used_days so the
employee's dashboard balance reflects the change immediately.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from math import ceil
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth import require_admin
from api.schemas.admin import (
    ApproveRejectBody,
    ApproveRejectResponse,
    BalanceSnapshot,
    EmployeeDetail,
    EmployeeListItem,
    PaginatedEmployees,
    RequestHistorySnapshot,
)
from db.models import Employee, RequestHistory, VacationBalance
from db.session import get_session

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get(
    "/employees",
    response_model=PaginatedEmployees,
    summary="List all employees (paginated, searchable)"
)
async def list_employees(
    page: int = 1,
    size: int = 10,
    q: str | None = None,
    db: AsyncSession = Depends(get_session), # noqa: B008
    _admin: Employee = Depends(require_admin), # noqa: B008
) -> PaginatedEmployees:
    if size < 1:
        size = 1
    if size > 100:
        size = 100
    if page < 1:
        page = 1

    base_query = select(Employee)
    count_query = select(func.count()).select_from(Employee)

    if q:
        pattern = f"%{q}%"
        filter_clause = or_(
            Employee.name.ilike(pattern),
            Employee.email.ilike(pattern),
        )
        base_query = base_query.where(filter_clause)
        count_query = count_query.where(filter_clause)

    total: int = cast(int, await db.scalar(count_query)) or 0

    rows = (
        (
            await db.execute(
                base_query
                .order_by(Employee.name)
                .offset((page - 1) * size)
                .limit(size)
            )
        )
        .scalars()
        .all()
    )

    return PaginatedEmployees(
        items=[
            EmployeeListItem(
                id=cast(int, e.id),
                name=cast(str, e.name),
                email=cast(str, e.email),
                department=cast(str, e.department),
                role=cast(str, e.role),
                joined_date=e.joined_date,
                linked=e.clerk_user_id is not None,
            )
            for e in rows
        ],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total else 0,
    )

@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeDetail,
    summary="Get a single employee with balances and request history",
)
async def get_employee_detail(
    employee_id: int,
    db: AsyncSession = Depends(get_session), # noqa: B008
    _admin: Employee = Depends(require_admin), # noqa: B008
) -> EmployeeDetail:
    emp = (
        await db.execute(
            select(Employee)
            .options(
                selectinload(Employee.vacation_balances),
                selectinload(Employee.request_histories),
            )
            .where(Employee.id == employee_id)
        )
    ).scalar_one_or_none()

    if emp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return EmployeeDetail(
        id=cast(int, emp.id),
        name=cast(str, emp.name),
        email=cast(str, emp.email),
        department=cast(str, emp.department),
        role=cast(str, emp.role),
        joined_date=emp.joined_date,
        benefits_year_reset=emp.benefits_year_reset,
        linked=emp.clerk_user_id is not None,
        balances=[
            BalanceSnapshot(
                leave_type=b.leave_type,
                total_days=b.total_days,
                used_days=b.used_days,
                remaining_days=b.remaining_days,
            )
            for b in emp.vacation_balances
        ],
        request_history=[
            RequestHistorySnapshot(
                id=cast(int, r.id),
                type=cast(str, r.type),
                status=cast(str, r.status),
                created_at=r.created_at,
                body=cast(str | None, r.body),
            )
            for r in sorted(emp.request_histories, key=lambda r: r.created_at, reverse=True)
        ],
    )

@router.patch(
    "/requests/{request_id}",
    response_model=ApproveRejectResponse,
    summary="Approve or reject an employee HR request",
)
async def approve_or_reject_request(
    request_id: int,
    body: ApproveRejectBody,
    db: AsyncSession = Depends(get_session),  # noqa: B008
    _admin: Employee = Depends(require_admin),  # noqa: B008
) -> ApproveRejectResponse:
    req = (
        await db.execute(select(RequestHistory).where(RequestHistory.id == request_id))
    ).scalar_one_or_none()

    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )

    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request is already '{req.status}'",
        )

    emp = (
        await db.execute(select(Employee).where(Employee.id == req.employee_id))
    ).scalar_one_or_none()

    if emp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    req_body: dict[str, object] = json.loads(cast(str, req.body)) if req.body else {}

    # On approval of a leave type — deduct days from the balance
    if body.status == "approved" and req.type in ("vacation", "sick", "pto"):
        days = float(cast(float, req_body.get("days", 0)))
        start_date_str = str(req_body.get("start_date", ""))
        try:
            year = (
                datetime.fromisoformat(start_date_str).year
                if start_date_str
                else datetime.now(UTC).year
            )
        except ValueError:
            year = datetime.now(UTC).year

        if days > 0:
            balance = (
                await db.execute(
                    select(VacationBalance).where(
                        VacationBalance.employee_id == req.employee_id,
                        VacationBalance.leave_type == req.type,
                        VacationBalance.year == year,
                    )
                )
            ).scalar_one_or_none()

            if balance is not None:
                balance.used_days += days

    # Store rejection reason inside the request body
    if body.status == "rejected" and body.rejection_reason:
        req_body["rejection_reason"] = body.rejection_reason
        req.body = json.dumps(req_body)  # type: ignore[assignment]

    req.status = body.status
    await db.commit()

    # Fetch updated balances to return in response
    current_year = datetime.now(UTC).year
    balances = (
        (
            await db.execute(
                select(VacationBalance).where(
                    VacationBalance.employee_id == req.employee_id,
                    VacationBalance.year == current_year,
                )
            )
        )
        .scalars()
        .all()
    )

    return ApproveRejectResponse(
        request_id=cast(int, req.id),
        employee_name=cast(str, emp.name),
        employee_email=cast(str, emp.email),
        request_type=cast(str, req.type),
        new_status=body.status,
        rejection_reason=body.rejection_reason,
        updated_balances=[
            BalanceSnapshot(
                leave_type=b.leave_type,
                total_days=b.total_days,
                used_days=b.used_days,
                remaining_days=b.remaining_days,
            )
            for b in balances
        ],
    )
