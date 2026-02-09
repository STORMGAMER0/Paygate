"""Script to create an admin user."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import User, UserRole
from app.auth.utils import hash_password


def create_admin(email: str, password: str, full_name: str):
    """Create an admin user."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User with email {email} already exists.")
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                db.commit()
                print(f"Updated {email} to admin role.")
            return

        # Create admin user
        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print(f"Admin user created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_admin.py <email> <password> <full_name>")
        print("Example: python create_admin.py admin@example.com SecurePass123! 'Admin User'")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    full_name = " ".join(sys.argv[3:])

    create_admin(email, password, full_name)
