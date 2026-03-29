import os
import sys
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Set points to 0 for everyone who is NOT an alumnus
    non_alumni = User.query.filter(User.role != 'alumni').all()
    count = 0
    for u in non_alumni:
        if u.points != 0:
            u.points = 0
            count += 1
    db.session.commit()
    print(f"Cleaned up points for {count} non-alumni users.")
