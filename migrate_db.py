import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if the column exists first (optional but safer)
        # For MySQL/MariaDB:
        db.session.execute(text("ALTER TABLE message ADD COLUMN is_read BOOLEAN DEFAULT FALSE"))
        db.session.commit()
        print("Successfully added 'is_read' column to 'message' table.")
    except Exception as e:
        db.session.rollback()
        print(f"Error or column already exists: {e}")
