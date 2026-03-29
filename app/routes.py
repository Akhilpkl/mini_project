import os
import secrets
from flask import render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from datetime import datetime, timedelta
from app.models import User, Job, AlumniProfile, StudentProfile, Certificate, FacultyProfile, Message, PointTransaction, EventPhoto
from app.forms import RegistrationForm, LoginForm, JobPostForm, AlumniProfileForm, StudentProfileForm, FacultyProfileForm, EventPhotoForm

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    form_picture.save(picture_path)
    return picture_fn

def save_event_photo(form_photo):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_photo.filename)
    photo_fn = random_hex + f_ext
    photo_path = os.path.join(current_app.root_path, 'static/event_photos', photo_fn)
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
    form_photo.save(photo_path)
    return photo_fn

def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        # Daily Activity points
        if current_user.role == 'alumni':
            award_points(current_user, 'daily_login', 5)
        db.session.commit()

def award_points(user, action, amount, unique=False):
    """
    Awards points to Alumni users. 
    If unique=True, only awards if the action hasn't been logged before for this user.
    """
    if user.role != 'alumni':
        return False
    
    if unique:
        existing = PointTransaction.query.filter_by(user_id=user.id, action=action).first()
        if existing:
            return False

    # For daily_login, we check if already awarded today
    if action == 'daily_login':
        today = datetime.utcnow().date()
        # Filter transactions for this user, this action, and today
        # Note: we use timestamp comparison since db.func.date might be DB-specific
        start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_today = PointTransaction.query.filter(
            PointTransaction.user_id == user.id,
            PointTransaction.action == action,
            PointTransaction.timestamp >= start_of_today
        ).first()
        if existing_today:
            return False

    # Award points
    user.points += amount
    transaction = PointTransaction(user_id=user.id, action=action, amount=amount)
    db.session.add(transaction)
    db.session.commit()
    return True

def get_common_stats():
    """Returns a dictionary of platform-wide statistics for landing/auth pages."""
    total_alumni = AlumniProfile.query.filter_by(is_approved='Approved').count()
    
    # Jobs per month (current month)
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    jobs_per_month = Job.query.filter(Job.is_approved == True, Job.date_posted >= first_day_of_month).count()
    
    # Mentors (Approved Alumni + Approved Faculty)
    mentors = AlumniProfile.query.filter_by(is_approved='Approved').count() + \
              FacultyProfile.query.filter_by(is_approved=True).count()
              
    # Chapters (Unique departments)
    student_depts = db.session.query(StudentProfile.department).distinct().all()
    faculty_depts = db.session.query(FacultyProfile.department).distinct().all()
    all_depts = set([d[0] for d in student_depts if d[0]] + [d[0] for d in faculty_depts if d[0]])
    chapters = len(all_depts) if all_depts else 1
    
    # Active alumni in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_alumni = User.query.join(AlumniProfile).filter(
        AlumniProfile.is_approved == 'Approved',
        User.last_seen >= thirty_days_ago
    ).count()
    
    # Daily jobs
    daily_jobs = Job.query.filter(Job.is_approved == True, 
                                  Job.date_posted >= datetime.utcnow() - timedelta(hours=24)).count()

    return {
        'total_alumni': total_alumni,
        'jobs_per_month': jobs_per_month,
        'mentors': mentors,
        'chapters': chapters,
        'active_alumni': active_alumni,
        'daily_jobs': daily_jobs
    }

# Public Routes
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    stats = get_common_stats()
    return render_template('index.html', **stats)

# Auth Routes
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    
    stats = get_common_stats()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.flush() 

        if user.role == 'alumni':
            profile = AlumniProfile(user_id=user.id, graduation_year=2020, degree='B.Tech')
            db.session.add(profile)
        elif user.role == 'student':
            profile = StudentProfile(user_id=user.id, enrollment_year=2024, department='CSE')
            db.session.add(profile)
        elif user.role == 'faculty':
            profile = FacultyProfile(user_id=user.id)
            db.session.add(profile)
        
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, **stats)

def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()

    stats = get_common_stats()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form, **stats)

def logout():
    logout_user()
    return redirect(url_for('login'))

def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.role != 'admin':
                flash('Access denied: Admins only.', 'danger')
                return redirect(url_for('admin_login'))
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('admin_login.html', title='Admin Login', form=form)

