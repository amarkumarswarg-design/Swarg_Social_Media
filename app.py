from flask import Flask, request, redirect, render_template_string
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static/uploads"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
.tabs a{margin:10px;color:#1877f2;text-decoration:none;font-weight:bold}
.card{background:white;margin:15px;padding:15px;border-radius:12px}
img{width:60px;height:60px;border-radius:50%}
</style>
</head>
<body>
<div class="header">SWARG</div>
<div class="tabs">{tabs}</div>
{body}
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        if u in users and users[u]["password"]==p:
            return redirect(f"/home/{u}")
    return render_template_string(BASE, tabs="", body="""
    <div class="card">
    <h3>Login</h3>
    <form method="post">
    Username <input name="username"><br><br>
    Password <input name="password" type="password"><br><br>
    <button>Login</button>
    </form>
    <a href="/register">Register</a>
    </div>
    """)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"]
        users[u]={"password":request.form["password"],"dp":"/static/default.png"}
        return redirect("/")
    return render_template_string(BASE, tabs="", body="""
    <div class="card">
    <h3>Register</h3>
    <form method="post">
    Username <input name="username"><br><br>
    Password <input name="password"><br><br>
    <button>Register</button>
    </form>
    </div>
    """)

@app.route("/home/<u>", methods=["GET","POST"])
def home(u):
    if request.method=="POST":
        posts.append({"u":u,"text":request.form["text"]})
    feed=""
    for p in posts[::-1]:
        feed+=f"<div class='card'><img src='{users[p['u']]['dp']}'><b>@{p['u']}</b><p>{p['text']}</p></div>"
    return render_template_string(
        BASE,
        tabs=f"<a href='/profile/{u}'>Profile</a> <a href='/'>Logout</a>",
        body=f"""
        <div class="card">
        <form method="post">
        <textarea name="text"></textarea><br>
        <button>Post</button>
        </form>
        </div>
        {feed}
        """
    )

@app.route("/profile/<u>", methods=["GET","POST"])
def profile(u):
    if request.method=="POST":
        f=request.files["dp"]
        if f:
            name=secure_filename(f.filename)
            path=os.path.join(app.config["UPLOAD_FOLDER"],name)
            f.save(path)
            users[u]["dp"]="/"+path
    return render_template_string(
        BASE,
        tabs=f"<a href='/home/{u}'>Feed</a>",
        body=f"""
        <div class="card">
        <img src="{users[u]['dp']}"><br><br>
        <form method="post" enctype="multipart/form-data">
        Change DP:<br>
        <input type="file" name="dp" accept="image/*"><br><br>
        <button>Upload</button>
        </form>
        </div>
        """
    )

app.run(host="0.0.0.0", port=5000)
