import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User
from app import bcrypt

app = create_app()
with app.app_context():
    # Check for any admin
    admins = User.query.filter_by(role='admin').all()
    
    hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
    
    if not admins:
        # Check if email is taken
        existing_email = User.query.filter_by(email='admin@aluminet.edu').first()
        if existing_email:
            existing_email.role = 'admin'
            existing_email.password = hashed_pw
            print(f"Updated user with email admin@aluminet.edu to admin role and reset password.")
        else:
            # Check if username is taken
            existing_user = User.query.filter_by(username='admin').first()
            if existing_user:
                existing_user.role = 'admin'
                existing_user.password = hashed_pw
                existing_user.email = 'admin@aluminet.edu'
                print(f"Updated user with username 'admin' to admin role and reset password/email.")
            else:
                new_admin = User(username='admin', email='admin@aluminet.edu', password=hashed_pw, role='admin')
                db.session.add(new_admin)
                print("Created new admin: admin@aluminet.edu / admin123")
    else:
        # Reset first admin found
        admin = admins[0]
        admin.password = hashed_pw
        admin.email = 'admin@aluminet.edu'
        print(f"Reset admin password for {admin.username}: admin@aluminet.edu / admin123")
    
    db.session.commit()
