import os
from app import create_app, db
from app.models import User, FacultyProfile, AlumniProfile, StudentProfile, Job, Roadmap, Skill, Badge, Certificate

def reset_database():
    app = create_app()
    with app.app_context():
        print("--- Resetting Database ---")
        
        # Drop all tables
        print("Dropping all existing tables...")
        db.drop_all()
        print("All tables dropped successfully.")
        
        # Create all tables
        print("Creating all tables from models...")
        db.create_all()
        print("All tables created successfully.")
        
        # Create default admin user
        admin_email = "admin@alumninet.com"
        from app import bcrypt
        
        print("Creating default administrator...")
        hashed_pw = bcrypt.generate_password_hash("admin@123").decode('utf-8')
        admin_user = User(
            username="Administrator",
            email=admin_email,
            password=hashed_pw,
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: admin@123")
        print("\n--- Database Reset Complete ---")

if __name__ == '__main__':
    reset_database()
