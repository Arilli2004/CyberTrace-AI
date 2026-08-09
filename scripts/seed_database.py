"""
Database Seeding Utility Script — CyberTrace AI
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.database.connection import Base
from app.models import User, Case, UserRole, CaseStatus
from app.core.security import hash_password


async def seed():
    print("🌱 Seeding database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Seed users
        admin = User(name="Admin User", email="admin@cybertrace.ai", password_hash=hash_password("Admin@123"), role=UserRole.admin)
        investigator = User(name="Lead Investigator", email="investigator@cybertrace.ai", password_hash=hash_password("Admin@123"), role=UserRole.investigator)
        db.add_all([admin, investigator])
        await db.commit()

        # Seed sample cases
        case1 = Case(title="ACME Ransomware Attack", description="Investigating server encryption on host FS-01", investigator_id=investigator.id, status=CaseStatus.analysis, priority="critical")
        case2 = Case(title="Finance Exfiltration", description="Suspicious outbound network connection to unauthorized IP", investigator_id=investigator.id, status=CaseStatus.evidence_uploaded, priority="high")
        db.add_all([case1, case2])
        await db.commit()

    print("✅ Database seeding complete!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