@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    
    # Stats for the overview
    users_count = User.query.count()
    jobs_count = Job.query.count()
    pending_faculties = FacultyProfile.query.filter_by(is_approved=False).count()
    pending_alumni = AlumniProfile.query.filter_by(is_approved='Pending').count()
    total_points = db.session.query(db.func.sum(User.points)).scalar() or 0
    messages_count = Message.query.count()
    
    # Recent activity (e.g. last 5 users)
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html', 
                           users_count=users_count, 
                           jobs_count=jobs_count, 
                           pending_faculties=pending_faculties,
                           pending_alumni=pending_alumni,
                           total_points=total_points,
                           messages_count=messages_count,
                           recent_users=recent_users)

@login_required
def admin_faculty_approvals():
    if current_user.role != 'admin':
        abort(403)
    pending_faculties = FacultyProfile.query.filter_by(is_approved=False).all()
    pending_alumni = AlumniProfile.query.filter_by(is_approved='Pending').all()
    return render_template('admin_faculty_approvals.html', 
                           pending_faculties=pending_faculties, 
                           pending_alumni=pending_alumni)

@login_required
def admin_points():
    if current_user.role != 'admin':
        abort(403)
    # Simple view to trigger resets or see point leaderboard for admin
    top_pointed_users = User.query.filter_by(role='alumni').order_by(User.points.desc()).limit(10).all()
    recent_transactions = PointTransaction.query.order_by(PointTransaction.timestamp.desc()).limit(50).all()
    return render_template('admin_points.html', users=top_pointed_users, transactions=recent_transactions)

@login_required
def admin_stats():
    if current_user.role != 'admin':
        abort(403)
    
    # More detailed statistics
    role_counts = db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all()
    role_data = {role: count for role, count in role_counts}
    total_users = sum(role_data.values())
    
    job_status = db.session.query(Job.is_approved, db.func.count(Job.id)).group_by(Job.is_approved).all()
    total_jobs = sum(count for status, count in job_status)
    
    return render_template('admin_stats.html', 
                           role_data=role_data, 
                           total_users=total_users,
                           job_status=job_status,
                           total_jobs=total_jobs)

@login_required
def admin_reset_all_points():
    if current_user.role != 'admin':
        abort(403)
    User.query.update({User.points: 0})
    db.session.commit()
    flash('All user points have been reset to 0.', 'success')
    return redirect(url_for('admin_users'))

@login_required
def admin_users():
    if current_user.role != 'admin':
        abort(403)
    users = User.query.all()
    return render_template('admin_users.html', title='Manage Users', users=users)

@login_required
def admin_jobs():
    if current_user.role != 'admin':
        abort(403)
    jobs = Job.query.all()
    return render_template('admin_jobs.html', title='Manage Jobs', jobs=jobs)

@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete yourself!', 'danger')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_users'))

