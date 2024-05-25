from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash

from datetime import date
from typing import List
import os


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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
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
    comments: Mapped[List["Comment"]] = relationship(back_populates="parent_post")


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    password: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped["User"] = relationship(back_populates="comments")
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")
    parent_post_id: Mapped[int] = mapped_column(ForeignKey("blog_posts.id"))
    posted_time : Mapped[str] = mapped_column(Text, nullable=False) # TODO add time function which calculates the time from post being posted


@app.route('/')
def main_hub():
    return render_template("index.html", footer=footer_variables,
                           header_img_path = "../static/img/cube-like-bg.jpg")


@app.route('/python')
def get_python_page():
    return render_template("python_page.html", footer=footer_variables,
                           header_img_path = "../static/img/cube-like-bg.jpg")


@app.route('/web-development')
def get_web_development_page():
    return render_template("web_development.html", footer=footer_variables,
                           header_img_path = "../static/img/cube-like-bg.jpg", blog_data = get(url=WebDevPosts_URL).json())


@app.route('/python/blog')
def get_python_blog():
     return render_template("python_blogs.html", footer=footer_variables,
                           header_img_path = "../static/img/cube-like-bg.jpg", blog_data = get(url=Python100DaysPosts_URL).json())


@app.route('/about')
def about_page():
    return render_template("about.html", footer=footer_variables,
                            header_img_path = "../static/img/about-bg.jpg")


@app.route('/contact', methods=["POST", "GET"])
def contact_page():
    if request.method == "GET":
        return render_template("contact.html", footer=footer_variables,
                            header_img_path = "../static/img/mountains-bg.jpg", send_email=False)
    elif request.method == "POST":
        response = email_module.send_email(name=request.form["name"], email=request.form["email"],
                                      phone_number=request.form["phone"], message=request.form["message"])
        if response:
            return render_template("contact.html", footer=footer_variables,
                            header_img_path = "../static/img/mountains-bg.jpg", send_email=True)
        
        else:
            return render_template("error.html", footer=footer_variables,
                            header_img_path = "../static/img/mountains-bg.jpg")
            


@app.route("/blog-post/<string:blog_type>")
def get_blog_post(blog_type):
    id_type = blog_type.split(":")[0]
    if id_type == "py":
        url=Python100DaysPosts_URL
    elif id_type == "web-dev":
        url=WebDevPosts_URL

    for blog in get(url=url).json():
        if blog["id"] == blog_type:
            blog_data = Post(blog)
            break
    
    return render_template("post.html", footer=footer_variables,
                           blog=blog_data, header_img_path = "../static/img/coding-bg.jpg")


if __name__ == "__main__":
    # app.run(debug=False, host='0.0.0.0', port=3000)
    app.run(debug=True)