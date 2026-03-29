from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Association Tables
user_skills = db.Table('user_skills',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False) # 'admin', 'faculty', 'alumni', 'student'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    alumni_profile = db.relationship('AlumniProfile', backref='user', uselist=False, lazy=True)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, lazy=True)
    faculty_profile = db.relationship('FacultyProfile', backref='user', uselist=False, lazy=True)
    certificates = db.relationship('Certificate', backref='owner', lazy=True)
    skills = db.relationship('Skill', secondary=user_skills, lazy='subquery', backref=db.backref('users', lazy=True))
    badges = db.relationship('Badge', secondary=user_badges, lazy='subquery', backref=db.backref('users', lazy=True))
    
    # Points for gamification
    points = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class AlumniProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    current_company = db.Column(db.String(100))
    current_position = db.Column(db.String(100))
    linkedin_url = db.Column(db.String(200))
    is_approved = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    
    jobs_posted = db.relationship('Job', backref='author', lazy=True)
    roadmaps = db.relationship('Roadmap', backref='author', lazy=True)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    enrollment_year = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float)

class FacultyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department = db.Column(db.String(100), default='General')
    is_approved = db.Column(db.Boolean, default=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    apply_link = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    target_year = db.Column(db.String(20), default='All')
    user_id = db.Column(db.Integer, db.ForeignKey('alumni_profile.id'), nullable=False)

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    issuing_org = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon_class = db.Column(db.String(50)) # FontAwesome class
    description = db.Column(db.String(200))

class Roadmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300))
    alumni_id = db.Column(db.Integer, db.ForeignKey('alumni_profile.id'), nullable=False)
    steps = db.relationship('RoadmapStep', backref='roadmap', lazy=True)

class RoadmapStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmap.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='messages_sent')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='messages_received')

class PointTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False) # e.g., 'profile_update', 'job_post', 'daily_login'
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref='point_history', lazy=True)

    def __repr__(self):
        return f"PointTransaction('{self.action}', {self.amount}, '{self.timestamp}')"

class EventPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200))
    event_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    uploader = db.relationship('User', foreign_keys=[user_id], backref='uploaded_photos')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_photos')

