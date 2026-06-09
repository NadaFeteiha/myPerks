"""
myPerks — Dev Seed Data
backend/db/seed.py

Usage:
    python -m db.seed

Populates the database with realistic dev data:
- 3 employees + 1 HR admin
- vacation balances (vacation, sick, pto) per person for current year
- sample request histories
- sample conversations
"""

import asyncio
import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Conversation,
    Employee,
    Message,
    RequestHistory,
    VacationBalance,
)
from db.session import AsyncSessionLocal

CURRENT_YEAR = datetime.datetime.now().year
# Benefits year resets on Jan 1. Banner (T37) shows the upcoming reset date.
BENEFITS_YEAR_RESET = datetime.date(CURRENT_YEAR + 1, 1, 1)


async def clear_data(session: AsyncSession) -> None:
    """Delete all existing seed data in correct order (respect FK constraints)."""
    await session.execute(text("DELETE FROM messages"))
    await session.execute(text("DELETE FROM conversations"))
    await session.execute(text("DELETE FROM request_histories"))
    await session.execute(text("DELETE FROM vacation_balances"))
    await session.execute(text("DELETE FROM document_chunks"))
    await session.execute(text("DELETE FROM documents"))
    await session.execute(text("DELETE FROM employees"))
    await session.commit()
    print("✓ Cleared existing data")


async def seed_employees(session: AsyncSession) -> list[Employee]:
    employees = [
        Employee(
            clerk_user_id="clerk_user_001",
            name="Alice Johnson",
            email="alice.johnson@myperks.dev",
            role="employee",
            department="engineering",
            joined_date=datetime.date(2022, 3, 1),
            benefits_year_reset=BENEFITS_YEAR_RESET,
        ),
        Employee(
            clerk_user_id="clerk_user_002",
            name="Bob Martinez",
            email="bob.martinez@myperks.dev",
            role="employee",
            department="hr",
            joined_date=datetime.date(2021, 7, 15),
            benefits_year_reset=BENEFITS_YEAR_RESET,
        ),
        Employee(
            clerk_user_id="clerk_user_003",
            name="Carol Chen",
            email="carol.chen@myperks.dev",
            role="employee",
            department="marketing",
            joined_date=datetime.date(2023, 9, 12),
            benefits_year_reset=BENEFITS_YEAR_RESET,
        ),
    ]
    session.add_all(employees)
    await session.flush()  # get IDs without committing
    print(f"✓ Seeded {len(employees)} employees")
    return employees


async def seed_hr_admin(session: AsyncSession) -> Employee:
    # Pre-created, UNLINKED row: clerk_user_id is None until this person signs in
    # through Clerk, at which point onboarding links it by email (T27). For that
    # link to work, the email below MUST be the real address you log in with.
    hr_admin = Employee(
        clerk_user_id=None,
        name="HR Admin",
        email="aymanlahmamsi@gmail.com",  # TODO: set before seeding
        role="hr_admin",
        department="hr",
        joined_date=datetime.date(2020, 1, 6),
        benefits_year_reset=BENEFITS_YEAR_RESET,
    )
    session.add(hr_admin)
    await session.flush()
    print("✓ Seeded 1 HR admin (unlinked — links by email on first login)")
    return hr_admin


async def seed_vacation_balances(
    session: AsyncSession, employees: list[Employee]
) -> None:
    balances = []
    leave_configs = [
        ("vacation", 15.0, 3.0),
        ("sick", 10.0, 1.0),
        ("pto", 5.0, 0.0),
    ]
    for employee in employees:
        for leave_type, total, used in leave_configs:
            balances.append(
                VacationBalance(
                    employee_id=employee.id,
                    leave_type=leave_type,
                    total_days=total,
                    used_days=used,
                    year=CURRENT_YEAR,
                )
            )
    session.add_all(balances)
    await session.flush()
    print(f"✓ Seeded {len(balances)} vacation balances")


