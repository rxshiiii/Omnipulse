from __future__ import annotations

import asyncio
import hashlib
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.append(str(BACKEND))

from database.connection import AsyncSessionLocal, init_db  # noqa: E402
from database.models import (  # noqa: E402
    Agent,
    Bank,
    ChannelAttribution,
    ComplianceLog,
    Customer,
    DeadChannel,
    LoanJourney,
    Message,
)


BANK_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CUSTOMER_IDS = {
    "ramesh": uuid.UUID("22222222-2222-2222-2222-222222222221"),
    "kavita": uuid.UUID("22222222-2222-2222-2222-222222222222"),
    "suresh": uuid.UUID("22222222-2222-2222-2222-222222222223"),
    "meena": uuid.UUID("22222222-2222-2222-2222-222222222224"),
}


def make_hash(prev_hash: str, bank_id: str, customer_id: str, message_id: str, result: str, ts: datetime) -> str:
    payload = f"{bank_id}|{customer_id}|{message_id}|{result}|{ts.isoformat()}|{prev_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()


async def seed() -> None:
    await init_db()

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        bank = await session.get(Bank, BANK_UUID)
        if not bank:
            bank = Bank(id=BANK_UUID, code="UB", name="Union Bank of India")
            session.add(bank)
            await session.commit()

        customers = [
            Customer(
                id=CUSTOMER_IDS["ramesh"],
                bank_id=BANK_UUID,
                phone="9876543210",
                email="ramesh.kumar@example.com",
                name="Ramesh Kumar",
                preferred_channel="whatsapp",
                frustration_score=8.4,
                emotional_state="frustrated",
                exit_risk="high",
                attributes={
                    "kcc_limit": 50000,
                    "kcc_status": "blocked",
                    "branch": "Vidarbha",
                    "preferred_language": "marathi",
                    "whatsapp_consent": True,
                    "loan_stage": "disbursement",
                },
            ),
            Customer(
                id=CUSTOMER_IDS["kavita"],
                bank_id=BANK_UUID,
                phone="9876543211",
                email="kavita.desai@example.com",
                name="Kavita Desai",
                preferred_channel="whatsapp",
                frustration_score=7.2,
                emotional_state="frustrated",
                exit_risk="medium",
                attributes={"issue": "rtgs_failed", "rtgs_amount": 200000, "whatsapp_consent": True},
            ),
            Customer(
                id=CUSTOMER_IDS["suresh"],
                bank_id=BANK_UUID,
                phone="9876543212",
                email="suresh.patil@example.com",
                name="Suresh Patil",
                preferred_channel="whatsapp",
                frustration_score=5.8,
                emotional_state="concerned",
                exit_risk="low",
                attributes={
                    "issue": "double_debit",
                    "debit_amount": 5000,
                    "contacts_count": 3,
                    "whatsapp_consent": True,
                },
            ),
            Customer(
                id=CUSTOMER_IDS["meena"],
                bank_id=BANK_UUID,
                phone="9876543213",
                email="meena.sharma@example.com",
                name="Meena Sharma",
                preferred_channel="email",
                frustration_score=2.1,
                emotional_state="calm",
                exit_risk="low",
                attributes={
                    "loan_stage": "sanctioning",
                    "loan_amount": 4500000,
                    "loan_type": "home_loan",
                    "whatsapp_consent": True,
                },
            ),
        ]

        for customer in customers:
            if not await session.get(Customer, customer.id):
                session.add(customer)

        journey_steps = [
            ("Application", "Retail Ops"),
            ("KYC", "Compliance Desk"),
            ("Legal", "Legal Cell"),
            ("Valuation", "Field Ops"),
            ("Sanctioning", "Credit Team"),
            ("Disbursement", "Treasury"),
        ]

        for idx, (stage, dept) in enumerate(journey_steps):
            status = "issue" if stage == "Valuation" else ("complete" if idx < 3 else "pending")
            session.add(
                LoanJourney(
                    bank_id=BANK_UUID,
                    customer_id=CUSTOMER_IDS["ramesh"],
                    stage=stage,
                    department=dept,
                    agent_id="UB-4421",
                    action_taken=f"Updated {stage.lower()} status",
                    notes="KCC verification mismatch" if stage == "Valuation" else "Normal progress",
                    status=status,
                    created_at=now - timedelta(days=7 - idx),
                )
            )

        seed_messages = []
        for key, cid in CUSTOMER_IDS.items():
            for i in range(8):
                inbound = i % 2 == 0
                created = now - timedelta(hours=(50 - i * 4))
                base_content = f"{key} message {i + 1}"
                translated = None
                audio_url = None
                original_lang = "en"
                channel = "whatsapp"

                if key == "ramesh" and i == 2:
                    channel = "voice"
                    original_lang = "mr"
                    base_content = "माझे KCC खाते अजूनही ब्लॉक आहे"
                    translated = "My KCC account is still blocked"
                    audio_url = "https://example.com/ramesh-voice.ogg"

                if key == "ramesh" and i in [4, 6]:
                    channel = "sms"
                if key == "meena" and i in [1, 3, 5]:
                    channel = "email"

                seed_messages.append(
                    Message(
                        bank_id=BANK_UUID,
                        customer_id=cid,
                        channel=channel,
                        direction="inbound" if inbound else "outbound",
                        content=base_content,
                        original_language=original_lang,
                        translated_content=translated,
                        audio_url=audio_url,
                        intent_label="kcc_issue" if key == "ramesh" else "query",
                        intent_confidence=0.91,
                        ai_draft=(
                            "Ramesh ji, we understand your concern. KCC unblock review is initiated and branch team will call you within 4 working hours. — Priya, Union Bank Support"
                            if not inbound
                            else None
                        ),
                        sent_content=None if inbound else "Thank you, your issue is being processed.",
                        agent_id="UB-4421" if not inbound else None,
                        message_type="transactional",
                        created_at=created,
                    )
                )

        session.add_all(seed_messages)
        await session.flush()

        outbound = [m for m in seed_messages if m.direction == "outbound"]
        prev_hash = "GENESIS"
        for m in outbound:
            ts = m.created_at or now
            h = make_hash(prev_hash, str(BANK_UUID), str(m.customer_id), str(m.id), "PASS", ts)
            prev_hash = h
            session.add(
                ComplianceLog(
                    bank_id=BANK_UUID,
                    customer_id=m.customer_id,
                    message_id=m.id,
                    dnc_checked=True,
                    dnc_result="not_on_list",
                    consent_valid=True,
                    rbi_content_passed=True,
                    tone_fit_passed=True,
                    safety_check_passed=True,
                    overall_result="PASS",
                    fail_reason=None,
                    agent_version="v1.0",
                    hash_chain=h,
                    created_at=ts,
                )
            )

        session.add_all(
            [
                ChannelAttribution(
                    bank_id=BANK_UUID,
                    customer_id=CUSTOMER_IDS["ramesh"],
                    channel="whatsapp",
                    touch_weight=72.0,
                    total_interactions=18,
                    last_interaction=now - timedelta(hours=1),
                    updated_at=now,
                ),
                ChannelAttribution(
                    bank_id=BANK_UUID,
                    customer_id=CUSTOMER_IDS["ramesh"],
                    channel="sms",
                    touch_weight=28.0,
                    total_interactions=7,
                    last_interaction=now - timedelta(days=1),
                    updated_at=now,
                ),
                ChannelAttribution(
                    bank_id=BANK_UUID,
                    customer_id=CUSTOMER_IDS["kavita"],
                    channel="whatsapp",
                    touch_weight=100.0,
                    total_interactions=11,
                    last_interaction=now - timedelta(hours=2),
                    updated_at=now,
                ),
            ]
        )

        session.add(
            DeadChannel(
                bank_id=BANK_UUID,
                customer_id=CUSTOMER_IDS["ramesh"],
                channel="email",
                buried_at=now - timedelta(days=420),
                reason="No engagement",
                inactive_days=420,
            )
        )

        session.add(
            Agent(
                bank_id=BANK_UUID,
                name="Priya Sharma",
                email="priya.sharma@unionbank.co.in",
                role="agent",
                is_online=True,
            )
        )

        await session.commit()

    print("Seed complete. Bank UUID:", BANK_UUID)


if __name__ == "__main__":
    asyncio.run(seed())