@login_required
def admin_update_points(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    new_points = request.form.get('points', type=int)
    if new_points is not None:
        user.points = new_points
        db.session.commit()
        flash(f'Points updated for {user.username}.', 'success')
    return redirect(url_for('admin_users'))

@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        abort(403)
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job posting deleted.', 'success')
    return redirect(url_for('admin_jobs'))

# Main App Routes
@login_required
def dashboard():
    # Common data for all roles
    approved_photos = EventPhoto.query.filter_by(status='approved').order_by(EventPhoto.uploaded_at.desc()).limit(6).all()
    
    if current_user.role == 'admin':
        users_count = User.query.count()
        jobs_count = Job.query.count()
        pending_alumni = AlumniProfile.query.filter_by(is_approved='Pending').count()
        return render_template('dashboard.html', 
                               users_count=users_count, 
                               jobs_count=jobs_count, 
                               pending_alumni=pending_alumni, 
                               event_photos=approved_photos)
    
    elif current_user.role == 'faculty':
        if not current_user.faculty_profile or not current_user.faculty_profile.is_approved:
            reason = 'pending admin approval' if current_user.faculty_profile else 'missing profile (please contact admin)'
            flash(f'Your faculty account is {reason}.', 'warning')
            return render_template('dashboard.html', pending_jobs=[], pending_alumni=[], event_photos=approved_photos)
        
        pending_jobs = Job.query.filter_by(is_approved=False).all()
        pending_alumni = AlumniProfile.query.filter_by(is_approved='Pending').all()
        return render_template('dashboard.html', 
                               pending_jobs=pending_jobs, 
                               pending_alumni=pending_alumni, 
                               event_photos=approved_photos)
    
    elif current_user.role == 'alumni':
        if not current_user.alumni_profile:
            flash('Your alumni profile is missing. Please contact an admin or complete your registration.', 'danger')
            return render_template('dashboard.html', jobs=[], profile=None, event_photos=approved_photos)
        
        my_jobs = Job.query.filter_by(user_id=current_user.alumni_profile.id).all()
        return render_template('dashboard.html', 
                               jobs=my_jobs, 
                               profile=current_user.alumni_profile, 
                               event_photos=approved_photos)
    
    elif current_user.role == 'student':
        if not current_user.student_profile:
            flash('Your student profile is missing. Please contact an admin.', 'danger')
            return render_template('dashboard.html', jobs=[], event_photos=approved_photos)
            
        current_year = datetime.utcnow().year
        student_yr_num = current_year - current_user.student_profile.enrollment_year + 1
        year_map = {1: "1st Year", 2: "2nd Year", 3: "3rd Year", 4: "4th Year"}
        student_yr_str = year_map.get(student_yr_num, "4th Year" if student_yr_num > 4 else "1st Year")
        
        recent_jobs = Job.query.filter(Job.is_approved==True).filter(
            db.or_(Job.target_year == 'All', Job.target_year == student_yr_str)
        ).order_by(Job.date_posted.desc()).limit(5).all()
        
        return render_template('dashboard.html', jobs=recent_jobs, event_photos=approved_photos)
    
    return render_template('dashboard.html', event_photos=approved_photos)



@login_required
def jobs():
    if current_user.role == 'student':
        current_year = datetime.utcnow().year
        student_yr_num = current_year - current_user.student_profile.enrollment_year + 1
        if student_yr_num == 1: student_yr_str = "1st Year"
        elif student_yr_num == 2: student_yr_str = "2nd Year"
        elif student_yr_num == 3: student_yr_str = "3rd Year"
        elif student_yr_num >= 4: student_yr_str = "4th Year"
        else: student_yr_str = "1st Year"
        
        jobs = Job.query.filter(Job.is_approved==True).filter(
            db.or_(Job.target_year == 'All', Job.target_year == student_yr_str)
        ).all()
    else:
        jobs = Job.query.filter_by(is_approved=True).all()
    return render_template('jobs.html', jobs=jobs)

@login_required
def new_job():
    if current_user.role != 'alumni':
        abort(403)
    form = JobPostForm()
    if form.validate_on_submit():
        job = Job(title=form.title.data, company=form.company.data, 
                  location=form.location.data, description=form.description.data,
                  target_year=form.target_year.data,
                  apply_link=form.apply_link.data, author=current_user.alumni_profile)
        db.session.add(job)
        db.session.commit()
        flash('Job posted! Waiting for faculty approval.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_job.html', title='New Job', form=form)

@login_required
def approve_job(job_id):
    if current_user.role not in ['faculty', 'admin']:
        abort(403)
    if current_user.role == 'faculty' and (not current_user.faculty_profile or not current_user.faculty_profile.is_approved):
        abort(403)
    job = Job.query.get_or_404(job_id)
    job.is_approved = True
    # Award points to Alumnus author when job is approved
    award_points(job.author.user, f'job_post_{job.id}', 20, unique=True)
    db.session.commit()
    flash('Job verified and published! Author awarded 20 points.', 'success')
    if current_user.role == 'admin':
        return redirect(url_for('admin_jobs'))
    return redirect(url_for('dashboard'))

@login_required
def approve_alumni(profile_id):
    if current_user.role not in ['faculty', 'admin']:
        abort(403)
    if current_user.role == 'faculty' and (not current_user.faculty_profile or not current_user.faculty_profile.is_approved):
        abort(403)
    profile = AlumniProfile.query.get_or_404(profile_id)
    profile.is_approved = 'Approved'
    profile.user.points += 50
    db.session.commit()
    flash('Alumni profile verified! User awarded 50 points.', 'success')
    if current_user.role == 'admin':
        return redirect(url_for('admin_faculty_approvals'))
    return redirect(url_for('dashboard'))

@login_required
def approve_faculty(profile_id):
    if current_user.role != 'admin':
        abort(403)
    profile = FacultyProfile.query.get_or_404(profile_id)
    profile.is_approved = True
    db.session.commit()
    flash('Faculty profile approved successfully!', 'success')
    return redirect(url_for('admin_faculty_approvals'))

@login_required
def reject_faculty(profile_id):
    if current_user.role != 'admin':
        abort(403)
    profile = FacultyProfile.query.get_or_404(profile_id)
    user = profile.user
    db.session.delete(profile)
    db.session.delete(user)
    db.session.commit()
    flash('Faculty registration rejected and user account removed.', 'warning')
    return redirect(url_for('admin_faculty_approvals'))

@login_required
def profile():
    form = None
    if current_user.role == 'alumni':
        form = AlumniProfileForm()
        if form.validate_on_submit():
            if form.picture.data:
                current_user.image_file = save_picture(form.picture.data)
            current_user.alumni_profile.degree = form.degree.data
            current_user.alumni_profile.graduation_year = form.graduation_year.data
            current_user.alumni_profile.current_company = form.current_company.data
            current_user.alumni_profile.current_position = form.current_position.data
            current_user.alumni_profile.linkedin_url = form.linkedin_url.data
            
            # Award points for first-time profile completion
            award_points(current_user, 'profile_update', 10, unique=True)
            
            db.session.commit()
            flash('Profile Updated!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.degree.data = current_user.alumni_profile.degree
            form.graduation_year.data = current_user.alumni_profile.graduation_year
            form.current_company.data = current_user.alumni_profile.current_company
            form.current_position.data = current_user.alumni_profile.current_position
            form.linkedin_url.data = current_user.alumni_profile.linkedin_url

    elif current_user.role == 'student':
        form = StudentProfileForm()
        if form.validate_on_submit():
            if form.picture.data:
                current_user.image_file = save_picture(form.picture.data)
            current_user.student_profile.department = form.department.data
            current_user.student_profile.enrollment_year = form.enrollment_year.data
            current_user.student_profile.cgpa = float(form.cgpa.data) if form.cgpa.data else 0.0
            db.session.commit()
            flash('Profile Updated!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.department.data = current_user.student_profile.department
            form.enrollment_year.data = current_user.student_profile.enrollment_year
            form.cgpa.data = current_user.student_profile.cgpa

    elif current_user.role == 'faculty':
        if not current_user.faculty_profile:
            flash('Your faculty profile is missing. Please contact admin.', 'danger')
            return redirect(url_for('dashboard'))
        form = FacultyProfileForm()
        if form.validate_on_submit():
            if form.picture.data:
                current_user.image_file = save_picture(form.picture.data)
            current_user.faculty_profile.department = form.department.data
            db.session.commit()
            flash('Profile Updated!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.department.data = current_user.faculty_profile.department

    # Fetch jobs for alumni to display on profile
    my_jobs = []
    if current_user.role == 'alumni' and current_user.alumni_profile:
        my_jobs = Job.query.filter_by(user_id=current_user.alumni_profile.id).all()

    return render_template('profile.html', title='Profile', form=form, jobs=my_jobs)

@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_profile.html', title=f"{user.username}'s Profile", user=user)

def leaderboard():
    # Only show Alumni in the leaderboard
    users = User.query.filter_by(role='alumni').order_by(User.points.desc()).limit(10).all()
    return render_template('leaderboard.html', users=users)

@login_required
def search():
    query = request.args.get('q', '').strip()
    results = []
    
    if current_user.role == 'student':
        alumni = AlumniProfile.query.filter(AlumniProfile.is_approved == 'Approved').all()
        results = [{'type': 'alumni', 'profile': a, 'user': a.user} for a in alumni]
    elif current_user.role == 'alumni':
        students = StudentProfile.query.all()
        alumni = AlumniProfile.query.filter(AlumniProfile.is_approved == 'Approved', AlumniProfile.user_id != current_user.id).all()
        results = [{'type': 'student', 'profile': s, 'user': s.user} for s in students] + \
                  [{'type': 'alumni', 'profile': a, 'user': a.user} for a in alumni]
    elif current_user.role in ['faculty', 'admin']:
        alumni = AlumniProfile.query.filter(AlumniProfile.is_approved == 'Approved').all()
        students = StudentProfile.query.all()
        results = [{'type': 'alumni', 'profile': a, 'user': a.user} for a in alumni] + \
                  [{'type': 'student', 'profile': s, 'user': s.user} for s in students]

    if query:
        query_lower = query.lower()
        filtered_results = []
        for r in results:
            u = r['user']
            p = r['profile']
            match = False
            if query_lower in u.username.lower(): match = True
            elif r['type'] == 'alumni':
                if p.degree and query_lower in p.degree.lower(): match = True
                if p.current_company and query_lower in p.current_company.lower(): match = True
                if p.current_position and query_lower in p.current_position.lower(): match = True
            elif r['type'] == 'student':
                if p.department and query_lower in p.department.lower(): match = True
            if match:
                filtered_results.append(r)
        results = filtered_results

    return render_template('search.html', title='Search', results=results, query=query)

@login_required
def messages():
    # Subquery to get the latest message timestamp for each conversation
    # We define a "conversation" by the user we are talking to.
    
    # Get all unique users current_user has exchanged messages with
    sent_to = db.session.query(Message.recipient_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(recipient_id=current_user.id)
    contact_ids = sent_to.union(received_from).all()
    contact_ids = [cid[0] for cid in contact_ids]

    contacts_data = []
    for cid in contact_ids:
        contact = User.query.get(cid)
        # Get the very latest message in this conversation
        last_msg = Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == current_user.id, Message.recipient_id == cid),
                db.and_(Message.sender_id == cid, Message.recipient_id == current_user.id)
            )
        ).order_by(Message.timestamp.desc()).first()
        
        # Get unread count for this specific contact
        unread_cnt = Message.query.filter_by(sender_id=cid, recipient_id=current_user.id, is_read=False).count()
        
        contacts_data.append({
            'contact': contact,
            'last_msg': last_msg,
            'unread_count': unread_cnt
        })
    
    # Sort contacts by last message timestamp (descending)
    contacts_data.sort(key=lambda x: x['last_msg'].timestamp if x['last_msg'] else datetime.min, reverse=True)
    
    return render_template('messages.html', title='Messages', contacts_data=contacts_data)

@login_required
def chat(user_id):
    if user_id == current_user.id:
        return redirect(url_for('messages'))
    other_user = User.query.get_or_404(user_id)
    return render_template('chat.html', title=f'Chat with {other_user.username}', other_user=other_user)

@login_required
def api_get_chat(user_id):
    # Mark messages as read when they are fetched
    unread_msgs = Message.query.filter_by(sender_id=user_id, recipient_id=current_user.id, is_read=False).all()
    for m in unread_msgs:
        m.is_read = True
    db.session.commit()

    msgs = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'content': m.content,
        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': m.is_read
    } for m in msgs])

