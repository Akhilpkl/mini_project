from app import create_app, db
from app.models import User
from app import bcrypt

app = create_app()
with app.app_context():
    admin = User.query.filter_by(email='admin@aluminet.edu').first()
    if not admin:
        # Create a new admin if none exists
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(username='admin', email='admin@aluminet.edu', password=hashed_pw, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Created new admin: admin@aluminet.edu / admin123")
    else:
        # Reset password of existing admin to be sure
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin.password = hashed_pw
        admin.role = 'admin' # Ensure it has the role
        db.session.commit()
        print("Reset existing admin password: admin@aluminet.edu / admin123")
