from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('student', 'Student'), ('alumni', 'Alumni'), ('faculty', 'Faculty')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class JobPostForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    target_year = SelectField('Target Year', choices=[('All', 'All Students'), ('1st Year', '1st Year'), ('2nd Year', '2nd Year'), ('3rd Year', '3rd Year'), ('4th Year', '4th Year')], validators=[DataRequired()])
    apply_link = StringField('Application Link', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Post Job')

class AlumniProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    graduation_year = IntegerField('Graduation Year', validators=[DataRequired(), NumberRange(min=1950, max=2030)])
    degree = StringField('Degree', validators=[DataRequired()])
    current_company = StringField('Current Company')
    current_position = StringField('Current Position')
    linkedin_url = StringField('LinkedIn URL')
    submit = SubmitField('Update Profile')

class StudentProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    enrollment_year = IntegerField('Enrollment Year', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    cgpa = StringField('CGPA')
    submit = SubmitField('Update Profile')

class FacultyProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    department = StringField('Department', validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class EventPhotoForm(FlaskForm):
    photo = FileField('Upload Event Photo', validators=[DataRequired(), FileAllowed(['jpg', 'png'])])
    event_name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    caption = TextAreaField('Caption', validators=[Length(max=200)])
    submit = SubmitField('Upload Photo')

