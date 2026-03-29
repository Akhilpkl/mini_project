import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
bcrypt = Bcrypt()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Register Routes
    from app import routes
    app.before_request(routes.before_request)
    app.add_url_rule('/', 'index', routes.index)
    app.add_url_rule('/register', 'register', routes.register, methods=['GET', 'POST'])
    app.add_url_rule('/login', 'login', routes.login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', routes.logout)
    app.add_url_rule('/admin', 'admin_login', routes.admin_login, methods=['GET', 'POST'])
    app.add_url_rule('/admin/dashboard', 'admin_dashboard', routes.admin_dashboard)
    app.add_url_rule('/admin/users', 'admin_users', routes.admin_users)
    app.add_url_rule('/admin/faculty-approvals', 'admin_faculty_approvals', routes.admin_faculty_approvals)
    app.add_url_rule('/admin/jobs', 'admin_jobs', routes.admin_jobs)
    app.add_url_rule('/admin/points', 'admin_points', routes.admin_points)
    app.add_url_rule('/admin/stats', 'admin_stats', routes.admin_stats)
    app.add_url_rule('/admin/user/<int:user_id>/delete', 'admin_delete_user', routes.admin_delete_user)
    app.add_url_rule('/admin/user/<int:user_id>/points', 'admin_update_points', routes.admin_update_points, methods=['POST'])
    app.add_url_rule('/admin/users/reset_points', 'admin_reset_all_points', routes.admin_reset_all_points, methods=['POST'])
    app.add_url_rule('/admin/job/<int:job_id>/delete', 'admin_delete_job', routes.admin_delete_job)
    app.add_url_rule('/admin/approve_faculty/<int:profile_id>', 'approve_faculty', routes.approve_faculty)
    app.add_url_rule('/admin/reject_faculty/<int:profile_id>', 'reject_faculty', routes.reject_faculty)
    app.add_url_rule('/dashboard', 'dashboard', routes.dashboard)
    app.add_url_rule('/jobs', 'jobs', routes.jobs)
    app.add_url_rule('/job/new', 'new_job', routes.new_job, methods=['GET', 'POST'])
    app.add_url_rule('/approve/job/<int:job_id>', 'approve_job', routes.approve_job)
    app.add_url_rule('/approve/alumni/<int:profile_id>', 'approve_alumni', routes.approve_alumni)
    app.add_url_rule('/profile', 'profile', routes.profile, methods=['GET', 'POST'])
    app.add_url_rule('/user/<int:user_id>', 'view_profile', routes.view_profile)
    app.add_url_rule('/leaderboard', 'leaderboard', routes.leaderboard)
    app.add_url_rule('/search', 'search', routes.search)
    app.add_url_rule('/messages', 'messages', routes.messages)
    app.add_url_rule('/chat/<int:user_id>', 'chat', routes.chat)
    app.add_url_rule('/api/chat/<int:user_id>', 'api_get_chat', routes.api_get_chat)
    app.add_url_rule('/api/chat/send/<int:user_id>', 'api_send_message', routes.api_send_message, methods=['POST'])

    # Create tables within application context if they don't exist
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from app import models
        db.create_all()

    @app.context_processor
    def inject_unread_count():
        from flask_login import current_user
        from app.models import Message
        if current_user.is_authenticated:
            count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
            return dict(unread_count=count)
        return dict(unread_count=0)

    return app
