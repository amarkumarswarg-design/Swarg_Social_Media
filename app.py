from flask import Flask, request, redirect, render_template_string
from werkzeug.utils import secure_filename
from markupsafe import Markup
import sqlite3, os, datetime

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------- DATABASE ----------
def db():
    con = sqlite3.connect("swarg.db", check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

cur = db().cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT,
    bio TEXT,
    school TEXT,
    city TEXT,
    dp TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    content TEXT,
    time TEXT
)""")
db().commit()

# ---------- BASE LAYOUT ----------
BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Swarg</title>
<style>
body{font-family:Arial;background:#f0f2f5;margin:0}
header{background:#1877f2;color:white;padding:12px;text-align:center;font-size:22px}
nav{display:flex;justify-content:space-around;background:#fff;padding:10px}
nav a{text-decoration:none;color:#1877f2;font-weight:bold}
.card{background:white;margin:10px;padding:15px;border-radius:8px}
input,textarea,button{width:100%;padding:8px;margin:5px 0}
button{background:#1877f2;color:white;border:none}
img.dp{width:80px;height:80px;border-radius:50%}
</style>
</head>
<body>
<header>SWARG</header>
{{nav}}
{{body}}
</body>
</html>
"""

def page(nav, body):
    return render_template_string(BASE, nav=Markup(nav), body=Markup(body))

def navbar(user):
    return f"""
    <nav>
    <a href="/feed/{user}">Feed</a>
    <a href="/search/{user}">Search</a>
    <a href="/profile/{user}">Profile</a>
    <a href="/">Logout</a>
    </nav>
    """

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        cur=db().cursor()
        cur.execute("SELECT password FROM users WHERE username=?", (u,))
        r=cur.fetchone()
        if r and r["password"]==p:
            return redirect(f"/feed/{u}")
        error="Incorrect login"
    return page("", f"""
    <div class="card">
    <h3>Login</h3>
    <form method="post">
    <input name="username" required placeholder="Username">
    <input name="password" type="password" required placeholder="Password">
    <button>Login</button>
    </form>
    <p style="color:red">{error}</p>
    <a href="/register">Create account</a>
    </div>
    """)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]
        try:
            cur=db().cursor()
            cur.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",
                        (u,p,"","","",""))
            db().commit()
            return redirect("/")
        except:
            pass
    return page("", """
    <div class="card">
    <h3>Register</h3>
    <form method="post">
    <input name="username" required>
    <input name="password" type="password" required>
    <button>Create</button>
    </form>
    </div>
    """)

# ---------- FEED ----------
@app.route("/feed/<user>", methods=["GET","POST"])
def feed(user):
    if request.method=="POST":
        txt=request.form["post"]
        t=datetime.datetime.now().strftime("%d %b %H:%M")
        cur=db().cursor()
        cur.execute("INSERT INTO posts(username,content,time) VALUES(?,?,?)",(user,txt,t))
        db().commit()
    cur=db().cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts=""
    for p in cur.fetchall():
        posts+=f"<div class='card'><b>{p['username']}</b><br>{p['content']}<br><small>{p['time']}</small></div>"
    return page(navbar(user), f"""
    <div class="card">
    <form method="post">
    <textarea name="post" placeholder="What's on your mind?" required></textarea>
    <button>Post</button>
    </form>
    </div>
    {posts}
    """)

# ---------- SEARCH ----------
@app.route("/search/<user>", methods=["GET","POST"])
def search(user):
    result=""
    if request.method=="POST":
        q=request.form["q"]
        cur=db().cursor()
        cur.execute("SELECT username FROM users WHERE username LIKE ?", ("%"+q+"%",))
        for r in cur.fetchall():
            result+=f"<div class='card'><a href='/profile/{r['username']}'>{r['username']}</a></div>"
    return page(navbar(user), f"""
    <div class="card">
    <form method="post">
    <input name="q" placeholder="Search user">
    <button>Search</button>
    </form>
    </div>
    {result}
    """)

# ---------- PROFILE ----------
@app.route("/profile/<user>", methods=["GET","POST"])
def profile(user):
    cur=db().cursor()
    if request.method=="POST":
        f=request.files["dp"]
        if f.filename:
            name=secure_filename(f.filename)
            path=os.path.join(app.config["UPLOAD_FOLDER"],name)
            f.save(path)
            cur.execute("UPDATE users SET dp=? WHERE username=?", (path,user))
            db().commit()
    cur.execute("SELECT * FROM users WHERE username=?", (user,))
    u=cur.fetchone()
    dp=u["dp"] if u["dp"] else "https://via.placeholder.com/80"
    return page(navbar(user), f"""
    <div class="card">
    <img src="/{dp}" class="dp"><br>
    <b>{user}</b><br>
    {u['bio']}<br>
    {u['school']}<br>
    {u['city']}
    <form method="post" enctype="multipart/form-data">
    <input type="file" name="dp">
    <button>Change DP</button>
    </form>
    <a href="/edit/{user}">Edit Profile</a>
    </div>
    """)

# ---------- EDIT PROFILE ----------
@app.route("/edit/<user>", methods=["GET","POST"])
def edit(user):
    cur=db().cursor()
    if request.method=="POST":
        cur.execute("UPDATE users SET bio=?,school=?,city=? WHERE username=?",
                    (request.form["bio"],request.form["school"],request.form["city"],user))
        db().commit()
        return redirect(f"/profile/{user}")
    return page(navbar(user), f"""
    <div class="card">
    <form method="post">
    <input name="bio" placeholder="About you">
    <input name="school" placeholder="School/Work">
    <input name="city" placeholder="City">
    <button>Save</button>
    </form>
    </div>
    """)

# ---------- RUN ----------
app.run(host="0.0.0.0", port=5000)
