from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from wtforms import validators
from flask_ckeditor import CKEditorField
from werkzeug.security import generate_password_hash, check_password_hash
import re


def password_validator(form, field):
    password = field.data
    lowercase = re.search(r'[a-z]', password)
    uppercase = re.search(r'[A-Z]', password)
    digit = re.search(r'\d', password)

    if not (lowercase and uppercase and digit):
        raise validators.ValidationError('Your password must contain at one lowercase letter (a-z), one uppercase letter (A-Z) and one digit (0-9). Minimal length is 6 characters')
    

def check_if_email_exist(field, email):
        if email == field.data:
            raise validators.ValidationError('This email is already in use')
    

class RegisterForm(FlaskForm):
    def __init__(self, db, User, *args, **kwargs):
        self.db = db
        self.User = User
        super().__init__(*args, **kwargs)

    def validate_email(self, field):
        if self.db.session.execute(self.db.select(self.User).where(self.User.email == field.data)).scalar():
            raise validators.ValidationError('This email is already in use')
        
    username = StringField("Enter you blog username", validators=[DataRequired()])
    email = StringField("Enter you email", validators=[DataRequired()])
    password = PasswordField("Enter you password" , validators=[DataRequired(), password_validator], render_kw={"placeholder": "At least one lowercase letter (a-z), one uppercase letter (A-Z) and one digit (0-9). Minimal length is 6 characters"})
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    def __init__(self, db, User, *args, **kwargs):
        self.db = db
        self.User = User
        super().__init__(*args, **kwargs)

    def validate_email(self, field):
        if self.db.session.execute(self.db.select(self.User).where(self.User.email == field.data)).scalar() == None:
            raise validators.ValidationError('This email does not exist.')

    def validate_password(self, field):
        user = self.db.session.execute(self.db.select(self.User).where(self.User.email == self.email.data)).scalar()
        if user and not check_password_hash(user.password, field.data):
            raise validators.ValidationError('Incorrect password')

    email = StringField("Enter you email", validators=[DataRequired()])
    password = PasswordField("Enter you password", validators=[DataRequired()])
    submit = SubmitField("Log in")

# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    body = StringField("Comment", validators=[DataRequired(), validators.Length(max=300, message="Limit exceeded! (Only 300 characters per comment)")])
    submit = SubmitField("Submit Comment")