# backend/api/routers/admin.py
"""
Single admin endpoint: approve or reject an employee HR request.
No Clerk auth required — accessible directly for demo/testing.
Approving a leave request updates VacationBalance.used_days so the
employee's dashboard balance reflects the change immediately.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.admin import ApproveRejectBody, ApproveRejectResponse, BalanceSnapshot
from db.models import Employee, RequestHistory, VacationBalance
from db.session import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch(
    "/requests/{request_id}",
    response_model=ApproveRejectResponse,
    summary="Approve or reject an employee HR request",
)
async def approve_or_reject_request(
    request_id: int,
    body: ApproveRejectBody,
    db: AsyncSession = Depends(get_session),  # noqa: B008
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
