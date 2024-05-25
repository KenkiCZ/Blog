from flask import Flask, render_template, request
from datetime import datetime
from requests import get
import scripts.web_email as email_module

app = Flask(__name__)

footer_variables = [datetime.now().year, "Lukas Sofka"]
Python100DaysPosts_URL = "https://api.npoint.io/5d28e60a504e89829062"
WebDevPosts_URL = "https://api.npoint.io/9a50a8d50c519db0d8ed"


class Post:
    def __init__(self, post: dict) -> None:
        self.id = post["id"]
        self.title = post["title"]
        self.subtitle = post["subtitle"]
        self.body = post["body"]
        self.date = post["date"]
        self.author = post["author"]

        if post["img-id"] != "None":
            self.img_id = post["img-id"]
            self.img = f'../static/img/{self.img_id}'

        else:
            self.img = False


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