import os
import sys
from app import create_app, db, bcrypt
from app.models import User, FacultyProfile, AlumniProfile, StudentProfile

def setup():
    app = create_app()
    with app.app_context():
        print("--- AlumniNet Database Setup ---")
        
        # 1. Create Tables
        print("Creating all tables...")
        db.create_all()
        print("Tables created successfully.")
        
        # 2. Check for Admin User
        admin_email = "admin@alumninet.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            print(f"Creating default administrator: {admin_email}")
            hashed_pw = bcrypt.generate_password_hash("admin@123").decode('utf-8')
            new_admin = User(
                username="Administrator",
                email=admin_email,
                password=hashed_pw,
                role="admin"
            )
            db.session.add(new_admin)
            db.session.commit()
            print("Admin account created successfully!")
            print("Credentials: admin@alumninet.com / admin@123")
        else:
            print("Admin account already exists.")
            
        print("\nSetup Complete!")
        print("You can now run the application using 'python run.py'.")

if __name__ == "__main__":
    setup()