async def seed_request_histories(
    session: AsyncSession, employees: list[Employee]
) -> None:
    alice, bob, carol = employees
    requests = [
        # Alice — approved vacation request
        RequestHistory(
            employee_id=alice.id,
            type="vacation",
            status="approved",
            created_at=datetime.datetime(CURRENT_YEAR, 3, 10),
            body=(
                '{"start_date": "2026-03-17", '
                '"end_date": "2026-03-19", '
                '"days": 3, '
                '"reason": "Spring break trip"}'
            ),
        ),
        # Alice — pending PTO request
        RequestHistory(
            employee_id=alice.id,
            type="pto",
            status="pending",
            created_at=datetime.datetime(CURRENT_YEAR, 5, 1),
            body=(
                '{"start_date": "2026-05-30", '
                '"end_date": "2026-05-30", '
                '"days": 1, '
                '"reason": "Personal errand"}'
            ),
        ),
        # Bob — approved sick leave
        RequestHistory(
            employee_id=bob.id,
            type="sick",
            status="approved",
            created_at=datetime.datetime(CURRENT_YEAR, 2, 5),
            body=(
                '{"start_date": "2026-02-05", '
                '"end_date": "2026-02-05", '
                '"days": 1, '
                '"reason": "Doctor appointment"}'
            ),
        ),
        # Bob — rejected vacation request
        RequestHistory(
            employee_id=bob.id,
            type="vacation",
            status="rejected",
            created_at=datetime.datetime(CURRENT_YEAR, 4, 15),
            body=(
                '{"start_date": "2026-07-04", '
                '"end_date": "2026-07-11", '
                '"days": 6, '
                '"reason": "Summer vacation", '
                '"rejection_reason": "Team coverage conflict"}'
            ),
        ),
        # Carol — approved vacation request
        RequestHistory(
            employee_id=carol.id,
            type="vacation",
            status="approved",
            created_at=datetime.datetime(CURRENT_YEAR, 1, 20),
            body=(
                '{"start_date": "2026-02-14", '
                '"end_date": "2026-02-14", '
                '"days": 1, '
                '"reason": "Valentine\'s Day"}'
            ),
        ),
        # Carol — pending reimbursement
        RequestHistory(
            employee_id=carol.id,
            type="reimbursement",
            status="pending",
            created_at=datetime.datetime(CURRENT_YEAR, 5, 10),
            body=(
                '{"amount": 250.00, '
                '"currency": "USD", '
                '"description": "Marketing conference registration fee"}'
            ),
        ),
    ]
    session.add_all(requests)
    await session.flush()
    print(f"✓ Seeded {len(requests)} request histories")


async def seed_conversations(session: AsyncSession, employees: list[Employee]) -> None:
    alice, bob, _ = employees

    # Alice's conversation with the AI
    alice_convo = Conversation(
        employee_id=alice.id,
        title="Vacation balance inquiry",
        created_at=datetime.datetime(CURRENT_YEAR, 5, 15, 9, 0),
        updated_at=datetime.datetime(CURRENT_YEAR, 5, 15, 9, 5),
    )
    session.add(alice_convo)
    await session.flush()

    session.add_all(
        [
            Message(
                conversation_id=alice_convo.id,
                role="user",
                content="How many vacation days do I have left this year?",
                created_at=datetime.datetime(CURRENT_YEAR, 5, 15, 9, 0),
            ),
            Message(
                conversation_id=alice_convo.id,
                role="assistant",
                content=(
                    "You have 12 vacation days remaining for 2026. "
                    "You started with 15 days and have used 3 days so far."
                ),
                created_at=datetime.datetime(CURRENT_YEAR, 5, 15, 9, 1),
            ),
            Message(
                conversation_id=alice_convo.id,
                role="user",
                content="Can I request next Friday off?",
                created_at=datetime.datetime(CURRENT_YEAR, 5, 15, 9, 3),
            ),
            Message(
                conversation_id=alice_convo.id,
                role="assistant",
                content=(
                    "Sure! I can help you submit a vacation request "
                    "for Friday May 23rd. "
                    "Would you like me to go ahead and submit that?"
                ),
                created_at=datetime.datetime(CURRENT_YEAR, 5, 15, 9, 4),
            ),
        ]
    )

    # Bob's conversation with the AI
    bob_convo = Conversation(
        employee_id=bob.id,
        title="Sick leave policy question",
        created_at=datetime.datetime(CURRENT_YEAR, 5, 18, 14, 0),
        updated_at=datetime.datetime(CURRENT_YEAR, 5, 18, 14, 3),
    )
    session.add(bob_convo)
    await session.flush()

    session.add_all(
        [
            Message(
                conversation_id=bob_convo.id,
                role="user",
                content="Do I need a doctor's note for sick leave?",
                created_at=datetime.datetime(CURRENT_YEAR, 5, 18, 14, 0),
            ),
            Message(
                conversation_id=bob_convo.id,
                role="assistant",
                content=(
                    "According to company policy, a doctor's note is required "
                    "for sick leave exceeding 3 consecutive days. "
                    "For 1-3 days, no documentation is needed."
                ),
                created_at=datetime.datetime(CURRENT_YEAR, 5, 18, 14, 1),
            ),
        ]
    )

    print("✓ Seeded 2 conversations with messages")


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        print("\n🌱 Starting seed...\n")
        await clear_data(session)
        employees = await seed_employees(session)
        hr_admin = await seed_hr_admin(session)
        # HR admin gets balances too (they're staff with their own leave).
        await seed_vacation_balances(session, [*employees, hr_admin])
        await seed_request_histories(session, employees)
        await seed_conversations(session, employees)
        await session.commit()
        print("\n✅ Seed complete!\n")


if __name__ == "__main__":
    asyncio.run(seed())