@login_required
def api_send_message(user_id):
    content = request.form.get('content', '').strip()
    if content:
        msg = Message(sender_id=current_user.id, recipient_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Empty content'}), 400

@login_required
def upload_event_photo():
    if current_user.role != 'alumni':
        abort(403)
    form = EventPhotoForm()
    if form.validate_on_submit():
        if form.photo.data:
            photo_file = save_event_photo(form.photo.data)
            event_photo = EventPhoto(
                user_id=current_user.id,
                image_path=photo_file,
                event_name=form.event_name.data,
                caption=form.caption.data
            )
            db.session.add(event_photo)
            db.session.commit()
            flash('Photo uploaded successfully! It will be visible once verified by faculty.', 'success')
            return redirect(url_for('dashboard'))
    return render_template('upload_photo.html', title='Upload Event Photo', form=form)

@login_required
def moderate_photos():
    if current_user.role not in ['faculty', 'admin']:
        abort(403)
    if current_user.role == 'faculty' and (not current_user.faculty_profile or not current_user.faculty_profile.is_approved):
        abort(403)
    pending_photos = EventPhoto.query.filter_by(status='pending').all()
    return render_template('moderate_photos.html', title='Moderate Photos', photos=pending_photos)

@login_required
def approve_photo(photo_id):
    if current_user.role not in ['faculty', 'admin']:
        abort(403)
    photo = EventPhoto.query.get_or_404(photo_id)
    photo.status = 'approved'
    photo.verified_by = current_user.id
    db.session.commit()
    flash('Photo approved and added to gallery!', 'success')
    return redirect(url_for('moderate_photos'))

@login_required
def reject_photo(photo_id):
    if current_user.role not in ['faculty', 'admin']:
        abort(403)
    photo = EventPhoto.query.get_or_404(photo_id)
    photo.status = 'rejected'
    photo.verified_by = current_user.id
    db.session.commit()
    flash('Photo has been rejected.', 'warning')
    return redirect(url_for('moderate_photos'))

@login_required
def delete_event_photo(photo_id):
    photo = EventPhoto.query.get_or_404(photo_id)
    
    # Permission check: Uploader or Admin
    if photo.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    
    # Remove from storage
    try:
        photo_path = os.path.join(current_app.root_path, 'static/event_photos', photo.image_path)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    except Exception as e:
        # Log error but proceed with DB deletion if file is already missing
        print(f"Error deleting file: {e}")

    db.session.delete(photo)
    db.session.commit()
    flash('Photo has been deleted.', 'success')
    return redirect(url_for('dashboard'))
