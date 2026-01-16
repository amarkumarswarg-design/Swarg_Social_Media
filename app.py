from flask import Flask, request, redirect
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

users = {}
posts = []

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Swarg</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#f0f2f5;margin:0}
.header{background:#1877f2;color:white;padding:15px;
font-size:26px;text-align:center;font-weight:bold}
.tabs{text-align:center;margin:10px}
.tabs a{margin:10px;color:#1877f2;text-decoration:none;font-weight:bold}
.card{background:white;margin:15px;padding:15px;border-radius:12px}
img{width:60px;height:60px;border-radius:50%}
textarea{width:100%;height:60px}
button{padding:8px 16px;background:#1877f2;color:white;border:none;border-radius:6px}
input{padding:6px;width:95%}
</style>
</head>
<body>
<div class="header">SWARG</div>
<div class="tabs">__TABS__</div>
__BODY__
</body>
</html>
"""

def render_page(tabs, body):
    return BASE.replace("__TABS__", tabs).replace("__BODY__", body)

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in users and users[u]["password"] == p:
            return redirect(f"/home/{u}")

    body = """
    <div class="card">
    <h3>Login</h3>
    <form method="post">
    <input name="username" placeholder="Username"><br><br>
    <input name="password" type="password" placeholder="Password"><br><br>
    <button>Login</button>
    </form>
    <br>
    <a href="/register">Create account</a>
    </div>
    """
    return render_page("", body)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        if u not in users:
            users[u] = {
                "password": request.form["password"],
                "dp": "/static/default.png"
            }
            return redirect("/")

    body = """
    <div class="card">
    <h3>Register</h3>
    <form method="post">
    <input name="username" placeholder="Username"><br><br>
    <input name="password" placeholder="Password"><br><br>
    <button>Register</button>
    </form>
    </div>
    """
    return render_page("", body)

@app.route("/home/<u>", methods=["GET","POST"])
def home(u):
    if request.method == "POST":
        posts.append({"user":u, "text":request.form["text"]})

    feed = ""
    for p in posts[::-1]:
        feed += f"""
        <div class="card">
        <img src="{users[p['user']]['dp']}">
        <b>@{p['user']}</b>
        <p>{p['text']}</p>
        </div>
        """

    body = f"""
    <div class="card">
    <form method="post">
    <textarea name="text" placeholder="What's on your mind?"></textarea><br><br>
    <button>Post</button>
    </form>
    </div>
    {feed}
    """

    tabs = f'<a href="/profile/{u}">Profile</a> | <a href="/">Logout</a>'
    return render_page(tabs, body)

@app.route("/profile/<u>", methods=["GET","POST"])
def profile(u):
    if request.method == "POST":
        f = request.files.get("dp")
        if f and f.filename:
            name = secure_filename(f.filename)
            path = os.path.join(UPLOAD_FOLDER, name)
            f.save(path)
            users[u]["dp"] = "/" + path

    body = f"""
    <div class="card">
    <img src="{users[u]['dp']}"><br><br>
    <form method="post" enctype="multipart/form-data">
    <input type="file" name="dp" accept="image/*"><br><br>
    <button>Upload DP</button>
    </form>
    </div>
    """

    tabs = f'<a href="/home/{u}">Feed</a>'
    return render_page(tabs, body)

app.run(host="0.0.0.0", port=5000)
