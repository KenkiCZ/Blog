from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, select, desc
from functools import wraps
from werkzeug.security import generate_password_hash

from typing import List
from forms import *
from web_email import *
import datetime, os


# Loading app and all related modules
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    use_ssl=False,
                    base_url=None)

# Creating connection with database
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] =  os.environ.get("DB_URI" )
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogCategory(db.Model):
    __tablename__ = "blog_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author: Mapped["User"] = relationship(back_populates="categories")
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="category")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    
    author: Mapped["User"] = relationship(back_populates="posts")
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    category: Mapped["BlogCategory"] = relationship(back_populates="posts")
    category_id: Mapped[int] = mapped_column(ForeignKey("blog_categories.id"))

    comments: Mapped[List["Comment"]] = relationship(back_populates="parent_post")


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    password: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")
    categories: Mapped[List["BlogCategory"]] = relationship(back_populates="author")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped["User"] = relationship(back_populates="comments")
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")
    parent_post_id: Mapped[int] = mapped_column(ForeignKey("blog_posts.id"))
    posted_time : Mapped[str] = mapped_column(Text, nullable=False) # TODO add time function which calculates the time from post being posted


class VariableManager():
    def __init__(self, edit:bool=False, send_email:bool=False):
        self.current_user = current_user
        self.year = datetime.datetime.now().strftime("%Y")
        self.author = "Lukas Sofka"
        self.edit = edit
        self.send_email = send_email


with app.app_context():
    db.create_all()


# Authentication Functions
@login_manager.user_loader
def load_user(user_id):
    """
    Loads a user by their ID for session management.
    Args: user_id (int): The ID of the user to be loaded.
    Returns: User: The user object if found, otherwise raises a 404 error.
    """
    return db.get_or_404(User, user_id)



@login_manager.unauthorized_handler
def handle_unauthorized_access():
    """
    Redirects the user to the login page if they attempt to access an endpoint
    that requires authentication without being logged in.
    """
    return redirect(url_for("login"))


def admin_only(function)->bool:
    """
    Check whether current user has admin privileges. Returns boolean
    """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            return redirect(url_for('login', next=request.url))
        elif current_user.id == 1:
            return function(*args, **kwargs)
        else:
            return function(*args, **kwargs)
    return decorated_function


def only_commenter(function)->bool:
    """
    Check whether user is owner of the comment. Return boolean.
    """
    @wraps(function)
    def check(*args, **kwargs):
        user = db.session.execute(db.select(Comment).where(Comment.author_id == current_user.id)).scalar()
        if not current_user.is_authenticated or current_user.id != user.author_id:
            return abort(403)
        return function(*args, **kwargs)
    return check


def hash_password(password: str)->str:
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)


def check_image(img: str)->str:
    if img == "Default":
        return "coding-bg.jpg"
    else:
        return img


# User Authentication Pages
@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm(db=db, User=User)
    if register_form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == register_form.email.data)).scalar():
            flash("Email already in use")
            return redirect(url_for("register"))
        
        else:
            hashed_password = hash_password(password=register_form.password.data)
            new_user = User(username=register_form.username.data, password=hashed_password, email=register_form.email.data)
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for("main_hub"))
    return render_template("register.html",
                           variables=VariableManager(),
                           form=register_form)


@app.route('/login', methods=["POST", "GET"])
def login():
    login_form = LoginForm(db=db, User=User)
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == login_form.email.data)).scalar()
        login_user(user)
        return redirect(url_for("main_hub"))
    return render_template("login.html",
                           variables=VariableManager(),
                           form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("main_hub"))


# Content pages 
@app.route('/')
def main_hub():
    categories_result = db.session.execute(db.select(BlogCategory))
    categories = categories_result.scalars().all()
    return render_template("index.html",
                           variables=VariableManager(),
                           categories=categories)

@app.route("/new-category", methods=["GET", "POST"])
@admin_only
def new_category():
    category_form = CategoryForm()
    if category_form.validate_on_submit():
        new_category = BlogCategory(title=category_form.title.data,
                                    subtitle=category_form.subtitle.data,
                                    img_url = category_form.img_url.data,
                                    author=current_user)
        db.session.add(new_category)
        db.session.commit()

        return redirect(url_for("main_hub"))
    return render_template("new_category.html",
                           variables=VariableManager(edit=False),
                           form=category_form)


