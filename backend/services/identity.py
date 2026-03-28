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
    customer_ref: str | None = None,
    customer_name: str | None = None,
    channel: str = "whatsapp",
) -> dict:
    bank_uuid = await resolve_bank_uuid(bank_id)
    async with AsyncSessionLocal() as session:
        customer = None

        if customer_ref:
            result = await session.execute(select(Customer).where(Customer.bank_id == bank_uuid))
            for row in result.scalars().all():
                attrs = row.attributes or {}
                ref = attrs.get("customer_ref") or attrs.get("external_customer_id")
                if ref and str(ref) == str(customer_ref):
                    customer = row
                    break

        if phone or email:
            if not customer:
                stmt = select(Customer).where(Customer.bank_id == bank_uuid)
                filters = []
                if phone:
                    filters.append(Customer.phone == phone)
                if email:
                    filters.append(Customer.email == email)
                stmt = stmt.where(or_(*filters))

                result = await session.execute(stmt)
                customer = result.scalar_one_or_none()

        if not customer:
            attributes = {}
            if customer_ref:
                attributes["customer_ref"] = str(customer_ref)

            customer = Customer(
                bank_id=bank_uuid,
                phone=phone,
                email=email,
                name=(customer_name.strip() if isinstance(customer_name, str) and customer_name.strip() else "New Customer"),
                preferred_channel=channel,
                attributes=attributes,
            )
            session.add(customer)
            await session.commit()
            await session.refresh(customer)
        else:
            customer.preferred_channel = channel
            attrs = customer.attributes or {}
            should_update = False
            clean_name = customer_name.strip() if isinstance(customer_name, str) else ""
            if clean_name and (not customer.name or customer.name == "New Customer"):
                customer.name = clean_name
                should_update = True
            if customer_ref and attrs.get("customer_ref") != str(customer_ref):
                attrs["customer_ref"] = str(customer_ref)
                should_update = True
            if phone and not customer.phone:
                customer.phone = phone
                should_update = True
            if email and not customer.email:
                customer.email = email
                should_update = True
            if should_update:
                customer.attributes = attrs
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
