#!/usr/bin/env python3
"""Script to setup or reset admin user for SME Management."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from app.db.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.company import CompanySettings
from app.models.expense import ExpenseType
from app.core.security import get_password_hash, verify_password


def check_tables():
    """Check if database tables exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
    return 'users' in tables


def create_tables():
    """Create all database tables."""
    # Import all models to register them
    from app.models import user, company, client, supplier, article, invoice, expense, collaborator
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def check_admin_user(db, email: str):
    """Check if admin user exists."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"User found: {user.email}")
        print(f"  - ID: {user.id}")
        print(f"  - Name: {user.first_name} {user.last_name}")
        print(f"  - Active: {user.is_active}")
        print(f"  - Created: {user.created_at}")
        return user
    print(f"User not found: {email}")
    return None


def create_admin_user(db, email: str, password: str, first_name: str, last_name: str):
    """Create admin user."""
    # Check if exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"User {email} already exists!")
        return existing

    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Admin user created: {email}")
    return user


def reset_password(db, email: str, new_password: str):
    """Reset user password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"User not found: {email}")
        return False

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    print(f"Password reset for: {email}")
    return True


def test_login(db, email: str, password: str):
    """Test login with credentials."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"LOGIN FAILED: User not found: {email}")
        return False

    if not verify_password(password, user.hashed_password):
        print(f"LOGIN FAILED: Wrong password for {email}")
        return False

    if not user.is_active:
        print(f"LOGIN FAILED: User {email} is disabled")
        return False

    print(f"LOGIN SUCCESS: {email}")
    return True


def main():
    print("=" * 50)
    print("SME Management - Admin Setup Script")
    print("=" * 50)

    # Check tables
    print("\n[1] Checking database tables...")
    if not check_tables():
        print("Tables not found. Creating...")
        create_tables()
    else:
        print("Tables exist.")

    # Default admin credentials
    admin_email = "admin@example.com"
    admin_password = "Admin123!"

    db = SessionLocal()
    try:
        # Check/create admin
        print(f"\n[2] Checking admin user ({admin_email})...")
        user = check_admin_user(db, admin_email)

        if not user:
            print("\n[3] Creating admin user...")
            user = create_admin_user(
                db,
                email=admin_email,
                password=admin_password,
                first_name="Admin",
                last_name="User"
            )

        # Test login
        print(f"\n[4] Testing login...")
        if test_login(db, admin_email, admin_password):
            print("\n" + "=" * 50)
            print("SUCCESS! You can login with:")
            print(f"  Email: {admin_email}")
            print(f"  Password: {admin_password}")
            print("=" * 50)
        else:
            print("\n[!] Login test failed. Resetting password...")
            reset_password(db, admin_email, admin_password)
            if test_login(db, admin_email, admin_password):
                print("\n" + "=" * 50)
                print("Password reset successful! You can login with:")
                print(f"  Email: {admin_email}")
                print(f"  Password: {admin_password}")
                print("=" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    main()