@app.route("/category/<int:id>")
def view_category(id):
    category_result = db.session.execute(select(BlogCategory).where(BlogCategory.id == id))
    category = category_result.scalar()
    return render_template("category.html",
                           variables=VariableManager(),
                           category=category)


@app.route("/edit-category/<int:c_id>", methods=["GET", "POST"])
@admin_only
def edit_category(c_id):
    id = c_id
    category_result = db.session.execute(db.select(BlogCategory).where(BlogCategory.id == id))
    category = category_result.scalar()
    edit_form = CategoryForm(title=category.title,
                             subtitle=category.subtitle,
                             img_url=category.img_url)
    if edit_form.validate_on_submit():
        category.title = edit_form.title.data
        category.subtitle = edit_form.subtitle.data
        category.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for("view_category", id=id))
    
    return render_template("new_category.html",
                           variables=VariableManager(edit=True),
                           form=edit_form,
                           id=id)


@app.route("/delete/<string:item>/<int:id>", methods=["GET", "POST"])
@admin_only
def delete_item(item, id):
    if item == "category":
        result = db.session.execute(db.select(BlogCategory).where(BlogCategory.id == id)).scalar()
    elif item == "post":
        result = db.session.execute(db.select(BlogPost).where(BlogPost.id == id)).scalar()
    else:
        flash("Invalid item type")
    
    db.session.delete(result)
    db.session.commit()
    return redirect(url_for("main_hub"))


@app.route("/category/<int:c_id>/post/<int:p_id>", methods=["GET", "POST"])
@login_required
def view_post(c_id, p_id):
    category_result = db.session.execute(db.select(BlogCategory).where(BlogCategory.id == c_id)).scalar()
    post = [post for post in category_result.posts if post.id == p_id]
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        new_comment = Comment(text=comment_form.body.data,
                              author_id=current_user.id,
                              parent_post_id=p_id,
                              posted_time=datetime.datetime.now().strftime("%d/%m/%Y"))
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("view_post", c_id=c_id, p_id=p_id))
    return render_template("post.html",
                           variables=VariableManager(),
                           post=post[0],
                           form=comment_form) 


@app.route("/category/<int:c_id>/new-post", methods=["GET", "POST"])
@admin_only
def new_post(c_id):
    post_form = CreatePostForm(img_url="Default", date=datetime.datetime.now().strftime("%d/%m/%Y"))
    if post_form.validate_on_submit():
        new_post = BlogPost(title=post_form.title.data,
                            subtitle=post_form.subtitle.data,
                            img_url=check_image(post_form.img_url.data),
                            body=post_form.body.data,
                            category_id=c_id,
                            author=current_user,
                            date=post_form.date.data)

        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("view_category", id=c_id))
    return render_template("new-post.html",
                           variables=VariableManager(edit=False),
                           form=post_form)


@app.route("/category/<int:c_id>/edit-post/<int:p_id>", methods=["POST", "GET"])
@admin_only
def edit_post(c_id, p_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == p_id)).scalar()
    edit_form = CreatePostForm(obj=post)
    if edit_form.validate_on_submit():
        post.title=edit_form.title.data
        post.subtitle=edit_form.subtitle.data
        post.img_url=check_image(edit_form.img_url.data)
        post.body=edit_form.body.data
        date=edit_form.date.data
        db.session.commit()
        return redirect(url_for("view_category", id=c_id))
    return render_template("new-post.html",
                           variables=VariableManager(edit=True),
                           form=edit_form)


@app.route("/category/<int:c_id>/post/<int:p_id>/delete-comment/<int:comment_id>")
@only_commenter
def delete_comment(c_id, p_id, comment_id):
    comment_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(comment_delete)
    db.session.commit()
    return redirect(url_for('view_post', c_id=c_id,p_id=p_id))


@app.route("/category/<int:c_id>/delete/<int:p_id>")
@admin_only
def delete_post(c_id, p_id):
    post_to_delete = db.get_or_404(BlogPost, p_id)
    [db.session.delete(comment) for comment in post_to_delete.comments]
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('view_category', id=c_id))


@app.route("/about")
def about():
    return render_template("about.html",
                            variables=VariableManager())


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        response = send_email(name=request.form["name"],
                              email=request.form["email"],
                              phone_number=request.form["phone"],
                              message=request.form["message"])
        if response:
            return render_template("contact.html",
                                   variables=VariableManager(send_email=True))
        
    return render_template("contact.html",
                            variables=VariableManager())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
