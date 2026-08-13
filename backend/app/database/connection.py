"""
Database Connection — Async SQLAlchemy with Automatic Fallback & Auto-Seeding
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, text
from typing import AsyncGenerator
import sys

from app.core.config import settings

# ─── Global State ─────────────────────────────────────────────────────────────
engine = None
AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass


async def init_db():
    """Initialize engine, create tables, and seed default data if needed."""
    global engine, AsyncSessionLocal

    if AsyncSessionLocal is not None:
        return

    # 1. Try primary database (PostgreSQL)
    try:
        pg_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        async with pg_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        engine = pg_engine
        print("[OK] Connected to PostgreSQL database successfully.")
    except Exception as e:
        print(f"[NOTICE] PostgreSQL connection failed: {e}. Falling back to SQLite local database.")
        sqlite_url = "sqlite+aiosqlite:///./cybertrace.db"
        engine = create_async_engine(sqlite_url, echo=False)

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # 2. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. Auto-seed default users if empty
    from app.models import User, Case, UserRole, CaseStatus
    from app.core.security import hash_password

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(User))
            users = result.scalars().all()
            if not users:
                print("[SEED] Seeding default users and sample cases...")
                admin = User(
                    name="Admin User",
                    email="admin@cybertrace.ai",
                    password_hash=hash_password("Admin@123"),
                    role=UserRole.admin,
                )
                investigator = User(
                    name="Lead Investigator",
                    email="investigator@cybertrace.ai",
                    password_hash=hash_password("Admin@123"),
                    role=UserRole.investigator,
                )
                session.add_all([admin, investigator])
                await session.commit()

                case1 = Case(
                    title="ACME Ransomware Attack",
                    description="Investigating server encryption on host FS-01",
                    investigator_id=investigator.id,
                    status=CaseStatus.analysis,
                    priority="critical",
                )
                case2 = Case(
                    title="Finance Exfiltration",
                    description="Suspicious outbound network connection to unauthorized IP",
                    investigator_id=investigator.id,
                    status=CaseStatus.evidence_uploaded,
                    priority="high",
                )
                session.add_all([case1, case2])
                await session.commit()
                print("[OK] Default users and sample cases seeded successfully!")

            # Auto-seed sample evidence files if empty
            from app.models import Evidence, EvidenceType
            from app.services.storage_service import StorageService
            import os, shutil

            ev_result = await session.execute(select(Evidence))
            ev_list = ev_result.scalars().all()
            if not ev_list:
                print("[SEED] Seeding sample evidence records...")
                base_uploads = StorageService.get_upload_base_dir()
                sample_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_evidence"))
                if not os.path.exists(sample_dir):
                    sample_dir = os.path.abspath(os.path.join(os.getcwd(), "sample_evidence"))

                csv_source = os.path.join(sample_dir, "auth_audit.csv")

                c1_upload_dir = os.path.join(base_uploads, "1")
                os.makedirs(c1_upload_dir, exist_ok=True)
                
                c1_uuid = "22285a1f-edec-4b90-8dca-f4e3350ce653"
                c1_dest = os.path.join(c1_upload_dir, f"{c1_uuid}.csv")
                if os.path.exists(csv_source):
                    shutil.copy(csv_source, c1_dest)

                ev1 = Evidence(
                    uuid_id=c1_uuid,
                    case_id=1,
                    filename=f"{c1_uuid}.csv",
                    original_filename="auth_audit.csv",
                    storage_path=c1_dest,
                    file_path=c1_dest,
                    extension="csv",
                    mime_type="text/csv",
                    size=os.path.getsize(c1_dest) if os.path.exists(c1_dest) else 686,
                    sha256="d7a18bfa98e1f0e21a2c3b4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
                    file_type=EvidenceType.csv,
                    uploaded_by=1,
                    verification_status="verified",
                    normalization_status="pending",
                    graph_status="pending",
                    csp_status="pending",
                    correlation_status="pending",
                    timeline_status="pending",
                    processing_stage="VERIFIED",
                    parser_status="pending",
                    is_parsed=False,
                )
                session.add(ev1)
                await session.commit()
                print("[OK] Sample evidence records seeded successfully!")
        except Exception as seed_err:
            print(f"[NOTICE] Seeding info: {seed_err}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get a database session."""
    if AsyncSessionLocal is None:
        await init_db()

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


