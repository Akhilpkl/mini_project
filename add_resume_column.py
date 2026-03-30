from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE alumni_profile ADD COLUMN resume_file VARCHAR(200)"))
            conn.commit()
        print("SUCCESS: resume_file column added to alumni_profile table.")
    except Exception as e:
        if "Duplicate column name" in str(e) or "1060" in str(e):
            print("Column already exists — no action needed.")
        else:
            print(f"ERROR: {e}")
