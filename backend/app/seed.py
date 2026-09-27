import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.entities import User, UserRole, Client

async def seed_database():
    """Seed initial Admin and 3 isolated Healthcare Clients."""
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(User).where(User.email == "admin@flplatform.org"))
        if result.scalars().first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding initial institutions and users...")

        # 1. Seed 3 Isolated Healthcare Clients
        clients_data = [
            {
                "id": "client_1",
                "name": "Hospital/Clinic A (Metropolitan General)",
                "institution_type": "Tertiary Care Hospital",
                "location": "North Medical District"
            },
            {
                "id": "client_2",
                "name": "Hospital/Clinic B (St. Jude Healthcare)",
                "institution_type": "Cardiovascular & Specialty Clinic",
                "location": "Central Healthcare Hub"
            },
            {
                "id": "client_3",
                "name": "Hospital/Clinic C (Regional Health Center)",
                "institution_type": "Community Medical Center",
                "location": "Eastern Rural Health Network"
            }
        ]

        for c in clients_data:
            client = Client(
                id=c["id"],
                name=c["name"],
                institution_type=c["institution_type"],
                location=c["location"],
                status="active"
            )
            session.add(client)
        
        await session.flush()

        # 2. Seed Admin User
        admin_user = User(
            email="admin@flplatform.org",
            hashed_password=get_password_hash("admin123"),
            full_name="Central FL Server Administrator",
            role=UserRole.ADMIN.value,
            client_id=None,
            is_active=True
        )
        session.add(admin_user)

        # 3. Seed Client Users (Hospital A, B, C)
        client_users = [
            {
                "email": "hospital_a@flplatform.org",
                "password": "client1pass",
                "name": "Dr. Sarah Chen (Hospital A Chief ML Lead)",
                "client_id": "client_1"
            },
            {
                "email": "hospital_b@flplatform.org",
                "password": "client2pass",
                "name": "Dr. Marcus Vance (Hospital B Research Director)",
                "client_id": "client_2"
            },
            {
                "email": "hospital_c@flplatform.org",
                "password": "client3pass",
                "name": "Dr. Elena Rostova (Hospital C Health Informatics)",
                "client_id": "client_3"
            }
        ]

        for u in client_users:
            client_user = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["name"],
                role=UserRole.CLIENT.value,
                client_id=u["client_id"],
                is_active=True
            )
            session.add(client_user)

        await session.commit()
        print("Seeding completed successfully:")
        print("  - Admin: admin@flplatform.org / admin123")
        print("  - Client 1: hospital_a@flplatform.org / client1pass")
        print("  - Client 2: hospital_b@flplatform.org / client2pass")
        print("  - Client 3: hospital_c@flplatform.org / client3pass")
        print("  - Initial Models: None published (satisfies Rule 9 & Rule 47 Stage 1)")

if __name__ == "__main__":
    asyncio.run(seed_database())
