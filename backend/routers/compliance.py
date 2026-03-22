from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import ComplianceLog, Customer
from services.bank import resolve_bank_uuid


router = APIRouter()


@router.get("/passport/{bank_id}")
async def get_passport(
    bank_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    customer_id: str | None = None,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
):
    bank_id = await resolve_bank_uuid(bank_id)
    filters = [ComplianceLog.bank_id == bank_id]
    if customer_id:
        filters.append(ComplianceLog.customer_id == customer_id)
    if from_date:
        filters.append(ComplianceLog.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        filters.append(ComplianceLog.created_at <= datetime.fromisoformat(to_date))

    query = (
        select(ComplianceLog, Customer.name)
        .join(Customer, and_(Customer.id == ComplianceLog.customer_id, Customer.bank_id == bank_id))
        .where(*filters)
        .order_by(ComplianceLog.created_at.desc())
    )
    rows = (await db.execute(query)).all()

    data = [
        {
            "audit_token": str(log.audit_token),
            "customer": name,
            "channel": "omnichannel",
            "dnc": log.dnc_result,
            "consent": log.consent_valid,
            "rbi": log.rbi_content_passed,
            "tone": log.tone_fit_passed,
            "safety": log.safety_check_passed,
            "result": log.overall_result,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "hash_chain": log.hash_chain,
        }
        for log, name in rows
    ]

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()) if data else ["audit_token"])
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=compliance_passport_{bank_id}.csv"},
        )

    return {"bank_id": bank_id, "records": data, "count": len(data)}


@router.get("/verify/{audit_token}")
async def verify_hash(audit_token: str, db: AsyncSession = Depends(get_db)) -> dict:
    q = await db.execute(select(ComplianceLog).where(ComplianceLog.audit_token == audit_token))
    record = q.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="audit token not found")

    prev = await db.execute(
        select(ComplianceLog)
        .where(
            ComplianceLog.bank_id == record.bank_id,
            ComplianceLog.created_at < record.created_at,
        )
        .order_by(ComplianceLog.created_at.desc())
        .limit(1)
    )
    prev_record = prev.scalar_one_or_none()
    prev_hash = prev_record.hash_chain if prev_record else "GENESIS"

    payload = f"{record.bank_id}|{record.customer_id}|{record.message_id}|{record.overall_result}|{record.created_at.isoformat()}|{prev_hash}"
    expected = hashlib.sha256(payload.encode()).hexdigest()

    return {
        "valid": expected == record.hash_chain,
        "record": {
            "audit_token": str(record.audit_token),
            "result": record.overall_result,
            "hash_chain": record.hash_chain,
        },
    }


@router.get("/stats/{bank_id}")
async def compliance_stats(bank_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    bank_id = await resolve_bank_uuid(bank_id)
    total = (
        await db.execute(
            select(func.count()).select_from(ComplianceLog).where(ComplianceLog.bank_id == bank_id)
        )
    ).scalar_one()

    passed = (
        await db.execute(
            select(func.count())
            .select_from(ComplianceLog)
            .where(ComplianceLog.bank_id == bank_id, ComplianceLog.overall_result == "PASS")
        )
    ).scalar_one()

    dnc_blocked = (
        await db.execute(
            select(func.count())
            .select_from(ComplianceLog)
            .where(ComplianceLog.bank_id == bank_id, ComplianceLog.dnc_result != "not_on_list")
        )
    ).scalar_one()

    consent_blocked = (
        await db.execute(
            select(func.count())
            .select_from(ComplianceLog)
            .where(ComplianceLog.bank_id == bank_id, ComplianceLog.consent_valid.is_(False))
        )
    ).scalar_one()

    violations_prevented = total - passed

    return {
        "pass_rate": round((passed / total) * 100, 2) if total else 100.0,
        "violations_prevented": violations_prevented,
        "dnc_blocked": dnc_blocked,
        "consent_blocked": consent_blocked,
    }
