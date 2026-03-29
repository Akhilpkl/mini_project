import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import PointTransaction

app = create_app()
with app.app_context():
    db.create_all()
    print("Database updated with PointTransaction table.")
