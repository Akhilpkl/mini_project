import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User, AlumniProfile, StudentProfile, FacultyProfile
from app import bcrypt

app = create_app()
with app.app_context():
    # Find or create admin
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User.query.filter_by(email='admin@aluminet.edu').first()
    
    hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
    
    if not admin:
        admin = User(username='admin', email='admin@aluminet.edu', password=hashed_pw, role='admin')
        db.session.add(admin)
        print("Created new admin: admin@aluminet.edu / admin123")
    else:
        admin.password = hashed_pw
        admin.email = 'admin@aluminet.edu'
        admin.role = 'admin'
        print(f"Updated existing admin ({admin.username}): admin@aluminet.edu / admin123")
    
    db.session.commit()
