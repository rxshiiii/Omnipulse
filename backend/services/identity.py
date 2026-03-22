from __future__ import annotations

from sqlalchemy import or_, select

from database.connection import AsyncSessionLocal
from database.models import Customer
from services.bank import resolve_bank_uuid


async def resolve_customer(
    bank_id: str,
    *,
    phone: str | None = None,
    email: str | None = None,
    channel: str = "whatsapp",
) -> dict:
    bank_uuid = await resolve_bank_uuid(bank_id)
    async with AsyncSessionLocal() as session:
        stmt = select(Customer).where(Customer.bank_id == bank_uuid)
        if phone or email:
            filters = []
            if phone:
                filters.append(Customer.phone == phone)
            if email:
                filters.append(Customer.email == email)
            stmt = stmt.where(or_(*filters))

        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(
                bank_id=bank_uuid,
                phone=phone,
                email=email,
                name="New Customer",
                preferred_channel=channel,
                attributes={},
            )
            session.add(customer)
            await session.commit()
            await session.refresh(customer)
        else:
            customer.preferred_channel = channel
            await session.commit()

        return {
            "id": str(customer.id),
            "bank_id": str(customer.bank_id),
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "preferred_channel": customer.preferred_channel,
            "frustration_score": customer.frustration_score,
            "emotional_state": customer.emotional_state,
            "exit_risk": customer.exit_risk,
            "attributes": customer.attributes or {},
        }
