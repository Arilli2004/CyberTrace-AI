"""
Create Admin User Script — CyberTrace AI
Run: python scripts/create_admin.py
"""
import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.core.security import hash_password
from app.database.connection import Base
from app.models import User, UserRole


async def create_admin():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    name = input("Admin Name: ").strip() or "Admin"
    email = input("Admin Email: ").strip() or "admin@cybertrace.ai"
    password = input("Admin Password: ").strip() or "Admin@123"

    async with AsyncSession() as session:
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"❌ User with email {email} already exists")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
        )
        session.add(admin)
        await session.commit()
        print(f"✅ Admin user created: {email}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin())
