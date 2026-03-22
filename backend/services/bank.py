from __future__ import annotations

import uuid

from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import Bank


UNION_BANK_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")


async def resolve_bank_uuid(bank_identifier: str) -> str:
    try:
        parsed = uuid.UUID(bank_identifier)
        return str(parsed)
    except ValueError:
        pass

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Bank).where((Bank.code == bank_identifier) | (Bank.name == bank_identifier))
        )
        bank = result.scalar_one_or_none()
        if bank:
            return str(bank.id)

        if bank_identifier == "union_bank_demo":
            fallback = await session.execute(select(Bank).order_by(Bank.created_at.asc()).limit(1))
            first_bank = fallback.scalar_one_or_none()
            if first_bank:
                return str(first_bank.id)

            # Bootstrap demo tenant bank when no bank rows exist yet.
            bank = Bank(id=UNION_BANK_UUID, code="UB", name="Union Bank of India")
            session.add(bank)
            await session.commit()
            return str(bank.id)

    return bank_identifier
