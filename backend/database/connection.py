from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from database.models import Base


engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

RLS_TABLES = [
    "customers",
    "messages",
    "compliance_log",
    "loan_journeys",
    "channel_attribution",
    "dead_channels",
    "agents",
]


async def init_db() -> None:
    async with engine.connect() as conn:
        try:
            autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            await autocommit_conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
        except SQLAlchemyError:
            # Local non-container postgres may not have pgcrypto path configured.
            # UUIDs are generated in application code, so continue safely.
            pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        for table in RLS_TABLES:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
                await conn.execute(text(f"DROP POLICY IF EXISTS {table}_bank_isolation ON {table};"))
                await conn.execute(
                    text(
                        f"""
                        CREATE POLICY {table}_bank_isolation
                        ON {table}
                        USING (bank_id::text = current_setting('app.bank_id', true))
                        WITH CHECK (bank_id::text = current_setting('app.bank_id', true));
                        """
                    )
                )
            except SQLAlchemyError:
                # Keep local setup resilient; tables are already created.
                pass

        try:
            await conn.execute(
                text(
                    """
                    CREATE OR REPLACE FUNCTION prevent_compliance_modification()
                    RETURNS TRIGGER AS $$
                    BEGIN
                      RAISE EXCEPTION 'compliance_log is append-only. No updates or deletes allowed.';
                    END;
                    $$ LANGUAGE plpgsql;
                    """
                )
            )
            await conn.execute(text("DROP TRIGGER IF EXISTS compliance_log_immutable ON compliance_log;"))
            await conn.execute(
                text(
                    """
                    CREATE TRIGGER compliance_log_immutable
                    BEFORE UPDATE OR DELETE ON compliance_log
                    FOR EACH ROW EXECUTE FUNCTION prevent_compliance_modification();
                    """
                )
            )
        except SQLAlchemyError:
            # Some local clusters may not have plpgsql available due legacy setup.
            # Continue for local demo seeding; production should enforce trigger.
            pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
